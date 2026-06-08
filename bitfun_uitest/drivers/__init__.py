from __future__ import annotations

from bitfun_uitest.config import TestConfig
from bitfun_uitest.platforms.oh import OpenHarmonyDriver
from bitfun_uitest.platforms.webdriver import EmbeddedWebDriverDriver
from bitfun_uitest.ui import UiDriver


def create_driver(config: TestConfig) -> UiDriver:
    if config.platform == "oh":
        return OpenHarmonyDriver.from_env()
    if config.platform in {"win", "mac"}:
        return EmbeddedWebDriverDriver.from_env(config.platform)
    raise ValueError(f"Unsupported platform: {config.platform}")

