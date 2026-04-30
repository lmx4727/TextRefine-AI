from __future__ import annotations

import json

from text_refine_ai.schemas import OutputMode, StructuredDocument

MODE_LABELS: dict[OutputMode, str] = {
    "dialogue": "对话稿",
    "minutes": "会议纪要",
    "report": "报告初稿",
}


def build_generation_prompt(
    mode: OutputMode,
    text: str,
    chunk_index: int,
    total_chunks: int,
) -> str:
    label = MODE_LABELS[mode]
    return f"""你是 TextRefineAI 的文本结构化 Agent。
请将以下内容整理为{label}，默认使用中文，保持原意，不保存或复述完整原始输入。

输出要求：
1. 只输出 JSON，不要输出 Markdown。
2. JSON 顶层字段必须包含 mode、title、summary、sections、dialogue_turns、action_items、metadata。
3. sections 使用 heading 和 items。
4. dialogue_turns 使用 speaker 和 content，仅对话稿模式需要填充。
5. action_items 使用 owner、task、due，会议纪要和报告初稿模式优先填充。

当前分块：{chunk_index}/{total_chunks}
目标格式：{label}
文本：
{text}
"""


def build_refinement_prompt(mode: OutputMode, document: StructuredDocument) -> str:
    label = MODE_LABELS[mode]
    payload = json.dumps(document.to_json_dict(), ensure_ascii=False)
    return f"""你是 TextRefineAI 的优化 Agent。
请检查以下{label} JSON 的逻辑顺序、表达清晰度和结构完整性，默认使用中文。
只输出同样 schema 的 JSON，不要添加解释。

JSON：
{payload}
"""
