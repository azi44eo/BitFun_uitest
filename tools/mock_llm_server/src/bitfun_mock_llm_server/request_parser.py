from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

MOCK_BLOCK_RE = re.compile(r"\[MOCK_SCENARIO\](.*?)\[/MOCK_SCENARIO\]", re.DOTALL | re.I)
KEY_VALUE_RE = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*?)\s*$")


@dataclass(frozen=True)
class ParsedChatRequest:
    scenario_id: str | None
    turn_index: int
    stream: bool | None


def parse_chat_request(payload: dict[str, Any], default_scenario_id: str | None) -> ParsedChatRequest:
    control = _extract_top_level_control(payload)
    control.update(_extract_marker_control(payload))

    scenario_id = control.get("id") or control.get("scenario_id") or default_scenario_id
    turn_index = _safe_int(control.get("turn") or control.get("turn_index"), default=0)
    stream = payload.get("stream")

    return ParsedChatRequest(
        scenario_id=str(scenario_id) if scenario_id else None,
        turn_index=turn_index,
        stream=stream if isinstance(stream, bool) else None,
    )


def _extract_top_level_control(payload: dict[str, Any]) -> dict[str, str]:
    control: dict[str, str] = {}

    scenario_id = payload.get("scenario_id")
    if isinstance(scenario_id, str):
        control["scenario_id"] = scenario_id

    metadata = payload.get("metadata")
    if isinstance(metadata, dict):
        for source_key, target_key in {
            "mock_scenario_id": "scenario_id",
            "scenario_id": "scenario_id",
            "mock_turn_index": "turn_index",
            "turn_index": "turn_index",
        }.items():
            value = metadata.get(source_key)
            if value is not None:
                control[target_key] = str(value)

    return control


def _extract_marker_control(payload: dict[str, Any]) -> dict[str, str]:
    for text in _iter_message_text(payload.get("messages", [])):
        match = MOCK_BLOCK_RE.search(text)
        if match:
            return _parse_control_block(match.group(1))
    return {}


def _iter_message_text(messages: object):
    if not isinstance(messages, list):
        return

    for message in messages:
        if not isinstance(message, dict):
            continue
        content = message.get("content")
        if isinstance(content, str):
            yield content
        elif isinstance(content, list):
            for part in content:
                if isinstance(part, dict) and isinstance(part.get("text"), str):
                    yield part["text"]


def _parse_control_block(block: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in block.strip().splitlines():
        match = KEY_VALUE_RE.match(line)
        if match:
            values[match.group(1)] = match.group(2)
    return values


def _safe_int(value: object, default: int) -> int:
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return default

