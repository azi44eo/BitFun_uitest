from __future__ import annotations

from typing import Any

from bitfun_uitest.platforms.dom import DomTestIdMixin


class EmbeddedWebDriverDriver(DomTestIdMixin):
    """Placeholder for Windows/macOS BitFun embedded WebDriver integration."""

    def __init__(self, platform: str) -> None:
        self.platform = platform

    @classmethod
    def from_env(cls, platform: str) -> "EmbeddedWebDriverDriver":
        return cls(platform)

    def start(self) -> None:
        raise NotImplementedError(
            f"{self.platform} adapter is not wired yet. It will connect BitFun embedded WebDriver "
            "and expose the same data-testid API as the OH adapter."
        )

    def close(self) -> None:
        return None

    def evaluate(self, expression: str) -> Any:
        raise NotImplementedError("Embedded WebDriver JavaScript execution is not wired yet.")

