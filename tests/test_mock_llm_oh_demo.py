from __future__ import annotations

import os
import time
import urllib.request

import pytest


MOCK_MODEL_NAME = "bitfun-mock"
MOCK_PROVIDER_NAME = "BitFun Mock LLM"
SIMPLE_ANSWER_TEXT = "\u8fd9\u662f BitFun Mock LLM Server \u7684\u56fa\u5b9a\u56de\u7b54\u3002"
MODELS_API_MODEL_NAME = "bitfun-mock-tools"
MODELS_API_PROVIDER_NAME = "BitFun Mock LLM Tools"
TOOL_TRACE_FINAL_TEXT = "Mock tool calls completed through BitFun tools."
THINKING_FINAL_TEXT = "Here is the final answer after reasoning."
SHELL_COMMAND_FINAL_TEXT = "Rendered one shell command result."
FILE_CHANGE_FINAL_TEXT = "Rendered one file change result."
MINIAPP_FINAL_TEXT = "Rendered one mini app result."


@pytest.fixture
def bitfun_mock_model_configured(ui, mock_llm_server_session):
    configure_mock_model_in_bitfun(ui, mock_llm_server_session)
    return {
        "model": MOCK_MODEL_NAME,
        "base_url": mock_llm_server_session["bitfun_base_url"],
        "api_key": os.environ["BITFUN_TEST_LLM_API_KEY"],
    }


def test_bitfun_can_chat_with_mock_llm_simple_answer(ui, bitfun_mock_model_configured):
    open_session_scene(ui)
    select_chat_model(ui, MOCK_MODEL_NAME)

    prompt = "[MOCK_SCENARIO]\nid=simple_answer\n[/MOCK_SCENARIO]"
    ui.fill_by_test_id("chat-input-textarea", prompt)
    ui.click_by_test_id("chat-input-send-btn")

    wait_for_body_text(ui, SIMPLE_ANSWER_TEXT, timeout=120)
    messages = ui.wait_for_test_id("flowchat-messages", timeout=10)
    assert SIMPLE_ANSWER_TEXT in messages.text


def test_bitfun_can_load_mock_models_from_models_endpoint(ui, mock_llm_server_session):
    configure_mock_model_from_models_api(
        ui,
        mock_llm_server_session,
        provider_name=MODELS_API_PROVIDER_NAME,
        model_name=MODELS_API_MODEL_NAME,
    )


def test_bitfun_can_execute_mock_tool_calls(ui, mock_llm_server_session):
    configure_mock_model_from_models_api(
        ui,
        mock_llm_server_session,
        provider_name=MODELS_API_PROVIDER_NAME,
        model_name=MODELS_API_MODEL_NAME,
    )

    open_session_scene(ui)
    select_chat_model(ui, MODELS_API_MODEL_NAME)

    prompt = "[MOCK_SCENARIO]\nid=tool_trace_demo\n[/MOCK_SCENARIO]"
    ui.fill_by_test_id("chat-input-textarea", prompt)
    ui.click_by_test_id("chat-input-send-btn")

    wait_for_body_text(ui, TOOL_TRACE_FINAL_TEXT, timeout=180)
    messages = ui.wait_for_test_id("flowchat-messages", timeout=10)
    assert TOOL_TRACE_FINAL_TEXT in messages.text


def test_bitfun_can_render_mock_thinking_panel(ui, bitfun_mock_model_configured):
    open_session_scene(ui)
    select_chat_model(ui, MOCK_MODEL_NAME)

    prompt = "[MOCK_SCENARIO]\nid=thinking_panel_demo\n[/MOCK_SCENARIO]"
    ui.fill_by_test_id("chat-input-textarea", prompt)
    ui.click_by_test_id("chat-input-send-btn")

    wait_for_body_text(ui, THINKING_FINAL_TEXT, timeout=120)
    require_test_ids_or_skip(ui, ["chat-thinking-panel", "chat-thinking-content"], "thinking panel")
    panel = ui.wait_for_test_id("chat-thinking-panel", timeout=15)
    content = ui.wait_for_test_id("chat-thinking-content", timeout=15)
    assert panel.visible
    assert content.visible


def test_bitfun_can_render_mock_shell_command_result(ui, bitfun_mock_model_configured):
    open_session_scene(ui)
    select_chat_model(ui, MOCK_MODEL_NAME)

    prompt = "[MOCK_SCENARIO]\nid=shell_command_demo\n[/MOCK_SCENARIO]"
    ui.fill_by_test_id("chat-input-textarea", prompt)
    ui.click_by_test_id("chat-input-send-btn")

    wait_for_body_text(ui, SHELL_COMMAND_FINAL_TEXT, timeout=120)
    card = wait_for_root_card_or_skip(ui, "chat-shell-command-card", "shell command result")
    expand_card_if_collapsed(
        ui,
        "chat-shell-command-card",
        toggle_test_id="chat-shell-command-toggle",
        content_test_ids=["chat-shell-command-output", "chat-shell-command-exit-code"],
    )
    command = ui.wait_for_test_id("chat-shell-command-text", timeout=15)
    output = ui.wait_for_test_id("chat-shell-command-output", timeout=15)
    exit_code = ui.wait_for_test_id("chat-shell-command-exit-code", timeout=15)
    assert card.visible
    assert "printf 'M README.md\\n'" in command.text
    assert "M README.md" in output.text
    assert exit_code.visible


