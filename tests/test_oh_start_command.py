from __future__ import annotations

from bitfun_uitest.platforms.oh import OhAppConfig, OpenHarmonyDriver


class FakeHdc:
    def __init__(self) -> None:
        self.commands: list[str] = []

    def shell(self, command: str, *, timeout: int = 30) -> str:
        self.commands.append(command)
        return ""

    def run(self, *args: str, check: bool = True, timeout: int = 30) -> str:
        self.commands.append(" ".join(args))
        return ""


def test_oh_start_app_appends_formatted_llm_args(monkeypatch):
    monkeypatch.setenv("BITFUN_TEST_LLM_BASE_URL", "http://127.0.0.1:18787/v1")
    monkeypatch.setenv("BITFUN_TEST_LLM_MODEL", "bitfun-mock")
    monkeypatch.setenv("BITFUN_TEST_LLM_API_KEY", "mock-key")
    monkeypatch.setenv(
        "BITFUN_OH_APP_START_EXTRA_ARGS",
        "--ps llmBaseUrl {llm_base_url} --ps llmModel {llm_model} --ps llmApiKey {llm_api_key}",
    )

    hdc = FakeHdc()
    driver = OpenHarmonyDriver(
        hdc,
        OhAppConfig(bundle="bundle", module="module", ability="ability"),
    )

    driver._start_app()

    assert hdc.commands == [
        "aa start -b bundle -m module -a ability "
        "--ps llmBaseUrl http://127.0.0.1:18787/v1 "
        "--ps llmModel bitfun-mock --ps llmApiKey mock-key"
    ]


def test_oh_custom_start_command_can_use_llm_placeholders(monkeypatch):
    monkeypatch.setenv("BITFUN_TEST_LLM_BASE_URL", "http://127.0.0.1:18788/v1")
    monkeypatch.setenv(
        "BITFUN_OH_APP_START_COMMAND",
        "aa start -b {bundle} -m {module} -a {ability} --ps llmBaseUrl {llm_base_url}",
    )

    hdc = FakeHdc()
    driver = OpenHarmonyDriver(
        hdc,
        OhAppConfig(bundle="bundle", module="module", ability="ability"),
    )

    driver._start_app()

    assert hdc.commands == [
        "aa start -b bundle -m module -a ability --ps llmBaseUrl http://127.0.0.1:18788/v1"
    ]


def test_oh_close_stops_app_without_cleaning_data(monkeypatch):
    monkeypatch.delenv("BITFUN_KEEP_APP_OPEN", raising=False)

    hdc = FakeHdc()
    driver = OpenHarmonyDriver(
        hdc,
        OhAppConfig(bundle="bundle", module="module", ability="ability", clean_app_data=True),
    )

    driver.close()

    assert hdc.commands == ["shell aa force-stop bundle"]
