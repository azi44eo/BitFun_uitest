from __future__ import annotations

import asyncio
import re
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse

from bitfun_mock_llm_server.config import Settings, load_settings
from bitfun_mock_llm_server.request_parser import parse_chat_request
from bitfun_mock_llm_server.responses.chat_completions import (
    build_chat_completion,
    stream_chat_completion,
)
from bitfun_mock_llm_server.scenarios.loader import ScenarioLoader
from bitfun_mock_llm_server.scenarios.schema import AssistantTurn, Scenario, ToolCall, Turn


def create_router(settings: Settings | None = None) -> APIRouter:
    settings = settings or load_settings()
    scenario_loader = ScenarioLoader(settings.scenarios_dir)
    router = APIRouter()

    @router.get("/health")
    def health() -> dict[str, object]:
        return {
            "status": "ok",
            "service": "bitfun-mock-llm-server",
            "scenarios_dir": str(scenario_loader.scenarios_dir),
            "scenario_count": scenario_loader.count(),
        }

    @router.get("/v1/scenarios")
    def list_scenarios() -> dict[str, object]:
        return {"data": scenario_loader.list_ids()}

    @router.get("/v1/models")
    @router.get("/models")
    def list_models() -> dict[str, object]:
        return {
            "data": [
                {
                    "id": "bitfun-mock",
                    "display_name": "bitfun-mock",
                },
                {
                    "id": "bitfun-mock-tools",
                    "display_name": "bitfun-mock-tools",
                },
                {
                    "id": "bitfun-mock-files",
                    "display_name": "bitfun-mock-files",
                },
            ],
        }

    @router.post("/v1/chat/completions")
    async def chat_completions(request: Request):
        payload = await request.json()
        aux_turn = _auxiliary_turn(payload)
        if aux_turn is not None:
            aux_scenario = Scenario(
                scenario_id="auxiliary",
                description="Auxiliary BitFun compatibility response.",
                turns=[Turn(assistant=aux_turn)],
            )
            stream = payload.get("stream")
            if isinstance(stream, bool) and stream:
                return StreamingResponse(
                    stream_chat_completion(payload, aux_scenario, aux_turn),
                    media_type="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
                )
            return JSONResponse(build_chat_completion(payload, aux_scenario, aux_turn))

        parsed = parse_chat_request(
            payload,
            default_scenario_id=None if settings.strict_scenario else settings.default_scenario_id,
        )

        if not parsed.scenario_id:
            raise HTTPException(
                status_code=400,
                detail="Missing mock scenario marker. Add [MOCK_SCENARIO] id=<scenario_id> [/MOCK_SCENARIO].",
            )

        try:
            scenario = scenario_loader.load(parsed.scenario_id)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

        if scenario is None:
            raise HTTPException(
                status_code=404,
                detail=f"Scenario not found: {parsed.scenario_id}",
            )

        turn_index = parsed.turn_index
        if scenario.scenario_id == "error_then_success" and parsed.turn_index == 0:
            attempt_key = parsed.control.get("run_id") or parsed.control.get("attempt_key") or scenario.scenario_id
            turn_index = min(_next_scenario_attempt(f"{scenario.scenario_id}:{attempt_key}"), len(scenario.turns) - 1)

        turn = scenario.get_turn(turn_index)
        if turn.delay_ms > 0:
            await asyncio.sleep(turn.delay_ms / 1000)
        if turn.error_status is not None:
            raise HTTPException(status_code=turn.error_status, detail=turn.error_detail or "Mock scenario error.")
        stream = parsed.stream if parsed.stream is not None else scenario.default_stream

        if stream:
            return StreamingResponse(
                stream_chat_completion(payload, scenario, turn),
                media_type="text/event-stream",
                headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
            )

        return JSONResponse(build_chat_completion(payload, scenario, turn))

    return router


def _auxiliary_turn(payload: dict[str, Any]) -> AssistantTurn | None:
    if _is_session_title_request(payload):
        return AssistantTurn(final_text="Mock 会话")

    if _has_mock_marker(payload):
        return None

    tools = payload.get("tools")
    if isinstance(tools, list) and tools:
        if _has_tool_result_message(payload):
            return AssistantTurn(final_text="Tool capability probe completed.")
        tool_call = _first_tool_call(tools, payload)
        if tool_call is not None:
            return AssistantTurn(tool_calls=[tool_call])

    return None


def _has_mock_marker(payload: dict[str, Any]) -> bool:
    for text in _iter_message_text(payload):
        if "[MOCK_SCENARIO]" in text:
            return True
    return False


def _is_session_title_request(payload: dict[str, Any]) -> bool:
    joined = "\n".join(_iter_message_text(payload)).lower()
    return "session title" in joined and "generate session title" in joined


def _has_tool_result_message(payload: dict[str, Any]) -> bool:
    messages = payload.get("messages")
    if not isinstance(messages, list):
        return False
    for message in messages:
        if isinstance(message, dict) and str(message.get("role") or "").lower() in {"tool", "function"}:
            return True
    return False


def _first_tool_call(tools: list[object], payload: dict[str, Any]) -> ToolCall | None:
    first = tools[0] if tools else None
    if not isinstance(first, dict):
        return None
    function = first.get("function")
    if not isinstance(function, dict):
        return None
    name = function.get("name")
    if not isinstance(name, str) or not name:
        return None
    arguments: dict[str, Any] = {}
    prompt = "\n".join(_iter_message_text(payload))
    city_match = re.search(r"city\s*=\s*([A-Za-z\u4e00-\u9fff_-]+)", prompt)
    if city_match:
        arguments["city"] = city_match.group(1)
    return ToolCall(id=f"call_{name}", name=name, arguments=arguments)


def _iter_message_text(payload: dict[str, Any]) -> list[str]:
    messages = payload.get("messages")
    if not isinstance(messages, list):
        return []

    texts: list[str] = []
    for message in messages:
        if not isinstance(message, dict):
            continue
        content = message.get("content")
        if isinstance(content, str):
            texts.append(content)
        elif isinstance(content, list):
            for part in content:
                if isinstance(part, dict) and isinstance(part.get("text"), str):
                    texts.append(part["text"])
    return texts


router = create_router()


_SCENARIO_ATTEMPTS: dict[str, int] = {}


def _next_scenario_attempt(scenario_id: str) -> int:
    current = _SCENARIO_ATTEMPTS.get(scenario_id, 0)
    _SCENARIO_ATTEMPTS[scenario_id] = current + 1
    return current
