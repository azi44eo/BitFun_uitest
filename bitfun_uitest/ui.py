from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class UiElement:
    test_id: str
    tag_name: str
    text: str
    value: str | None
    visible: bool
    disabled: bool
    rect: dict[str, float]


class UiDriver(Protocol):
    def start(self) -> None:
        ...

    def close(self) -> None:
        ...

    def wait_for_test_id(self, test_id: str, timeout: float = 15.0) -> UiElement:
        ...

    def find_by_test_id(self, test_id: str) -> UiElement | None:
        ...

    def click_by_test_id(self, test_id: str) -> None:
        ...

    def fill_by_test_id(self, test_id: str, text: str) -> None:
        ...

    def evaluate(self, expression: str) -> Any:
        ...

