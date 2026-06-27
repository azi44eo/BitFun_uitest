from __future__ import annotations

import time

from tests.test_mock_llm_oh_demo import (
    FILE_CHANGE_FINAL_TEXT,
    MOCK_MODEL_NAME,
    SHELL_COMMAND_FINAL_TEXT,
    THINKING_FINAL_TEXT,
    open_session_scene,
    select_chat_model,
)
from tests.test_system_e2e_ready import ready_mock_model, send_prompt_and_wait


def test_chat_thinking_panel_can_expand_and_collapse(ui, ready_mock_model):
    open_session_scene(ui)
    select_chat_model(ui, MOCK_MODEL_NAME)

    send_prompt_and_wait(
        ui,
        "[MOCK_SCENARIO]\nid=thinking_panel_demo\n[/MOCK_SCENARIO]",
        THINKING_FINAL_TEXT,
        timeout=120,
    )

    ui.wait_for_test_id("chat-thinking-panel", timeout=15)
    ui.wait_for_test_id("chat-thinking-toggle", timeout=15)
    ui.wait_for_test_id("chat-thinking-content", timeout=15)

    exercise_expand_collapse(ui, "chat-thinking-panel", "chat-thinking-toggle")


def test_chat_explore_group_can_expand_and_collapse(ui, ready_mock_model):
    open_session_scene(ui)
    select_chat_model(ui, MOCK_MODEL_NAME)

    send_prompt_and_wait(
        ui,
        "[MOCK_SCENARIO]\nid=shell_command_demo\n[/MOCK_SCENARIO]",
        SHELL_COMMAND_FINAL_TEXT,
        timeout=120,
    )

    ui.wait_for_test_id("chat-explore-group", timeout=15)
    ui.wait_for_test_id("chat-explore-group-toggle", timeout=15)

    exercise_expand_collapse(
        ui,
        "chat-explore-group",
        "chat-explore-group-toggle",
        expanded_content_test_id="chat-explore-group-content",
    )


def test_chat_file_change_card_can_expand_and_collapse(ui, ready_mock_model):
    open_session_scene(ui)
    select_chat_model(ui, MOCK_MODEL_NAME)

    send_prompt_and_wait(
        ui,
        "[MOCK_SCENARIO]\nid=file_change_demo\n[/MOCK_SCENARIO]",
        FILE_CHANGE_FINAL_TEXT,
        timeout=120,
    )

    ui.wait_for_test_id("chat-file-change-card", timeout=15)
    ui.wait_for_test_id("chat-file-change-toggle", timeout=15)
    ui.wait_for_test_id("chat-file-change-path", timeout=15)
    ui.wait_for_test_id("chat-file-change-action", timeout=15)

    exercise_expand_collapse(
        ui,
        "chat-file-change-card",
        "chat-file-change-toggle",
        expanded_content_test_id="chat-file-change-preview",
    )


def exercise_expand_collapse(
    ui,
    card_test_id: str,
    toggle_test_id: str,
    *,
    expanded_content_test_id: str | None = None,
    timeout: float = 15.0,
) -> None:
    set_card_expanded(ui, card_test_id, toggle_test_id, expanded=False, timeout=timeout)

    set_card_expanded(ui, card_test_id, toggle_test_id, expanded=True, timeout=timeout)
    if expanded_content_test_id:
        expanded_content = ui.wait_for_test_id(expanded_content_test_id, timeout=timeout)
        assert expanded_content.visible

    set_card_expanded(ui, card_test_id, toggle_test_id, expanded=False, timeout=timeout)


def set_card_expanded(
    ui,
    card_test_id: str,
    toggle_test_id: str,
    *,
    expanded: bool,
    timeout: float = 15.0,
) -> None:
    expected = "true" if expanded else "false"
    card = ui.wait_for_test_id(card_test_id, timeout=timeout)
    if card.attributes.get("data-expanded") == expected:
        return

    ui.click_by_test_id(toggle_test_id)
    wait_for_card_expanded(ui, card_test_id, expected=expected, timeout=timeout)


def wait_for_card_expanded(ui, card_test_id: str, *, expected: str, timeout: float) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        card = ui.find_by_test_id(card_test_id)
        if card is not None and card.attributes.get("data-expanded") == expected:
            return
        time.sleep(0.2)
    raise AssertionError(f"Timed out waiting for {card_test_id!r} data-expanded={expected!r}")