def test_bitfun_can_render_mock_file_changes(ui, bitfun_mock_model_configured):
    open_session_scene(ui)
    select_chat_model(ui, MOCK_MODEL_NAME)

    prompt = "[MOCK_SCENARIO]\nid=file_change_demo\n[/MOCK_SCENARIO]"
    ui.fill_by_test_id("chat-input-textarea", prompt)
    ui.click_by_test_id("chat-input-send-btn")

    wait_for_body_text(ui, FILE_CHANGE_FINAL_TEXT, timeout=120)
    card = wait_for_root_card_or_skip(ui, "chat-file-change-card", "file change result")
    expand_card_if_collapsed(
        ui,
        "chat-file-change-card",
        toggle_test_id="chat-file-change-toggle",
        content_test_ids=["chat-file-change-preview"],
    )
    path = ui.wait_for_test_id("chat-file-change-path", timeout=15)
    action = ui.wait_for_test_id("chat-file-change-action", timeout=15)
    preview = ui.wait_for_test_id("chat-file-change-preview", timeout=15)
    assert card.visible
    assert path.text == "App.tsx" or ".bitfun-ui-test/mock-file-change/App.tsx" in path.text
    assert action.visible
    assert "Hello" in preview.text


def test_bitfun_can_render_mock_miniapp_result(ui, bitfun_mock_model_configured):
    open_session_scene(ui)
    select_chat_model(ui, MOCK_MODEL_NAME)

    prompt = "[MOCK_SCENARIO]\nid=miniapp_demo\n[/MOCK_SCENARIO]"
    ui.fill_by_test_id("chat-input-textarea", prompt)
    ui.click_by_test_id("chat-input-send-btn")

    wait_for_body_text(ui, MINIAPP_FINAL_TEXT, timeout=120)
    card = wait_for_root_card_or_skip(ui, "chat-miniapp-card", "miniapp result")
    expand_card_if_collapsed(
        ui,
        "chat-miniapp-card",
        toggle_test_id="chat-miniapp-open-btn",
        content_test_ids=["chat-miniapp-file-list", "chat-miniapp-file-row"],
    )
    title = ui.wait_for_test_id("chat-miniapp-title", timeout=15)
    file_list = ui.wait_for_test_id("chat-miniapp-file-list", timeout=15)
    file_row = ui.wait_for_test_id("chat-miniapp-file-row", timeout=15)
    assert card.visible
    assert "BitFun Mock Mini App" in title.text
    assert file_list.visible
    assert file_row.visible


def configure_mock_model_in_bitfun(ui, mock_llm_server_session) -> None:
    wait_for_mock_server_from_device(ui)
    open_settings_models(ui)
    if model_row_exists(ui, MOCK_MODEL_NAME):
        wait_for_model_success(ui, MOCK_MODEL_NAME)
        return

    ui.click_by_test_id("settings-model-create-first-config-btn")
    ui.click_by_test_id("settings-model-custom-config-btn")
    ui.fill_by_test_id("settings-model-provider-name-input", MOCK_PROVIDER_NAME)
    ui.fill_by_test_id("settings-model-api-key-input", os.environ["BITFUN_TEST_LLM_API_KEY"])
    ui.fill_by_test_id("settings-model-base-url-input", mock_llm_server_session["bitfun_base_url"])
    ui.fill_by_test_id("settings-model-manual-name-input", MOCK_MODEL_NAME)
    ui.click_by_test_id("settings-model-add-custom-btn")
    selected = ui.wait_for_test_id("settings-model-selected-row", attrs={"model-name": MOCK_MODEL_NAME}, timeout=15)
    assert selected.visible
    ui.click_by_test_id("settings-model-save-btn")
    wait_for_model_success(ui, MOCK_MODEL_NAME)


def configure_mock_model_from_models_api(
    ui,
    mock_llm_server_session,
    *,
    provider_name: str,
    model_name: str,
) -> None:
    wait_for_mock_server_from_device(ui)
    open_settings_models(ui)
    if model_row_exists(ui, model_name):
        wait_for_model_success(ui, model_name)
        return

    ui.click_by_test_id("settings-model-create-first-config-btn")
    ui.click_by_test_id("settings-model-custom-config-btn")
    ui.fill_by_test_id("settings-model-provider-name-input", provider_name)
    ui.fill_by_test_id("settings-model-api-key-input", os.environ["BITFUN_TEST_LLM_API_KEY"])
    ui.fill_by_test_id("settings-model-base-url-input", mock_llm_server_session["bitfun_base_url"])
    ui.click_by_test_id("settings-model-select-btn")
    ui.wait_for_test_id("settings-model-select-menu", timeout=30)
    ui.wait_for_test_id("settings-model-option", attrs={"model-name": model_name}, timeout=30)
    ui.click_by_test_id("settings-model-option", attrs={"model-name": model_name})
    selected = ui.wait_for_test_id("settings-model-selected-row", attrs={"model-name": model_name}, timeout=30)
    assert selected.visible
    ui.click_by_test_id("settings-model-save-btn")
    wait_for_model_success(ui, model_name)


