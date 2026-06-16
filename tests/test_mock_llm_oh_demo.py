from __future__ import annotations

import os
import time

import pytest


MOCK_MODEL_NAME = "bitfun-mock"
MOCK_PROVIDER_NAME = "BitFun Mock LLM"
SIMPLE_ANSWER_TEXT = "\u8fd9\u662f BitFun Mock LLM Server \u7684\u56fa\u5b9a\u56de\u7b54\u3002"


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


def configure_mock_model_in_bitfun(ui, mock_llm_server_session) -> None:
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
        body_text = ui.evaluate("document.body.innerText")
        if isinstance(body_text, str) and text in body_text:
            return
        time.sleep(0.5)
    raise AssertionError(f"Timed out waiting for body text: {text!r}")
