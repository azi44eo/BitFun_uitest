from fastapi import FastAPI

from bitfun_mock_llm_server.api.routes import create_router
from bitfun_mock_llm_server.config import Settings, load_settings


def create_app(settings: Settings | None = None) -> FastAPI:
    app = FastAPI(
        title="BitFun Mock LLM Server",
        description="Deterministic OpenAI-compatible mock LLM server for BitFun UI tests.",
        version="0.1.0",
    )
    app.include_router(create_router(settings or load_settings()))
    return app


app = create_app()
