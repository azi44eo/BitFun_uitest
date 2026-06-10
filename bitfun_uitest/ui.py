from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Protocol


@dataclass(frozen=True)
class UiElement:
    test_id: str
    tag_name: str
    text: str
    value: str | None
    visible: bool
    disabled: bool
    rect: dict[str, float]
    attributes: dict[str, str]


class UiDriver(Protocol):
    def start(self) -> None:
        ...

    def close(self) -> None:
        ...

    def wait_for_test_id(
        self,
        test_id: str,
        timeout: float = 15.0,
        attrs: Mapping[str, str] | None = None,
    ) -> UiElement:
        ...

    def wait_for_test_id_gone(self, test_id: str, timeout: float = 15.0) -> None:
        ...

    def find_by_test_id(self, test_id: str, attrs: Mapping[str, str] | None = None) -> UiElement | None:
        ...

    def click_by_test_id(self, test_id: str, attrs: Mapping[str, str] | None = None) -> None:
        ...

    def fill_by_test_id(self, test_id: str, text: str, attrs: Mapping[str, str] | None = None) -> None:
        ...

    def evaluate(self, expression: str) -> Any:
        ...
