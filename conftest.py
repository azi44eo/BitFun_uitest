from __future__ import annotations

import pytest

from bitfun_uitest.config import TestConfig, load_local_config, normalize_platform
from bitfun_uitest.drivers import create_driver
from bitfun_uitest.ui import UiDriver


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


@pytest.fixture(scope="session")
def test_config(pytestconfig: pytest.Config) -> TestConfig:
    return TestConfig(
        platform=normalize_platform(pytestconfig.getoption("--platform")),
        local_config=load_local_config(
            pytestconfig.getoption("--local-config"),
            root=pytestconfig.rootpath,
        ),
    )


@pytest.fixture(scope="function")
def ui(test_config: TestConfig) -> UiDriver:
    driver = create_driver(test_config)
    driver.start()
    try:
        yield driver
    finally:
        driver.close()
