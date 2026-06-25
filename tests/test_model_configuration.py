from __future__ import annotations

import time

import pytest

from tests.model_locator_helpers import (
    click_settings_model_option,
    wait_for_saved_model_row,
    wait_for_saved_model_status,
    wait_for_visible_chat_model_option,
)


OPENBITFUN_MODELS = ("deepseek-v4-pro", "glm-5.1")


@pytest.fixture
def openbitfun_api_key(test_config) -> str:
    api_key = test_config.get_local_string("models", "openbitfun", "api_key")
    if api_key is None:
        pytest.skip("Missing models.openbitfun.api_key in local-config.json")
    return api_key


def test_openbitfun_models_are_visible_after_configuration(openbitfun_api_key, ui):
    open_settings_models(ui)
    configure_openbitfun_models_if_needed(ui, openbitfun_api_key)
    assert_saved_models_succeeded(ui)
    assert_models_visible_in_claw_selector(ui)


def open_settings_models(ui) -> None:
    ui.click_by_test_id("nav-footer-more-btn")
    ui.wait_for_test_id("nav-footer-menu")
    ui.click_by_test_id("nav-footer-settings-item")
    ui.wait_for_test_id("settings-scene")
    ui.wait_for_test_id("settings-nav")

    ui.wait_for_test_id("settings-nav-tab", attrs={"settings-tab": "models"})
    ui.click_by_test_id("settings-nav-tab", attrs={"settings-tab": "models"})
    settings = ui.wait_for_test_id("settings-scene", attrs={"settings-tab": "models"})
    assert settings.visible


def configure_openbitfun_models_if_needed(ui, api_key: str) -> None:
    if not needs_initial_model_configuration(ui):
        return

    ui.click_by_test_id("settings-model-create-first-config-btn")
    ui.click_by_test_id("settings-model-provider-option", attrs={"provider-id": "openbitfun"})
    ui.fill_by_test_id("settings-model-api-key-input", api_key)
    ui.click_by_test_id("settings-model-select-btn")

    for model in OPENBITFUN_MODELS:
        click_settings_model_option(ui, model, timeout=90)

    ui.click_by_test_id("settings-model-save-btn")


def needs_initial_model_configuration(ui, timeout: float = 20.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if all(
            ui.find_by_test_id("settings-model-row", attrs={"model-name": model}) is not None
            for model in OPENBITFUN_MODELS
        ):
            return False
        if ui.find_by_test_id("settings-model-create-first-config-btn") is not None:
            return True
        time.sleep(0.2)

    raise AssertionError("Timed out waiting for settings model list or first-config action")


def assert_saved_models_succeeded(ui) -> None:
    ui.wait_for_test_id("settings-model-list", timeout=20)
    for model in OPENBITFUN_MODELS:
        wait_for_saved_model_row(ui, model, timeout=30)
        wait_for_saved_model_status(ui, model, status="success", timeout=120)


def assert_models_visible_in_claw_selector(ui) -> None:
    ui.click_by_test_id("nav-session-item")
    ui.wait_for_test_id("session-scene")
    ui.wait_for_test_id("chat-input-container")
    ui.click_by_test_id("chat-model-selector-btn")

    ui.wait_for_test_id("chat-model-selector-menu")

    for model in OPENBITFUN_MODELS:
        wait_for_visible_chat_model_option(ui, model, timeout=30)
