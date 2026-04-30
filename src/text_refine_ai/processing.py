from __future__ import annotations

import re

FILLER_WORDS = (
    "嗯",
    "啊",
    "呃",
    "额",
    "就是",
    "那个",
    "这个",
    "然后呢",
)

SENTENCE_PATTERN = re.compile(r"[^。！？!?]+[。！？!?]?")


def preprocess_text(raw_text: str) -> str:
    text = (raw_text or "").replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\s+", "", text)
    for filler in FILLER_WORDS:
        text = text.replace(filler, "")

    sentences = [match.group(0).strip() for match in SENTENCE_PATTERN.finditer(text)]
    if not sentences and text:
        sentences = [text]

    cleaned: list[str] = []
    previous_key = ""
    for sentence in sentences:
        if not sentence:
            continue
        key = re.sub(r"[。！？!?，,、；;\s]+", "", sentence)
        if not key or key == previous_key or previous_key.endswith(key):
            continue
        cleaned.append(_ensure_terminal_punctuation(sentence))
        previous_key = key

    return "".join(cleaned)


def split_into_chunks(text: str, max_chars: int = 4000, overlap: int = 300) -> list[str]:
    clean_text = (text or "").strip()
    if not clean_text:
        return []
    if max_chars <= 0:
        raise ValueError("max_chars must be greater than 0")
    if overlap < 0 or overlap >= max_chars:
        raise ValueError("overlap must be >= 0 and smaller than max_chars")
    if len(clean_text) <= max_chars:
        return [clean_text]

    chunks: list[str] = []
    step = max_chars - overlap
    for start in range(0, len(clean_text), step):
        chunk = clean_text[start : start + max_chars]
        if chunk:
            chunks.append(chunk)
        if start + max_chars >= len(clean_text):
            break
    return chunks


def _ensure_terminal_punctuation(sentence: str) -> str:
    if sentence.endswith(("。", "！", "？", "!", "?")):
        return sentence
    return f"{sentence}。"
