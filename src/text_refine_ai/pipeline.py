from __future__ import annotations

from text_refine_ai.exceptions import InputError
from text_refine_ai.llm import LLMClient, MockLLMClient
from text_refine_ai.processing import preprocess_text, split_into_chunks
from text_refine_ai.prompts import build_generation_prompt, build_refinement_prompt
from text_refine_ai.renderer import render_markdown
from text_refine_ai.schemas import (
    ActionItem,
    DialogueTurn,
    RefineRequest,
    RefineResult,
    Section,
    StructuredDocument,
)


class TextRefinePipeline:
    def __init__(
        self,
        llm_client: LLMClient | None = None,
        chunk_size: int = 4000,
        overlap: int = 300,
    ) -> None:
        self.llm_client = llm_client or MockLLMClient()
        self.chunk_size = chunk_size
        self.overlap = overlap

    def run(self, request: RefineRequest) -> RefineResult:
        clean_text = preprocess_text(request.raw_text)
        if not clean_text:
            raise InputError("输入不能为空")

        chunks = split_into_chunks(clean_text, max_chars=self.chunk_size, overlap=self.overlap)
        generated: list[StructuredDocument] = []
        for index, chunk in enumerate(chunks, start=1):
            prompt = build_generation_prompt(request.mode, chunk, index, len(chunks))
            generated.append(self.llm_client.generate(prompt, request.mode))

        document = _merge_documents(generated, request.mode)
        for _round in range(request.refine_rounds):
            prompt = build_refinement_prompt(request.mode, document)
            document = self.llm_client.refine(prompt, request.mode, document)

        metadata = {
            "chunks": len(chunks),
            "refine_rounds": request.refine_rounds,
            "provider": request.provider,
        }
        document.metadata.update(metadata)
        markdown = render_markdown(document)
        return RefineResult(markdown=markdown, data=document, metadata=metadata)


def _merge_documents(documents: list[StructuredDocument], mode: str) -> StructuredDocument:
    if not documents:
        raise InputError("输入不能为空")
    if len(documents) == 1:
        return documents[0].model_copy(deep=True)

    first = documents[0]
    return StructuredDocument(
        mode=first.mode,
        title=first.title,
        summary=" ".join(_dedupe_strings([document.summary for document in documents])),
        sections=_merge_sections(documents),
        dialogue_turns=_merge_dialogue_turns(documents),
        action_items=_merge_action_items(documents),
        metadata={},
    )


def _merge_sections(documents: list[StructuredDocument]) -> list[Section]:
    by_heading: dict[str, list[str]] = {}
    for document in documents:
        for section in document.sections:
            by_heading.setdefault(section.heading, [])
            by_heading[section.heading].extend(section.items)
    return [
        Section(heading=heading, items=_dedupe_strings(items))
        for heading, items in by_heading.items()
    ]


def _merge_dialogue_turns(documents: list[StructuredDocument]) -> list[DialogueTurn]:
    turns: list[DialogueTurn] = []
    seen: set[tuple[str, str]] = set()
    for document in documents:
        for turn in document.dialogue_turns:
            key = (turn.speaker, turn.content)
            if key not in seen:
                turns.append(turn)
                seen.add(key)
    return turns


def _merge_action_items(documents: list[StructuredDocument]) -> list[ActionItem]:
    items: list[ActionItem] = []
    seen: set[tuple[str, str, str]] = set()
    for document in documents:
        for item in document.action_items:
            key = (item.owner, item.task, item.due)
            if key not in seen:
                items.append(item)
                seen.add(key)
    return items


def _dedupe_strings(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        clean = value.strip()
        if clean and clean not in seen:
            result.append(clean)
            seen.add(clean)
    return result
