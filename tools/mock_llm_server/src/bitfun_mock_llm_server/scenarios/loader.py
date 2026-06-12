from __future__ import annotations

import json
from pathlib import Path

from pydantic import ValidationError

from bitfun_mock_llm_server.scenarios.schema import Scenario


class ScenarioLoader:
    def __init__(self, scenarios_dir: Path):
        self.scenarios_dir = scenarios_dir

    def load(self, scenario_id: str) -> Scenario | None:
        path = self.scenarios_dir / f"{scenario_id}.json"
        if not path.exists():
            return None

        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            return Scenario.model_validate(raw)
        except (json.JSONDecodeError, ValidationError) as exc:
            raise ValueError(f"Invalid scenario file: {path}") from exc

    def list_ids(self) -> list[str]:
        if not self.scenarios_dir.exists():
            return []
        return sorted(path.stem for path in self.scenarios_dir.glob("*.json") if path.is_file())

    def count(self) -> int:
        return len(self.list_ids())

