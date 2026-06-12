from __future__ import annotations

import uvicorn

from bitfun_mock_llm_server.config import load_settings


def main() -> None:
    settings = load_settings()
    uvicorn.run(
        "bitfun_mock_llm_server.main:app",
        host=settings.host,
        port=settings.port,
        reload=False,
    )


if __name__ == "__main__":
    main()

