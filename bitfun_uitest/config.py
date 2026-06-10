from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class TestConfig:
    platform: str
    local_config: dict[str, Any]

    def get_local_string(self, *path: str) -> str | None:
        value: Any = self.local_config
        for key in path:
            if not isinstance(value, dict) or key not in value:
                return None
            value = value[key]
        if not isinstance(value, str) or not value.strip():
            return None
        return value


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


def load_local_config(path: str | None = None, *, root: Path | None = None) -> dict[str, Any]:
    config_path = _resolve_local_config_path(path, root=root)
    if config_path is None or not config_path.exists():
        return {}

    with config_path.open("r", encoding="utf-8") as file:
        payload = json.load(file)
    if not isinstance(payload, dict):
        raise ValueError(f"Local config must be a JSON object: {config_path}")
    return payload


def _resolve_local_config_path(path: str | None = None, *, root: Path | None = None) -> Path | None:
    raw_path = path or os.environ.get("BITFUN_LOCAL_CONFIG")
    if raw_path:
        return Path(raw_path).expanduser().resolve()

    base = root or Path.cwd()
    return (base / "local-config.json").resolve()
