from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse

from bitfun_mock_llm_server.config import Settings, load_settings
from bitfun_mock_llm_server.request_parser import parse_chat_request
from bitfun_mock_llm_server.responses.chat_completions import (
    build_chat_completion,
    stream_chat_completion,
)
from bitfun_mock_llm_server.scenarios.loader import ScenarioLoader


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

    @router.post("/v1/chat/completions")
    async def chat_completions(request: Request):
        payload = await request.json()
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

        turn = scenario.get_turn(parsed.turn_index)
        stream = parsed.stream if parsed.stream is not None else scenario.default_stream

        if stream:
            return StreamingResponse(
                stream_chat_completion(payload, scenario, turn),
                media_type="text/event-stream",
                headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
            )

        return JSONResponse(build_chat_completion(payload, scenario, turn))

    return router


router = create_router()