def open_settings_models(ui) -> None:
    ui.click_by_test_id("nav-footer-more-btn")
    ui.wait_for_test_id("nav-footer-menu")
    ui.click_by_test_id("nav-footer-settings-item")
    ui.wait_for_test_id("settings-nav", timeout=30)
    ui.wait_for_test_id("settings-nav-tab", attrs={"settings-tab": "models"}, timeout=30)
    ui.click_by_test_id("settings-nav-tab", attrs={"settings-tab": "models"})
    ui.wait_for_test_id("settings-scene", attrs={"settings-tab": "models"}, timeout=30)


def open_session_scene(ui) -> None:
    ui.click_by_test_id("nav-session-item")
    ui.wait_for_test_id("session-scene", timeout=30)
    ui.wait_for_test_id("chat-input-container", timeout=30)


def select_chat_model(ui, model: str) -> None:
    ui.click_by_test_id("chat-model-selector-btn")
    ui.wait_for_test_id("chat-model-selector-menu")
    ui.click_by_test_id("chat-model-selector-option", attrs={"model-name": model})


def model_row_exists(ui, model: str) -> bool:
    return ui.find_by_test_id("settings-model-row", attrs={"model-name": model}) is not None


def wait_for_model_success(ui, model: str) -> None:
    row = ui.wait_for_test_id("settings-model-row", timeout=30, attrs={"model-name": model})
    assert row.visible
    if ui.find_by_test_id("settings-model-test-status", attrs={"model-name": model}) is None:
        return

    status = ui.wait_for_test_id(
        "settings-model-test-status",
        timeout=120,
        attrs={"model-name": model, "status": "success"},
    )
    assert status.visible


def wait_for_body_text(ui, text: str, timeout: float = 30.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            body_text = ui.evaluate("document.body ? document.body.innerText : ''")
            if isinstance(body_text, str) and text in body_text:
                return
        except Exception:
            pass
        time.sleep(0.5)
    raise AssertionError(f"Timed out waiting for body text: {text!r}")


def wait_for_mock_server_from_device(ui, timeout: float = 20.0) -> None:
    hdc = getattr(ui, "hdc", None)
    if hdc is None:
        return

    deadline = time.monotonic() + timeout
    last_error = ""
    while time.monotonic() < deadline:
        try:
            output = hdc.shell("curl -s http://127.0.0.1:18787/health", timeout=5)
            if '"status":"ok"' in output:
                return
            last_error = output.strip()
        except Exception as exc:  # pragma: no cover - best effort polling
            last_error = str(exc)
        time.sleep(0.5)
    raise AssertionError(f"Mock server is not reachable from OH device: {last_error}")


def wait_for_root_card_or_skip(ui, card_test_id: str, surface: str, timeout: float = 15.0):
    card = ui.find_by_test_id(card_test_id)
    if card is None:
        pytest.skip(f"Missing {surface} locators: {card_test_id}")
    return ui.wait_for_test_id(card_test_id, timeout=timeout)


def expand_card_if_collapsed(
    ui,
    card_test_id: str,
    *,
    toggle_test_id: str | None = None,
    content_test_ids: list[str] | None = None,
    timeout: float = 15.0,
) -> None:
    content_test_ids = content_test_ids or []
    card = ui.wait_for_test_id(card_test_id, timeout=timeout)
    if card.attributes.get("data-expanded") == "true":
        return

    toggle = ui.find_by_test_id(toggle_test_id) if toggle_test_id else None
    if toggle_test_id and toggle is not None:
        ui.click_by_test_id(toggle_test_id)
    else:
        ui.click_by_test_id(card_test_id)

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        refreshed = ui.find_by_test_id(card_test_id)
        if refreshed is not None and refreshed.attributes.get("data-expanded") == "true":
            return
        if content_test_ids and all(ui.find_by_test_id(test_id) is not None for test_id in content_test_ids):
            return
        time.sleep(0.2)

    raise AssertionError(f"Timed out expanding {card_test_id!r}")


def require_test_ids_or_skip(ui, test_ids: list[str], surface: str) -> None:
    missing = [
        test_id
        for test_id in test_ids
        if ui.find_by_test_id(test_id) is None
    ]
    if missing:
        pytest.skip(f"Missing {surface} locators: {', '.join(missing)}")
