from __future__ import annotations

from typing import Any, Literal

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class ToolCall(BaseModel):
    model_config = ConfigDict(extra="allow")

    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    id: str | None = None


class ShellCommand(BaseModel):
    command: str
    output: str = ""
    exit_code: int = 0


class FileChange(BaseModel):
    path: str
    action: Literal["create", "modify", "delete"] = "modify"
    content: str | None = None


class MiniAppFile(BaseModel):
    path: str
    content: str


class MiniApp(BaseModel):
    title: str
    files: list[MiniAppFile] = Field(default_factory=list)


class AssistantTurn(BaseModel):
    thinking: list[str] = Field(default_factory=list)
    tool_calls: list[ToolCall] = Field(default_factory=list)
    shell_commands: list[ShellCommand] = Field(default_factory=list)
    file_changes: list[FileChange] = Field(default_factory=list)
    miniapp: MiniApp | None = None
    final_text: str = ""
    stream_chunks: list[str] | None = None


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
