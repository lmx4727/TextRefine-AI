from __future__ import annotations

from text_refine_ai.schemas import StructuredDocument


def render_markdown(document: StructuredDocument) -> str:
    lines: list[str] = [f"# {document.title}", "", "## 摘要", document.summary, ""]

    for section in document.sections:
        lines.extend([f"## {section.heading}"])
        if section.items:
            lines.extend(f"- {item}" for item in section.items)
        else:
            lines.append("- 暂无")
        lines.append("")

    if document.dialogue_turns:
        lines.extend(["## 对话稿"])
        for turn in document.dialogue_turns:
            lines.append(f"{turn.speaker}：{turn.content}")
        lines.append("")

    if document.action_items:
        lines.extend(["## 后续行动"])
        for item in document.action_items:
            lines.append(f"- {item.owner}：{item.task}（截止：{item.due}）")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"
