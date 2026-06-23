from __future__ import annotations

from typing import Any, Literal

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class ToolCall(BaseModel):
    model_config = ConfigDict(extra="allow")

    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    id: str | None = None


class AssistantTurn(BaseModel):
    thinking: list[str] = Field(default_factory=list)
    tool_calls: list[ToolCall] = Field(default_factory=list)
    final_text: str = ""
    stream_chunks: list[str] | None = None
    delay_ms: int = 0
    error_status: int | None = None
    error_detail: str | None = None


class Turn(BaseModel):
    assistant: AssistantTurn


class Scenario(BaseModel):
    scenario_id: str
    description: str = ""
    mode: Literal["chat_completions"] = "chat_completions"
    default_stream: bool = Field(
        default=False,
        validation_alias=AliasChoices("default_stream", "stream"),
    )
    turns: list[Turn]

    def get_turn(self, turn_index: int) -> AssistantTurn:
        if not self.turns:
            raise ValueError(f"Scenario has no turns: {self.scenario_id}")
        if turn_index < 0 or turn_index >= len(self.turns):
            return self.turns[0].assistant
        return self.turns[turn_index].assistant
