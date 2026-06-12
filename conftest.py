from __future__ import annotations

import os
import socket
import sys
import threading
import time
import urllib.request
from pathlib import Path

import pytest
import uvicorn

from bitfun_uitest.config import TestConfig, load_local_config, normalize_platform
from bitfun_uitest.drivers import create_driver
from bitfun_uitest.platforms.hdc import HdcClient
from bitfun_uitest.ui import UiDriver

ROOT = Path(__file__).resolve().parent
MOCK_SERVER_SRC = ROOT / "tools" / "mock_llm_server" / "src"
MOCK_SCENARIOS_DIR = ROOT / "mock_scenarios"


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--platform",
        action="store",
        default=None,
        help="Target platform: oh, win, or mac. Defaults to BITFUN_TEST_PLATFORM or oh.",
    )
    parser.addoption(
        "--local-config",
        action="store",
        default=None,
        help="Path to a local JSON config file. Defaults to BITFUN_LOCAL_CONFIG or local-config.json.",
    )
    parser.addoption(
        "--mock-llm-device-port",
        action="store",
        default=None,
        help="OH-side TCP port for the mock LLM server. Defaults to BITFUN_MOCK_LLM_DEVICE_PORT or 18787.",
    )


@pytest.fixture(scope="session")
def test_config(pytestconfig: pytest.Config) -> TestConfig:
    return TestConfig(
        platform=normalize_platform(pytestconfig.getoption("--platform")),
        local_config=load_local_config(
            pytestconfig.getoption("--local-config"),
            root=pytestconfig.rootpath,
        ),
    )


@pytest.fixture(scope="session", autouse=True)
def mock_llm_server_session(pytestconfig: pytest.Config, test_config: TestConfig):
    if str(MOCK_SERVER_SRC) not in sys.path:
        sys.path.insert(0, str(MOCK_SERVER_SRC))

    host_port = _free_tcp_port()
    device_port = int(
        pytestconfig.getoption("--mock-llm-device-port")
        or os.environ.get("BITFUN_MOCK_LLM_DEVICE_PORT")
        or "18787"
    )
    bitfun_base_url = (
        f"http://127.0.0.1:{device_port}/v1"
        if test_config.platform == "oh"
        else f"http://127.0.0.1:{host_port}/v1"
    )

    previous_env = _patch_env(
        {
            "BITFUN_MOCK_HOST": "127.0.0.1",
            "BITFUN_MOCK_PORT": str(host_port),
            "BITFUN_MOCK_SCENARIOS_DIR": str(MOCK_SCENARIOS_DIR),
            "BITFUN_TEST_LLM_BASE_URL": bitfun_base_url,
            "BITFUN_TEST_LLM_MODEL": "bitfun-mock",
            "BITFUN_TEST_LLM_API_KEY": "mock-key",
        }
    )
    hdc_client: HdcClient | None = None
    server: uvicorn.Server | None = None
    thread: threading.Thread | None = None

    try:
        from bitfun_mock_llm_server.main import create_app

        server = uvicorn.Server(
            uvicorn.Config(
                create_app(),
                host="127.0.0.1",
                port=host_port,
                log_level=os.environ.get("BITFUN_MOCK_LLM_LOG_LEVEL", "warning"),
                access_log=False,
            )
        )
        thread = threading.Thread(target=server.run, name="bitfun-mock-llm-server", daemon=True)
        thread.start()

        _wait_http_ok(f"http://127.0.0.1:{host_port}/health")

        if test_config.platform == "oh" and not _env_flag("BITFUN_MOCK_LLM_SKIP_HDC"):
            hdc_client = HdcClient()
            hdc_client.remove_rport(device_port)
            hdc_client.rport(device_port, host_port)

        yield {
            "host_port": host_port,
            "device_port": device_port,
            "host_base_url": f"http://127.0.0.1:{host_port}/v1",
            "bitfun_base_url": bitfun_base_url,
            "scenarios_dir": str(MOCK_SCENARIOS_DIR),
        }
    finally:
        try:
            if hdc_client is not None:
                hdc_client.remove_rport(device_port)
        finally:
            if server is not None:
                server.should_exit = True
            if thread is not None:
                thread.join(timeout=5)
            _restore_env(previous_env)


@pytest.fixture(scope="function")
def ui(test_config: TestConfig, mock_llm_server_session) -> UiDriver:
    driver = create_driver(test_config)
    driver.start()
    try:
        yield driver
    finally:
        driver.close()


def _patch_env(values: dict[str, str]) -> dict[str, str | None]:
    previous = {name: os.environ.get(name) for name in values}
    os.environ.update(values)
    return previous


def _restore_env(previous: dict[str, str | None]) -> None:
    for name, value in previous.items():
        if value is None:
            os.environ.pop(name, None)
        else:
            os.environ[name] = value


def _free_tcp_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _wait_http_ok(url: str, timeout: float = 10.0) -> None:
    deadline = time.time() + timeout
    last_error: Exception | None = None

    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=0.5) as response:
                if response.status == 200:
                    return
        except Exception as exc:
            last_error = exc
            time.sleep(0.1)

    raise RuntimeError(f"Mock LLM server not ready: {url}. Last error: {last_error}")


def _env_flag(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes", "y", "on"}
