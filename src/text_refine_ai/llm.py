from __future__ import annotations

import json
import os
import re
from typing import Protocol

import httpx

from text_refine_ai.exceptions import ProviderConfigurationError, ProviderResponseError
from text_refine_ai.schemas import (
    ActionItem,
    DialogueTurn,
    OutputMode,
    Section,
    StructuredDocument,
)


class LLMClient(Protocol):
    provider_name: str

    def generate(self, prompt: str, mode: OutputMode) -> StructuredDocument:
        ...

    def refine(self, prompt: str, mode: OutputMode, document: StructuredDocument) -> StructuredDocument:
        ...


class MockLLMClient:
    provider_name = "mock"

    def generate(self, prompt: str, mode: OutputMode) -> StructuredDocument:
        return _mock_document(mode)

    def refine(self, prompt: str, mode: OutputMode, document: StructuredDocument) -> StructuredDocument:
        refined = document.model_copy(deep=True)
        refined.summary = f"{document.summary} 已完成逻辑检查与表达优化。"
        return refined


class OpenAICompatibleClient:
    provider_name = "real"

    def __init__(self, api_key: str, base_url: str, model: str, timeout: float = 60.0) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    @classmethod
    def from_env(cls) -> "OpenAICompatibleClient":
        values = {
            "TEXTREFINE_API_KEY": os.getenv("TEXTREFINE_API_KEY"),
            "TEXTREFINE_BASE_URL": os.getenv("TEXTREFINE_BASE_URL"),
            "TEXTREFINE_MODEL": os.getenv("TEXTREFINE_MODEL"),
        }
        missing = [name for name, value in values.items() if not value]
        if missing:
            joined = ", ".join(missing)
            raise ProviderConfigurationError(f"缺少真实模型配置: {joined}")
        return cls(
            api_key=values["TEXTREFINE_API_KEY"] or "",
            base_url=values["TEXTREFINE_BASE_URL"] or "",
            model=values["TEXTREFINE_MODEL"] or "",
        )

    def generate(self, prompt: str, mode: OutputMode) -> StructuredDocument:
        return self._request_structured_document(prompt, mode)

    def refine(self, prompt: str, mode: OutputMode, document: StructuredDocument) -> StructuredDocument:
        return self._request_structured_document(prompt, mode)

    def _request_structured_document(self, prompt: str, mode: OutputMode) -> StructuredDocument:
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "你只输出符合要求的 JSON。"},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
        }
        try:
            response = httpx.post(url, headers=headers, json=payload, timeout=self.timeout)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise ProviderResponseError(f"真实模型请求失败: {exc}") from exc

        try:
            content = response.json()["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ProviderResponseError("真实模型响应缺少 choices[0].message.content") from exc

        return _document_from_json_content(content, mode)


def create_llm_client(provider: str) -> LLMClient:
    if provider == "mock":
        return MockLLMClient()
    if provider == "real":
        return OpenAICompatibleClient.from_env()
    raise ProviderConfigurationError(f"未知 provider: {provider}")


def _document_from_json_content(content: str, mode: OutputMode) -> StructuredDocument:
    try:
        data = json.loads(_strip_json_fence(content))
    except json.JSONDecodeError as exc:
        raise ProviderResponseError("真实模型响应不是合法 JSON") from exc

    data.setdefault("mode", mode)
    data.setdefault("title", _title_for_mode(mode))
    data.setdefault("summary", "")
    data.setdefault("sections", [])
    data.setdefault("dialogue_turns", [])
    data.setdefault("action_items", [])
    data.setdefault("metadata", {})
    return StructuredDocument.model_validate(data)


def _strip_json_fence(content: str) -> str:
    match = re.search(r"```(?:json)?\s*(.*?)\s*```", content, flags=re.DOTALL)
    return match.group(1) if match else content.strip()


def _mock_document(mode: OutputMode) -> StructuredDocument:
    if mode == "dialogue":
        return StructuredDocument(
            mode=mode,
            title="结构化对话稿",
            summary="已将口语化内容整理为清晰对话。",
            sections=[
                Section(heading="对话脉络", items=["明确问题背景。", "整理回应与确认。"]),
            ],
            dialogue_turns=[
                DialogueTurn(speaker="A", content="提出问题与背景。"),
                DialogueTurn(speaker="B", content="给出方案并确认下一步。"),
            ],
            action_items=[],
        )
    if mode == "report":
        return StructuredDocument(
            mode=mode,
            title="结构化报告初稿",
            summary="已将零散信息整理为报告草稿。",
            sections=[
                Section(heading="背景", items=["梳理现状与问题。"]),
                Section(heading="分析", items=["归纳核心原因与影响。"]),
                Section(heading="建议", items=["形成可执行后续方案。"]),
            ],
            action_items=[
                ActionItem(owner="未指定", task="补充关键数据并完善报告", due="未定"),
            ],
        )
    return StructuredDocument(
        mode=mode,
        title="结构化会议纪要",
        summary="已将会议内容整理为背景、讨论、决策与行动项。",
        sections=[
            Section(heading="背景", items=["明确会议讨论的主要目标。"]),
            Section(heading="讨论内容", items=["归纳主要观点并去除重复表达。"]),
            Section(heading="决策结果", items=["形成统一的后续推进方向。"]),
        ],
        action_items=[
            ActionItem(owner="张三", task="推进后续测试并同步结果", due="未定"),
        ],
    )


def _title_for_mode(mode: OutputMode) -> str:
    return {
        "dialogue": "结构化对话稿",
        "minutes": "结构化会议纪要",
        "report": "结构化报告初稿",
    }[mode]
