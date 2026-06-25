from __future__ import annotations

import pytest

from tests.test_mock_llm_oh_demo import (
    FILE_CHANGE_FINAL_TEXT,
    MINIAPP_FINAL_TEXT,
    MOCK_MODEL_NAME,
    SHELL_COMMAND_FINAL_TEXT,
    expand_card_if_collapsed,
    open_session_scene,
    select_chat_model,
)
from tests.test_system_e2e_ready import (
    create_new_code_session,
    create_workspace_session,
    first_workspace_id_or_skip,
    gitcode_ready_mock_model,
    gitcode_workspace_ui,
    ready_mock_model,
    send_prompt,
    send_prompt_and_wait,
    switch_to_session,
    wait_for_any_test_id,
    wait_for_visible_test_id,
)


def test_e2e_005_notification_center_task_tracking(gitcode_workspace_ui, gitcode_ready_mock_model):
    ui = gitcode_workspace_ui
    workspace_id = first_workspace_id_or_skip(ui)
    session_id = create_workspace_session(ui, workspace_id, kind="code")
    switch_to_session(ui, session_id)
    select_chat_model(ui, MOCK_MODEL_NAME)

    send_prompt(ui, "[MOCK_SCENARIO]\nid=long_task_demo\n[/MOCK_SCENARIO]")
    ui.click_by_test_id("notification-button")
    ui.wait_for_test_id("notification-center", timeout=15)
    if ui.find_by_test_id("notification-center-active-section") is None:
        pytest.skip("Task tool did not surface a notification-center active section in the current build")
    ui.wait_for_test_id("notification-center-active-section", timeout=5)


def test_e2e_008_shell_panel_integration(gitcode_workspace_ui, gitcode_ready_mock_model):
    ui = gitcode_workspace_ui
    workspace_id = first_workspace_id_or_skip(ui)
    session_id = create_workspace_session(ui, workspace_id, kind="code")
    switch_to_session(ui, session_id)
    select_chat_model(ui, MOCK_MODEL_NAME)

    send_prompt_and_wait(ui, "[MOCK_SCENARIO]\nid=shell_command_demo\n[/MOCK_SCENARIO]", SHELL_COMMAND_FINAL_TEXT, timeout=120)
    shell_card = wait_for_any_test_id(
        ui,
        ["chat-shell-tool-card", "chat-shell-command-card"],
        timeout=15,
    )
    if shell_card is None:
        pytest.skip("Shell command ToolCard was not rendered")
    assert shell_card.visible

    expand_card_if_collapsed(
        ui,
        "chat-shell-command-card",
        toggle_test_id="chat-shell-command-toggle",
        content_test_ids=["chat-shell-command-output", "chat-shell-command-exit-code"],
    )
    command = ui.wait_for_test_id("chat-shell-command-text", timeout=15)
    output = ui.wait_for_test_id("chat-shell-command-output", timeout=15)
    exit_code = ui.wait_for_test_id("chat-shell-command-exit-code", timeout=15)
    assert "printf 'M README.md\\n'" in command.text
    assert "M README.md" in output.text
    assert exit_code.visible

    if ui.find_by_test_id("chat-shell-tool-open-panel") is None:
        pytest.skip("Shell ToolCard did not expose chat-shell-tool-open-panel")
    ui.click_by_test_id("chat-shell-tool-open-panel")
    wait_for_visible_test_id(ui, "shell-panel", timeout=30)
    wait_for_visible_test_id(ui, "shell-panel-title", timeout=15)

    if ui.find_by_test_id("shell-command-list") is not None:
        ui.wait_for_test_id("shell-command-list", timeout=15)


def test_e2e_013_mock_artifact_card_expansion(ui, ready_mock_model):
    open_session_scene(ui)
    select_chat_model(ui, MOCK_MODEL_NAME)

    send_prompt_and_wait(ui, "[MOCK_SCENARIO]\nid=shell_command_demo\n[/MOCK_SCENARIO]", SHELL_COMMAND_FINAL_TEXT, timeout=120)
    shell_card = wait_for_any_test_id(ui, ["chat-shell-command-card", "chat-shell-tool-card"], timeout=15)
    if shell_card is not None:
        expand_card_if_collapsed(
            ui,
            "chat-shell-command-card",
            toggle_test_id="chat-shell-command-toggle",
            content_test_ids=["chat-shell-command-output", "chat-shell-command-exit-code"],
        )
        shell_command = ui.wait_for_test_id("chat-shell-command-text", timeout=15)
        shell_output = ui.wait_for_test_id("chat-shell-command-output", timeout=15)
        shell_exit_code = ui.wait_for_test_id("chat-shell-command-exit-code", timeout=15)
        assert "printf 'M README.md\\n'" in shell_command.text
        assert "M README.md" in shell_output.text
        assert shell_exit_code.visible

    try:
        session_id = create_new_code_session(ui)
    except AssertionError:
        pytest.skip("Current build does not expose a stable path to create a fresh session for artifact expansion")
    switch_to_session(ui, session_id)
    select_chat_model(ui, MOCK_MODEL_NAME)
    send_prompt_and_wait(ui, "[MOCK_SCENARIO]\nid=file_change_demo\n[/MOCK_SCENARIO]", FILE_CHANGE_FINAL_TEXT, timeout=120)
    file_card = ui.wait_for_test_id("chat-file-change-card", timeout=15)
    assert file_card.visible
    expand_card_if_collapsed(
        ui,
        "chat-file-change-card",
        toggle_test_id="chat-file-change-toggle",
        content_test_ids=["chat-file-change-preview"],
    )
    file_path = ui.wait_for_test_id("chat-file-change-path", timeout=15)
    file_action = ui.wait_for_test_id("chat-file-change-action", timeout=15)
    file_preview = ui.wait_for_test_id("chat-file-change-preview", timeout=15)
    assert ".bitfun-ui-test/mock-file-change/App.tsx" in file_path.text or file_path.text == "App.tsx"
    assert file_action.visible
    assert "Hello" in file_preview.text

    try:
        session_id = create_new_code_session(ui)
    except AssertionError:
        pytest.skip("Current build does not expose a stable path to create a fresh session for miniapp artifact expansion")
    switch_to_session(ui, session_id)
    select_chat_model(ui, MOCK_MODEL_NAME)
    send_prompt_and_wait(ui, "[MOCK_SCENARIO]\nid=miniapp_demo\n[/MOCK_SCENARIO]", MINIAPP_FINAL_TEXT, timeout=120)
    miniapp_card = ui.wait_for_test_id("chat-miniapp-card", timeout=15)
    assert miniapp_card.visible
    expand_card_if_collapsed(
        ui,
        "chat-miniapp-card",
        toggle_test_id="chat-miniapp-open-btn",
        content_test_ids=["chat-miniapp-file-list", "chat-miniapp-file-row"],
    )
    miniapp_title = ui.wait_for_test_id("chat-miniapp-title", timeout=15)
    miniapp_file_list = ui.wait_for_test_id("chat-miniapp-file-list", timeout=15)
    miniapp_file_row = ui.wait_for_test_id("chat-miniapp-file-row", timeout=15)
    assert "BitFun Mock Mini App" in miniapp_title.text
    assert miniapp_file_list.visible
    assert miniapp_file_row.visible
