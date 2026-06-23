from __future__ import annotations

import json
import time
import uuid
from typing import Any

from bitfun_mock_llm_server.scenarios.schema import AssistantTurn, Scenario, ToolCall


def build_chat_completion(
    request_payload: dict[str, Any],
    scenario: Scenario,
    turn: AssistantTurn,
) -> dict[str, Any]:
    completion_id = _completion_id()
    model = _model_name(request_payload)
    finish_reason = _finish_reason(turn)

    return {
        "id": completion_id,
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": turn.final_text,
                    "reasoning_content": _reasoning_text(turn),
                    "tool_calls": [_tool_call_message(call, index) for index, call in enumerate(turn.tool_calls)],
                    "bitfun_mock": _bitfun_mock_payload(scenario, turn),
                },
                "finish_reason": finish_reason,
            }
        ],
        "usage": {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
        },
        "bitfun_mock": {
            "scenario_id": scenario.scenario_id,
            "mode": scenario.mode,
            "deterministic": True,
        },
    }


async def stream_chat_completion(
    request_payload: dict[str, Any],
    scenario: Scenario,
    turn: AssistantTurn,
):
    completion_id = _completion_id()
    created = int(time.time())
    model = _model_name(request_payload)

    yield _sse(_chunk(completion_id, created, model, {"role": "assistant"}))

    for thought in turn.thinking:
        yield _sse(_chunk(completion_id, created, model, {"reasoning_content": thought + "\n"}))

    for index, call in enumerate(turn.tool_calls):
        yield _sse(
            _chunk(
                completion_id,
                created,
                model,
                {"tool_calls": [_tool_call_delta(call, index)]},
            )
        )

    for text in _content_chunks(turn):
        yield _sse(_chunk(completion_id, created, model, {"content": text}))

    yield _sse(
        {
            "id": completion_id,
            "object": "chat.completion.chunk",
            "created": created,
            "model": model,
            "choices": [{"index": 0, "delta": {}, "finish_reason": _finish_reason(turn)}],
        }
    )
    yield "data: [DONE]\n\n"


def _chunk(completion_id: str, created: int, model: str, delta: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": completion_id,
        "object": "chat.completion.chunk",
        "created": created,
        "model": model,
        "choices": [{"index": 0, "delta": delta, "finish_reason": None}],
    }


def _sse(data: dict[str, Any]) -> str:
    return "data: " + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n\n"


def _completion_id() -> str:
    return f"chatcmpl-mock-{uuid.uuid4().hex[:12]}"


def _model_name(request_payload: dict[str, Any]) -> str:
    model = request_payload.get("model")
    return model if isinstance(model, str) and model else "bitfun-mock-model"


def _reasoning_text(turn: AssistantTurn) -> str:
    return "\n".join(turn.thinking)


def _tool_call_message(call: ToolCall, index: int) -> dict[str, Any]:
    return {
        "id": call.id or f"call_mock_{index}",
        "type": "function",
        "function": {
            "name": call.name,
            "arguments": json.dumps(call.arguments, ensure_ascii=False),
        },
    }


def _tool_call_delta(call: ToolCall, index: int) -> dict[str, Any]:
    return {
        "index": index,
        "id": call.id or f"call_mock_{index}",
        "type": "function",
        "function": {
            "name": call.name,
            "arguments": json.dumps(call.arguments, ensure_ascii=False),
        },
    }


def _content_chunks(turn: AssistantTurn) -> list[str]:
    if turn.tool_calls and not turn.final_text and turn.stream_chunks is None:
        return []
    if turn.stream_chunks is not None:
        return turn.stream_chunks
    if not turn.final_text:
        return []
    return [turn.final_text]


def _finish_reason(turn: AssistantTurn) -> str:
    if turn.tool_calls and not turn.final_text:
        return "tool_calls"
    return "stop"


def _bitfun_mock_payload(scenario: Scenario, turn: AssistantTurn) -> dict[str, Any]:
    return {
        "scenario_id": scenario.scenario_id,
        "thinking": turn.thinking,
    }

