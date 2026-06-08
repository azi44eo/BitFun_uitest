from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class TestConfig:
    platform: str


def normalize_platform(value: str | None) -> str:
    platform = (value or os.environ.get("BITFUN_TEST_PLATFORM") or "oh").strip().lower()
    aliases = {
        "open_harmony": "oh",
        "openharmony": "oh",
        "harmony": "oh",
        "windows": "win",
        "macos": "mac",
        "darwin": "mac",
    }
    platform = aliases.get(platform, platform)
    if platform not in {"oh", "win", "mac"}:
        raise ValueError(f"Unsupported platform: {platform!r}. Expected one of: oh, win, mac.")
    return platform

