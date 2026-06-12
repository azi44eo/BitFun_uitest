from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Settings:
    host: str = "127.0.0.1"
    port: int = 8787
    scenarios_dir: Path = Path("scenarios")
    default_scenario_id: str = "simple_answer"
    strict_scenario: bool = False


def load_settings() -> Settings:
    config_path = Path(os.getenv("BITFUN_MOCK_CONFIG", "config/server.example.json"))
    values: dict[str, Any] = {}

    if config_path.exists():
        values.update(json.loads(config_path.read_text(encoding="utf-8")))

    scenarios_dir = Path(os.getenv("BITFUN_MOCK_SCENARIOS_DIR", values.get("scenarios_dir", "scenarios")))

    return Settings(
        host=os.getenv("BITFUN_MOCK_HOST", values.get("host", "127.0.0.1")),
        port=int(os.getenv("BITFUN_MOCK_PORT", values.get("port", 8787))),
        scenarios_dir=scenarios_dir,
        default_scenario_id=os.getenv(
            "BITFUN_MOCK_DEFAULT_SCENARIO",
            values.get("default_scenario_id", "simple_answer"),
        ),
        strict_scenario=_to_bool(
            os.getenv("BITFUN_MOCK_STRICT_SCENARIO", values.get("strict_scenario", False))
        ),
    )


def _to_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).lower() in {"1", "true", "yes", "y", "on"}

