from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

OutputMode = Literal["dialogue", "minutes", "report"]
ProviderName = Literal["mock", "real"]


class Section(BaseModel):
    heading: str
    items: list[str] = Field(default_factory=list)


class DialogueTurn(BaseModel):
    speaker: str
    content: str


class ActionItem(BaseModel):
    owner: str = "未指定"
    task: str
    due: str = "未定"


class StructuredDocument(BaseModel):
    mode: OutputMode
    title: str
    summary: str
    sections: list[Section] = Field(default_factory=list)
    dialogue_turns: list[DialogueTurn] = Field(default_factory=list)
    action_items: list[ActionItem] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def to_json_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")


class RefineRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    raw_text: str
    mode: OutputMode
    refine_rounds: int = Field(default=1, ge=0, le=2)
    provider: ProviderName = "real"


class RefineResult(BaseModel):
    markdown: str
    data: StructuredDocument
    metadata: dict[str, Any] = Field(default_factory=dict)
