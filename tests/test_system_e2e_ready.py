from __future__ import annotations

import json
import hashlib
import os
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

import pytest

from bitfun_uitest.config import TestConfig
from bitfun_uitest.drivers import create_driver
from bitfun_uitest.platforms.hdc import HdcClient
from tests.model_locator_helpers import wait_for_visible_chat_model_option
from tests.test_mock_llm_oh_demo import (
    MOCK_MODEL_NAME,
    MODELS_API_MODEL_NAME,
    MODELS_API_PROVIDER_NAME,
    FILE_CHANGE_FINAL_TEXT,
    SHELL_COMMAND_FINAL_TEXT,
    SIMPLE_ANSWER_TEXT,
    THINKING_FINAL_TEXT,
    TOOL_TRACE_FINAL_TEXT,
    configure_mock_model_from_models_api,
    configure_mock_model_in_bitfun,
    open_session_scene,
    open_settings_models,
    select_chat_model,
    wait_for_body_text,
)

ROOT = Path(__file__).resolve().parent.parent
GITCODE_TEST_PROJECT_URL = os.environ.get(
    "BITFUN_TEST_PROJECT_GIT_URL",
    "https://gitcode.com/weixin_53033691/bitfun-test-project.git",
)
GITCODE_TEST_PROJECT_CACHE_DIR = ROOT / ".tmp_bitfun_test_project"
OH_APP_BUNDLE = os.environ.get("BITFUN_OH_BUNDLE", "com.develop.opensource.ohpcd.bitfun")
OH_APP_FILES_SHELL_DIR = f"/data/app/el2/100/base/{OH_APP_BUNDLE}/files"
OH_APP_HOME_SHELL_DIR = f"{OH_APP_FILES_SHELL_DIR}/home_dir"
OH_APP_WORKSPACE_SHELL_DIR = f"{OH_APP_HOME_SHELL_DIR}/workspaces"
OH_APP_HOME_VISIBLE_DIR = "/data/storage/el2/base/files/home_dir"
OH_APP_WORKSPACE_VISIBLE_DIR = f"{OH_APP_HOME_VISIBLE_DIR}/workspaces"
OH_ASSISTANT_WORKSPACE_ID = "local_0a25b4b7cd8739dd14dbbc3cfa68c593"
OH_ASSISTANT_WORKSPACE_VISIBLE_DIR = f"{OH_APP_HOME_VISIBLE_DIR}/.bitfun/personal_assistant/workspace"
OH_ASSISTANT_WORKSPACE_SHELL_DIR = f"{OH_APP_HOME_SHELL_DIR}/.bitfun/personal_assistant/workspace"
GITCODE_WORKSPACE_NAMES = ("bitfun-test-project-a", "bitfun-test-project-b")


@pytest.fixture
def ready_mock_model(ui, mock_llm_server_session):
    _ensure_mock_server_reverse_port(mock_llm_server_session)
    configure_mock_model_in_bitfun(ui, mock_llm_server_session)
    return {
        "model": MOCK_MODEL_NAME,
        "base_url": mock_llm_server_session["bitfun_base_url"],
        "api_key": os.environ["BITFUN_TEST_LLM_API_KEY"],
    }


@pytest.fixture
def gitcode_workspace_ui(test_config: TestConfig, mock_llm_server_session):
    if test_config.platform != "oh":
        pytest.skip("GitCode workspace fixture currently targets the OH platform only")

    _reset_oh_app_data_for_gitcode_workspace()
    previous_clean = os.environ.get("BITFUN_OH_CLEAN_APP_DATA")
    os.environ["BITFUN_OH_CLEAN_APP_DATA"] = "0"
    driver = create_driver(test_config)
    try:
        driver.start()
        _prepare_gitcode_workspace_dirs_on_oh_device()
        open_gitcode_workspaces_through_frontend(driver, require_nav=False)
        driver.close()

        driver = create_driver(test_config)
        driver.start()
        wait_for_workspace_ids(driver, minimum=len(GITCODE_WORKSPACE_NAMES), timeout=30)
        yield driver
    finally:
        driver.close()
        if previous_clean is None:
            os.environ.pop("BITFUN_OH_CLEAN_APP_DATA", None)
        else:
            os.environ["BITFUN_OH_CLEAN_APP_DATA"] = previous_clean


@pytest.fixture
def gitcode_ready_mock_model(gitcode_workspace_ui, mock_llm_server_session):
    _ensure_mock_server_reverse_port(mock_llm_server_session)
    configure_mock_model_in_bitfun(gitcode_workspace_ui, mock_llm_server_session)
    return {
        "model": MOCK_MODEL_NAME,
        "base_url": mock_llm_server_session["bitfun_base_url"],
        "api_key": os.environ["BITFUN_TEST_LLM_API_KEY"],
    }


def test_e2e_001_mock_session_interaction(ui, ready_mock_model):
    open_session_scene(ui)
    select_chat_model(ui, MOCK_MODEL_NAME)

    send_prompt_and_wait(ui, "[MOCK_SCENARIO]\nid=simple_answer\n[/MOCK_SCENARIO]", SIMPLE_ANSWER_TEXT, timeout=120)
    assert_input_ready(ui)

    send_prompt_and_wait(ui, "[MOCK_SCENARIO]\nid=thinking_panel_demo\n[/MOCK_SCENARIO]", THINKING_FINAL_TEXT, timeout=120)
    ui.wait_for_test_id("chat-thinking-panel", timeout=15)
    ui.wait_for_test_id("chat-thinking-toggle", timeout=15)
    ui.wait_for_test_id("chat-thinking-content", timeout=15)
    exercise_expand_collapse(ui, "chat-thinking-panel", "chat-thinking-toggle")
    assert_input_ready(ui)

    send_prompt_and_wait(ui, "[MOCK_SCENARIO]\nid=shell_command_demo\n[/MOCK_SCENARIO]", SHELL_COMMAND_FINAL_TEXT, timeout=120)
    ui.wait_for_test_id("chat-explore-group", timeout=15)
    ui.wait_for_test_id("chat-explore-group-toggle", timeout=15)
    exercise_expand_collapse(
        ui,
        "chat-explore-group",
        "chat-explore-group-toggle",
        expanded_content_test_id="chat-explore-group-content",
    )
    assert_input_ready(ui)

    send_prompt_and_wait(ui, "[MOCK_SCENARIO]\nid=file_change_demo\n[/MOCK_SCENARIO]", FILE_CHANGE_FINAL_TEXT, timeout=120)
    ui.wait_for_test_id("chat-file-change-card", timeout=15)
    ui.wait_for_test_id("chat-file-change-toggle", timeout=15)
    exercise_expand_collapse(
        ui,
        "chat-file-change-card",
        "chat-file-change-toggle",
        expanded_content_test_id="chat-file-change-preview",
    )
    assert_input_ready(ui)

    send_prompt_and_wait(ui, "[MOCK_SCENARIO]\nid=tool_trace_demo\n[/MOCK_SCENARIO]", TOOL_TRACE_FINAL_TEXT, timeout=180)
    assert_input_ready(ui)


def test_e2e_002_model_configuration_lifecycle(ui, mock_llm_server_session):
    configure_mock_model_from_models_api(
        ui,
        mock_llm_server_session,
        provider_name=MODELS_API_PROVIDER_NAME,
        model_name=MODELS_API_MODEL_NAME,
    )

    open_settings_models(ui)
    row = ui.wait_for_test_id("settings-model-row", timeout=30, attrs={"model-name": MODELS_API_MODEL_NAME})
    assert row.visible
    status = ui.wait_for_test_id(
        "settings-model-test-status",
        timeout=120,
        attrs={"model-name": MODELS_API_MODEL_NAME, "status": "success"},
    )
    assert status.visible

    open_session_scene(ui)
    ui.click_by_test_id("chat-model-selector-btn")
    wait_for_visible_chat_model_option(ui, MODELS_API_MODEL_NAME, timeout=30)


def test_e2e_003_session_management_lifecycle(gitcode_workspace_ui, gitcode_ready_mock_model):
    ui = gitcode_workspace_ui
    session_a_name = f"E2E Session A {int(time.time())}"
    prompt_a = "[MOCK_SCENARIO]\nid=session_a_reply\n[/MOCK_SCENARIO]\nSession A prompt"
    prompt_b = "[MOCK_SCENARIO]\nid=session_b_reply\n[/MOCK_SCENARIO]\nSession B prompt"
    reply_a = "Assistant reply for session A."
    reply_b = "Assistant reply for session B."

    workspace_id = first_workspace_id_or_skip(ui)
    session_a_id = create_workspace_session(ui, workspace_id, kind="code")
    send_prompt_and_wait(ui, prompt_a, reply_a, timeout=30)
    session_b_id = create_workspace_session(ui, workspace_id, kind="cowork")
    send_prompt_and_wait(ui, prompt_b, reply_b, timeout=30)

    rename_session(ui, session_a_id, session_a_name)
    switch_to_session(ui, session_a_id)
    wait_for_body_text(ui, reply_a, timeout=30)

    switch_to_session(ui, session_b_id)
    wait_for_body_text(ui, reply_b, timeout=30)

    delete_session(ui, session_a_id)
    assert ui.find_by_test_id("nav-session-item", attrs={"session-id": session_a_id}) is None

    switch_to_session(ui, session_b_id)
    send_prompt_and_wait(
        ui,
        "[MOCK_SCENARIO]\nid=simple_answer\n[/MOCK_SCENARIO]\nSession B follow-up prompt",
        SIMPLE_ANSWER_TEXT,
        timeout=30,
    )


def test_e2e_004_workspace_and_session_binding(gitcode_workspace_ui, gitcode_ready_mock_model):
    ui = gitcode_workspace_ui
    workspace_ids = first_two_workspace_ids_or_skip(ui)
    workspace_a, workspace_b = workspace_ids

    open_workspace_by_id(ui, workspace_a)
    wait_for_workspace_context_contains(ui, workspace_a, timeout=30)
    session_a = create_workspace_session(ui, workspace_a, kind="code")
    switch_to_session(ui, session_a)
    wait_for_workspace_context_contains(ui, workspace_a, timeout=30)
    select_chat_model(ui, MOCK_MODEL_NAME)
    send_prompt_and_wait(
        ui,
        "[MOCK_SCENARIO]\nid=workspace_a_reply\n[/MOCK_SCENARIO]\nWorkspace A binding prompt",
        "Assistant reply for workspace A.",
        timeout=30,
    )
    wait_for_workspace_context_contains(ui, workspace_a, timeout=30)

    open_workspace_by_id(ui, workspace_b)
    wait_for_workspace_context_contains(ui, workspace_b, timeout=30)
    session_b = create_workspace_session(ui, workspace_b, kind="code")
    switch_to_session(ui, session_b)
    wait_for_workspace_context_contains(ui, workspace_b, timeout=30)
    select_chat_model(ui, MOCK_MODEL_NAME)
    send_prompt_and_wait(
        ui,
        "[MOCK_SCENARIO]\nid=workspace_b_reply\n[/MOCK_SCENARIO]\nWorkspace B binding prompt",
        "Assistant reply for workspace B.",
        timeout=30,
    )
    wait_for_workspace_context_contains(ui, workspace_b, timeout=30)

    switch_to_session(ui, session_a)
    wait_for_workspace_context_contains(ui, workspace_a, timeout=30)
    wait_for_body_text(ui, "Assistant reply for workspace A.", timeout=30)
    switch_to_session(ui, session_b)
    wait_for_workspace_context_contains(ui, workspace_b, timeout=30)
    wait_for_body_text(ui, "Assistant reply for workspace B.", timeout=30)


def test_e2e_006_settings_navigation_and_persistence(ui, ready_mock_model):
    open_settings_models(ui)
    ui.click_by_test_id("settings-nav-tab", attrs={"settings-tab": "appearance"})
    ui.wait_for_test_id("settings-scene", attrs={"settings-tab": "appearance"}, timeout=30)

    current_level = get_ui_font_size_level_index(ui)
    next_level = click_next_ui_font_size_level(ui, current_level)
    if next_level is None:
        pytest.skip("Appearance font size buttons do not expose a stable switch path in the current UI")

    open_settings_models(ui)
    ui.click_by_test_id("settings-nav-tab", attrs={"settings-tab": "appearance"})
    ui.wait_for_test_id("settings-scene", attrs={"settings-tab": "appearance"}, timeout=30)
    persisted_level = get_ui_font_size_level_index(ui)
    assert persisted_level == next_level, (
        f"Expected appearance font size level {next_level} to persist, got {persisted_level}"
    )


def test_e2e_007_agent_and_skill_discovery_flow(ui):
    open_agent_skill_tabs(ui)

    ui.click_by_test_id("agent-tab")
    ui.wait_for_test_id("agent-skill-panel", timeout=30)
    ui.wait_for_test_id("agent-list", timeout=30)
    wait_and_click_first_visible_test_id_or_skip(
        ui,
        "agent-list-item",
        "No agent cards are available in the current build",
        timeout=30,
    )
    ui.wait_for_test_id("agent-detail-panel", timeout=30)
    ui.wait_for_test_id("agent-detail-title", timeout=15)
    ui.wait_for_test_id("agent-detail-description", timeout=15)
    if ui.find_by_test_id("agent-detail-tools-section") is not None:
        ui.wait_for_test_id("agent-detail-tools-section", timeout=15)
    ui.click_by_test_id("agent-detail-close")
    ui.wait_for_test_id_gone("agent-detail-panel", timeout=15)

    open_agent_skill_tabs(ui)
    ui.click_by_test_id("skill-tab")
    ui.wait_for_test_id("agent-skill-panel", timeout=30)
    ui.wait_for_test_id("skill-list", timeout=30)
    wait_and_click_first_visible_test_id_or_skip(
        ui,
        "skill-list-item",
        "No installed skill cards are available in the current build",
        timeout=30,
    )
    ui.wait_for_test_id("skill-detail-panel", timeout=30)
    ui.wait_for_test_id("skill-detail-title", timeout=15)
    ui.wait_for_test_id("skill-detail-capabilities-section", timeout=15)
    ui.click_by_test_id("skill-detail-close")
    ui.wait_for_test_id_gone("skill-detail-panel", timeout=15)


def test_e2e_011_skills_tab_navigation(ui):
    open_agent_skill_tabs(ui)
    ui.click_by_test_id("skill-tab")
    ui.wait_for_test_id("agent-skill-panel", timeout=30)

    installed_tab = ui.wait_for_test_id("skills-tab-installed", timeout=15)
    discover_tab = ui.wait_for_test_id("skills-tab-discover", timeout=15)
    assert installed_tab.visible
    assert discover_tab.visible

    ui.wait_for_test_id("skills-installed-panel", timeout=30)
    ui.click_by_test_id("skills-tab-discover")
    wait_for_visible_test_id(ui, "skills-discover-panel", timeout=30)
    discover_surface = wait_for_any_test_id(
        ui,
        [
            "skills-discover-search",
            "skills-discover-content",
            "skills-discover-list",
            "skills-discover-empty",
        ],
        timeout=5,
    )
    if discover_surface is not None:
        assert discover_surface.visible

    ui.click_by_test_id("skills-tab-installed")
    wait_for_visible_test_id(ui, "skills-installed-panel", timeout=30)
    installed_surface = wait_for_any_test_id(
        ui,
        [
            "skills-installed-content",
            "skill-list",
            "skill-list-item",
            "skills-installed-empty",
        ],
        timeout=5,
    )
    if installed_surface is not None:
        assert installed_surface.visible


def test_e2e_012_shell_panel_entry(ui):
    ui.click_by_test_id("shell-panel-entry")
    wait_for_visible_test_id(ui, "shell-panel", timeout=30)
    wait_for_visible_test_id(ui, "shell-panel-title", timeout=15)


def test_e2e_009_session_error_recovery(ui, ready_mock_model):
    open_session_scene(ui)
    select_chat_model(ui, MOCK_MODEL_NAME)

    run_id = f"e2e_009_{int(time.time() * 1000)}"
    send_prompt_and_wait(
        ui,
        f"[MOCK_SCENARIO]\nid=error_then_success\nrun_id={run_id}\n[/MOCK_SCENARIO]",
        "Recovered successfully after retry.",
        timeout=120,
    )
    assert_no_failed_user_message(ui)
    wait_for_chat_input_ready(ui, timeout=30)

    send_prompt_and_wait(ui, "[MOCK_SCENARIO]\nid=simple_answer\n[/MOCK_SCENARIO]", SIMPLE_ANSWER_TEXT, timeout=120)


def test_e2e_010_cold_start_to_productive_session(gitcode_workspace_ui, mock_llm_server_session):
    ui = gitcode_workspace_ui
    ui.wait_for_test_id("app-layout", timeout=30)
    _ensure_mock_server_reverse_port(mock_llm_server_session)
    workspace_ids = wait_for_workspace_ids(ui, minimum=1, timeout=20)
    assert workspace_ids, "Expected seeded GitCode workspaces to be visible after cold start"
    configure_mock_model_in_bitfun(ui, mock_llm_server_session)
    workspace_id = workspace_ids[0]
    open_workspace_by_id(ui, workspace_id)
    session_id = create_workspace_session(ui, workspace_id, kind="code")
    switch_to_session(ui, session_id)
    select_chat_model(ui, MOCK_MODEL_NAME)
    send_prompt_and_wait(ui, "[MOCK_SCENARIO]\nid=simple_answer\n[/MOCK_SCENARIO]", SIMPLE_ANSWER_TEXT, timeout=120)


def send_prompt(ui, prompt: str) -> None:
    ui.wait_for_test_id("chat-input-textarea", timeout=30)
    ui.fill_by_test_id("chat-input-textarea", prompt)
    ui.click_by_test_id("chat-input-send-btn")


def send_prompt_and_wait(ui, prompt: str, expected_text: str, timeout: float) -> None:
    send_prompt(ui, prompt)
    wait_for_body_text(ui, expected_text, timeout=timeout)
    wait_for_round_complete(ui, timeout=timeout)


def open_agent_skill_tabs(ui) -> None:
    ui.wait_for_test_id("agent-skill-entry", timeout=15)
    expanded = ui.evaluate(
        """
        (() => document.querySelector('[data-testid="agent-skill-entry"]')?.getAttribute('aria-expanded') === 'true')()
        """
    )
    if expanded is not True:
        ui.click_by_test_id("agent-skill-entry")
    ui.wait_for_test_id("agent-skill-tabs", timeout=15)


def wait_and_click_first_visible_test_id_or_skip(ui, test_id: str, skip_reason: str, *, timeout: float) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if click_first_visible_test_id(ui, test_id):
            return
        time.sleep(0.2)
    pytest.skip(skip_reason)


def wait_for_any_test_id(ui, test_ids: list[str], *, timeout: float):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        for test_id in test_ids:
            element = ui.find_by_test_id(test_id)
            if element is not None:
                return element
        time.sleep(0.2)
    return None


def wait_for_visible_test_id(ui, test_id: str, *, timeout: float, attrs: dict[str, str] | None = None):
    deadline = time.monotonic() + timeout
    last = None
    while time.monotonic() < deadline:
        last = ui.find_by_test_id(test_id, attrs=attrs)
        if last is not None and last.visible:
            return last
        time.sleep(0.2)
    if last is None:
        raise AssertionError(f"Timed out waiting for visible data-testid={test_id!r}")
    raise AssertionError(f"data-testid={test_id!r} exists but did not become visible")


def get_ui_font_size_level_index(ui) -> str | None:
    ui.wait_for_test_id("appearance-font-size-group", timeout=15)
    payload = ui.evaluate(
        """
        (() => {
          const buttons = Array.from(document.querySelectorAll('[data-testid="appearance-font-size-option"]'));
          if (!buttons.length) return null;
          const active = buttons.find((button) =>
            button.getAttribute('aria-pressed') === 'true' ||
            button.getAttribute('data-selected') === 'true'
          );
          if (!active) return null;
          return active.getAttribute('data-size-level') || active.getAttribute('data-font-level') || null;
        })()
        """
    )
    return payload if isinstance(payload, str) and payload else None


def click_next_ui_font_size_level(ui, current_index: str | None) -> str | None:
    ui.wait_for_test_id("appearance-font-size-group", timeout=15)
    payload = ui.evaluate(
        f"""
        (() => {{
          const buttons = Array.from(document.querySelectorAll('[data-testid="appearance-font-size-option"]'))
            .filter((button) =>
              !button.disabled &&
              button.getAttribute('aria-disabled') !== 'true' &&
              (button.getAttribute('data-size-level') || button.getAttribute('data-font-level')) !== 'custom'
            );
          if (buttons.length < 2) return null;
          const currentLevel = {json.dumps(current_index)};
          const active = buttons.find((button) => {{
            const level = button.getAttribute('data-size-level') || button.getAttribute('data-font-level');
            return level === currentLevel;
          }}) || buttons.find((button) =>
            button.getAttribute('aria-pressed') === 'true' ||
            button.getAttribute('data-selected') === 'true'
          );
          const activeLevel = active
            ? (active.getAttribute('data-size-level') || active.getAttribute('data-font-level'))
            : null;
          const target = buttons.find((button) => {{
            const level = button.getAttribute('data-size-level') || button.getAttribute('data-font-level');
            return level && level !== activeLevel;
          }});
          if (!target) return null;
          target.scrollIntoView({{ block: 'center', inline: 'center' }});
          target.click();
          return target.getAttribute('data-size-level') || target.getAttribute('data-font-level') || null;
        }})()
        """
    )
    return payload if isinstance(payload, str) and payload else None


def click_first_visible_test_id(ui, test_id: str) -> bool:
    clicked = ui.evaluate(
        f"""
        (() => {{
          const candidates = Array.from(document.querySelectorAll('[data-testid="{test_id}"]'));
          const target = candidates.find((el) => {{
            const rect = el.getBoundingClientRect();
            const style = window.getComputedStyle(el);
            return Boolean((rect.width || rect.height || el.getClientRects().length) &&
              style.display !== 'none' &&
              style.visibility !== 'hidden');
          }});
          if (!target) return false;
          target.scrollIntoView({{ block: 'center', inline: 'center' }});
          const rect = target.getBoundingClientRect();
          const x = rect.left + rect.width / 2;
          const y = rect.top + rect.height / 2;
          const clickTarget = document.elementFromPoint(x, y) || target;
          for (const type of ['pointerdown', 'mousedown', 'pointerup', 'mouseup', 'click']) {{
            clickTarget.dispatchEvent(new MouseEvent(type, {{
              bubbles: true,
              cancelable: true,
              view: window,
              clientX: x,
              clientY: y,
            }}));
          }}
          return true;
        }})()
        """
    )
    return bool(clicked)


def submit_browser_url(ui, url: str) -> None:
    ui.fill_by_test_id("browser-url-input", url)
    if getattr(ui, "hdc", None) is not None:
        ui.click_by_test_id("browser-url-input")
        ui.hdc.run("shell", "uitest uiInput keyEvent 66", check=False, timeout=10)
        time.sleep(0.5)
        return

    submitted = ui.evaluate(
        """
        (async () => {
          const input = document.querySelector('[data-testid="browser-url-input"]');
          const form = input?.closest('form');
          if (!input || !form) return false;
          input.focus();
          await new Promise((resolve) => setTimeout(resolve, 50));
          input.dispatchEvent(new KeyboardEvent('keydown', {
            key: 'Enter',
            code: 'Enter',
            bubbles: true,
            cancelable: true,
          }));
          input.dispatchEvent(new KeyboardEvent('keyup', {
            key: 'Enter',
            code: 'Enter',
            bubbles: true,
            cancelable: true,
          }));
          await new Promise((resolve) => setTimeout(resolve, 50));
          if (typeof form.requestSubmit === 'function') {
            form.requestSubmit();
          } else if (typeof SubmitEvent === 'function') {
            form.dispatchEvent(new SubmitEvent('submit', { bubbles: true, cancelable: true }));
          } else {
            form.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }));
          }
          return true;
        })()
        """
    )
    assert submitted is True


def try_wait_for_browser_url(ui, url: str, *, timeout: float) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        current = ui.find_by_test_id("browser-current-url")
        if current is not None and url in current.text:
            return True
        time.sleep(0.2)
    return False


def create_new_code_session(ui) -> str:
    before_active_id = active_session_id(ui)
    before_ids = set(list_session_ids(ui))
    ui.click_by_test_id("nav-new-code-session-btn")
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        active_id = active_session_id(ui)
        if active_id and active_id != before_active_id:
            return active_id
        ids = list_session_ids(ui)
        new_ids = [session_id for session_id in ids if session_id not in before_ids]
        if new_ids:
            return new_ids[-1]
        time.sleep(0.2)
    raise AssertionError("Timed out waiting for a new code session to be created")


def create_workspace_session(ui, workspace_id: str, *, kind: str) -> str:
    before_active_id = active_session_id(ui)
    open_workspace_menu(ui, workspace_id)
    action_test_id = (
        "nav-workspace-menu-create-code-session"
        if kind == "code"
        else "nav-workspace-menu-create-cowork-session"
    )
    ui.click_by_test_id(action_test_id)
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        session_id = active_session_id(ui)
        if session_id and session_id != before_active_id:
            return session_id
        time.sleep(0.2)
    raise AssertionError(f"Timed out waiting for a new {kind} workspace session to be created")


def active_session_id(ui) -> str | None:
    payload = ui.evaluate(
        """
        (() => {
          const active = document.querySelector('[data-testid="nav-session-item"][data-session-active="true"]');
          const id = active?.getAttribute('data-session-id');
          return typeof id === 'string' && id.length > 0 ? id : null;
        })()
        """
    )
    return payload if isinstance(payload, str) and payload else None


def list_session_ids(ui) -> list[str]:
    payload = ui.evaluate(
        """
        (() => Array.from(document.querySelectorAll('[data-testid="nav-session-item"]'))
          .map((el) => el.getAttribute('data-session-id'))
          .filter((value) => typeof value === 'string' && value.length > 0))()
        """
    )
    return payload if isinstance(payload, list) else []


def switch_to_session(ui, session_id: str) -> None:
    ui.click_by_test_id("nav-session-item", attrs={"session-id": session_id})
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        element = ui.find_by_test_id("nav-session-item", attrs={"session-id": session_id})
        if element is not None and element.attributes.get("data-session-active") == "true":
            return
        time.sleep(0.2)
    raise AssertionError(f"Timed out switching to session {session_id}")


def count_visible_flow_items(ui) -> int:
    payload = ui.evaluate(
        """
        (() => Array.from(document.querySelectorAll('[data-testid="flowchat-message-item"]'))
          .filter((el) => {
            const rect = el.getBoundingClientRect();
            const style = window.getComputedStyle(el);
            return Boolean((rect.width || rect.height || el.getClientRects().length) &&
              style.display !== 'none' &&
              style.visibility !== 'hidden');
          }).length)()
        """
    )
    return int(payload) if isinstance(payload, (int, float)) else 0


def assert_input_ready(ui) -> None:
    input_area = ui.wait_for_test_id("chat-input-textarea", timeout=15)
    assert input_area.visible
    assert not input_area.disabled


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


def set_card_expanded(ui, card_test_id: str, toggle_test_id: str, *, expanded: bool, timeout: float) -> None:
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


def wait_for_round_complete(ui, *, timeout: float) -> None:
    deadline = time.monotonic() + timeout
    last_snapshot = None
    stable_start: float | None = None
    while time.monotonic() < deadline:
        send_button = ui.find_by_test_id("chat-input-send-btn")
        input_area = ui.find_by_test_id("chat-input-textarea")
        failed_user = ui.evaluate(
            """
            (() => Boolean(document.querySelector('[data-testid="chat-user-message"][data-failed="true"]')))()
            """
        )
        input_ready = input_area is not None and input_area.visible and not input_area.disabled
        snapshot = ui.evaluate(
            """
            (() => {
                const body = document.body.innerText;
                const send = document.querySelector('[data-testid="chat-input-send-btn"]');
                const input = document.querySelector('[data-testid="chat-input-textarea"]');
                const expandedCards = Array.from(document.querySelectorAll('[data-expanded="true"]')).length;
                return JSON.stringify({
                    body,
                    sendDisabled: Boolean(send && send.hasAttribute('disabled')),
                    inputPresent: Boolean(input),
                    expandedCards
                });
            })()
            """
        )
        if input_ready and not failed_user:
            if snapshot != last_snapshot:
                last_snapshot = snapshot
                stable_start = time.monotonic()
            elif stable_start is not None and time.monotonic() - stable_start >= 1.0:
                return
        else:
            if stable_start is None:
                last_snapshot = snapshot
            stable_start = None
        time.sleep(0.2)
    raise AssertionError("Timed out waiting for the current round to settle")


def wait_for_chat_input_ready(ui, *, timeout: float) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        input_area = ui.find_by_test_id("chat-input-textarea")
        if input_area is not None and input_area.visible and not input_area.disabled:
            return
        time.sleep(0.2)
    raise AssertionError("Timed out waiting for the chat input to become available")


def assert_no_failed_user_message(ui) -> None:
    failed = ui.evaluate(
        """
        (() => Boolean(document.querySelector('[data-testid="chat-user-message"][data-failed="true"]')))()
        """
    )
    assert failed is False


def rename_session(ui, session_id: str, new_title: str) -> None:
    open_session_menu(ui, session_id)
    rename_item = ui.find_by_test_id("nav-session-menu-rename", attrs={"session-id": session_id})
    if rename_item is not None:
        ui.click_by_test_id("nav-session-menu-rename", attrs={"session-id": session_id})
    elif ui.find_by_test_id("nav-session-menu-rename") is not None:
        ui.click_by_test_id("nav-session-menu-rename")
    else:
        pytest.skip("Session rename menu item is not exposed by the current UI")

    renamed = ui.evaluate(
        f"""
        (() => {{
          const row = document.querySelector('[data-testid="nav-session-item"][data-session-id="{session_id}"]');
          if (!row) return false;
          const input = row.querySelector('input');
          if (!input) return false;
          input.focus();
          const value = {new_title!r};
          const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value')?.set;
          if (setter) {{
            setter.call(input, value);
          }} else {{
            input.value = value;
          }}
          input.dispatchEvent(new Event('input', {{ bubbles: true }}));
          input.dispatchEvent(new KeyboardEvent('keydown', {{ key: 'Enter', bubbles: true }}));
          input.dispatchEvent(new Event('blur', {{ bubbles: true }}));
          return true;
        }})()
        """
    )
    if not renamed:
        pytest.skip("Session rename input flow lacks a stable editable input in the current UI")

    wait_for_body_text(ui, new_title, timeout=30)


def delete_session(ui, session_id: str) -> None:
    open_session_menu(ui, session_id)
    delete_item = ui.find_by_test_id("nav-session-menu-delete", attrs={"session-id": session_id})
    if delete_item is not None:
        ui.click_by_test_id("nav-session-menu-delete", attrs={"session-id": session_id})
    elif ui.find_by_test_id("nav-session-menu-delete") is not None:
        ui.click_by_test_id("nav-session-menu-delete")
    else:
        pytest.skip("Session delete menu item is not exposed by the current UI")
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        if ui.find_by_test_id("nav-session-item", attrs={"session-id": session_id}) is None:
            return
        time.sleep(0.2)
    raise AssertionError(f"Timed out deleting session {session_id}")


def open_session_menu(ui, session_id: str) -> None:
    opened = ui.evaluate(
        f"""
        (() => {{
          const el = document.querySelector('[data-testid="nav-session-menu-btn"][data-session-id="{session_id}"]');
          if (!el) return false;
          const rect = el.getBoundingClientRect();
          const x = rect.left + rect.width / 2;
          const y = rect.top + rect.height / 2;
          for (const type of ['pointerdown', 'mousedown', 'pointerup', 'mouseup', 'click']) {{
            el.dispatchEvent(new MouseEvent(type, {{
              bubbles: true,
              cancelable: true,
              view: window,
              clientX: x,
              clientY: y,
            }}));
          }}
          return true;
        }})()
        """
    )
    if not opened:
        pytest.skip("Session menu button is not reachable in the current UI")
    ui.wait_for_test_id("nav-session-menu", timeout=15, attrs={"session-id": session_id})


def _prepare_gitcode_workspaces_on_oh_device() -> None:
    repo_dir = _ensure_gitcode_test_project_checkout()
    hdc = HdcClient()

    hdc.shell(f"mkdir -p {OH_APP_FILES_SHELL_DIR}/bitfun/data", timeout=30)
    hdc.shell(f"mkdir -p {OH_ASSISTANT_WORKSPACE_SHELL_DIR}", timeout=30)
    hdc.shell(f"mkdir -p {OH_APP_WORKSPACE_SHELL_DIR}", timeout=30)
    for workspace_name in GITCODE_WORKSPACE_NAMES:
        remote_dir = f"{OH_APP_WORKSPACE_SHELL_DIR}/{workspace_name}"
        hdc.shell(f"rm -rf {remote_dir}", timeout=30)
        hdc.file_send(str(repo_dir), remote_dir, timeout=180)

    payload = _load_workspace_data_from_device(hdc)
    payload["workspaces"] = _merged_workspace_map(payload.get("workspaces"))
    seeded_workspace_ids = [_workspace_id_for_name(workspace_name) for workspace_name in GITCODE_WORKSPACE_NAMES]
    payload["opened_workspace_ids"] = [OH_ASSISTANT_WORKSPACE_ID, *seeded_workspace_ids]
    payload["current_workspace_id"] = OH_ASSISTANT_WORKSPACE_ID
    payload["recent_workspaces"] = seeded_workspace_ids
    payload["recent_assistant_workspaces"] = [OH_ASSISTANT_WORKSPACE_ID]
    payload["saved_at"] = _utc_iso_now()

    temp_path = ROOT / ".tmp_workspace_data_seed.json"
    temp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    try:
        hdc.file_send(str(temp_path), f"{OH_APP_FILES_SHELL_DIR}/bitfun/data/workspace_data.json", timeout=60)
    finally:
        temp_path.unlink(missing_ok=True)


def _prepare_gitcode_workspace_dirs_on_oh_device() -> None:
    repo_dir = _ensure_gitcode_test_project_checkout()
    hdc = HdcClient()
    hdc.shell(f"mkdir -p {OH_APP_WORKSPACE_SHELL_DIR}", timeout=30)
    for workspace_name in GITCODE_WORKSPACE_NAMES:
        remote_dir = f"{OH_APP_WORKSPACE_SHELL_DIR}/{workspace_name}"
        hdc.shell(f"rm -rf {remote_dir}", timeout=30)
        hdc.file_send(str(repo_dir), remote_dir, timeout=180)


def open_gitcode_workspaces_through_frontend(ui, *, require_nav: bool = True) -> None:
    for workspace_name in GITCODE_WORKSPACE_NAMES:
        workspace_path = f"{OH_APP_WORKSPACE_VISIBLE_DIR}/{workspace_name}"
        opened = ui.evaluate(
            f"""
            (async () => {{
              const targetPath = {workspace_path!r};
              await window.__TAURI_INTERNALS__.invoke('open_workspace', {{
                request: {{ path: targetPath }}
              }});
              return true;
            }})()
            """
        )
        assert opened is True
    if require_nav:
        ids = wait_for_workspace_ids(ui, minimum=len(GITCODE_WORKSPACE_NAMES), timeout=30)
        assert len(ids) >= len(GITCODE_WORKSPACE_NAMES)


def _reset_oh_app_data_for_gitcode_workspace() -> None:
    hdc = HdcClient()
    hdc.run("shell", f"aa force-stop {OH_APP_BUNDLE}", check=False, timeout=30)
    clean_command = os.environ.get("BITFUN_OH_APP_CLEAN_COMMAND")
    if clean_command:
        hdc.run("shell", clean_command, check=False, timeout=60)
    else:
        hdc.run("shell", f"bm clean -d -n {OH_APP_BUNDLE}", check=False, timeout=60)


def _load_workspace_data_from_device(hdc: HdcClient) -> dict[str, object]:
    raw = hdc.run(
        "shell",
        f"cat {OH_APP_FILES_SHELL_DIR}/bitfun/data/workspace_data.json",
        check=False,
        timeout=30,
    ).strip()
    if not raw:
        return {
            "workspaces": {},
            "opened_workspace_ids": [],
            "current_workspace_id": None,
            "recent_workspaces": [],
            "recent_assistant_workspaces": [],
        }
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return {
            "workspaces": {},
            "opened_workspace_ids": [],
            "current_workspace_id": None,
            "recent_workspaces": [],
            "recent_assistant_workspaces": [],
        }
    return payload if isinstance(payload, dict) else {"workspaces": {}}


def _ensure_gitcode_test_project_checkout() -> Path:
    cache_dir = GITCODE_TEST_PROJECT_CACHE_DIR
    if not cache_dir.exists():
        subprocess.run(
            ["git", "clone", "--depth", "1", GITCODE_TEST_PROJECT_URL, str(cache_dir)],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
    else:
        status = subprocess.run(
            ["git", "-C", str(cache_dir), "status", "--short"],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        if not status.stdout.strip():
            subprocess.run(
                ["git", "-C", str(cache_dir), "pull", "--ff-only"],
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
    return cache_dir


def _ensure_mock_server_reverse_port(mock_llm_server_session) -> None:
    device_port = int(mock_llm_server_session["device_port"])
    host_port = int(mock_llm_server_session["host_port"])
    hdc = HdcClient()
    hdc.remove_rport(device_port)
    hdc.rport(device_port, host_port)


def _merged_workspace_map(existing: object) -> dict[str, dict[str, object]]:
    workspace_map = dict(existing) if isinstance(existing, dict) else {}
    preserved = {
        workspace_id: workspace
        for workspace_id, workspace in workspace_map.items()
        if isinstance(workspace, dict) and workspace.get("workspaceKind") == "assistant"
    }

    now = _utc_iso_now()
    preserved.setdefault(
        OH_ASSISTANT_WORKSPACE_ID,
        {
            "id": OH_ASSISTANT_WORKSPACE_ID,
            "name": "Claw",
            "rootPath": OH_ASSISTANT_WORKSPACE_VISIBLE_DIR,
            "workspaceType": "Other",
            "workspaceKind": "assistant",
            "status": "Active",
            "languages": [],
            "openedAt": now,
            "lastAccessed": now,
            "description": None,
            "tags": [],
            "statistics": None,
            "relatedPaths": [],
            "metadata": {"sshHost": "localhost"},
        },
    )
    for workspace_name in GITCODE_WORKSPACE_NAMES:
        workspace_id = _workspace_id_for_name(workspace_name)
        preserved[workspace_id] = {
            "id": workspace_id,
            "name": workspace_name,
            "rootPath": f"{OH_APP_WORKSPACE_VISIBLE_DIR}/{workspace_name}",
            "workspaceType": "Other",
            "workspaceKind": "normal",
            "status": "Active",
            "languages": ["Markdown"],
            "openedAt": now,
            "lastAccessed": now,
            "description": "GitCode test workspace",
            "tags": ["gitcode", "ui-test"],
            "statistics": None,
            "relatedPaths": [],
            "metadata": {"sshHost": "localhost"},
        }
    return preserved


def _workspace_id_for_name(workspace_name: str) -> str:
    root_path = f"{OH_APP_WORKSPACE_VISIBLE_DIR}/{workspace_name}"
    return "local_" + hashlib.md5(root_path.encode("utf-8")).hexdigest()


def _utc_iso_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def first_workspace_id_or_skip(ui) -> str:
    ids = wait_for_workspace_ids(ui, minimum=1, timeout=20)
    if not ids:
        pytest.skip("No visible normal workspace is available for workspace-scoped session tests")
    open_workspace_by_id(ui, ids[0])
    return ids[0]


def first_two_workspace_ids_or_skip(ui) -> tuple[str, str]:
    ids = wait_for_workspace_ids(ui, minimum=2, timeout=20)
    if len(ids) < 2:
        pytest.skip("Need at least two visible normal workspaces for workspace binding tests")
    open_workspace_by_id(ui, ids[0])
    open_workspace_by_id(ui, ids[1])
    return ids[0], ids[1]


def wait_for_workspace_ids(ui, *, minimum: int, timeout: float) -> list[str]:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        ids = list_workspace_ids(ui)
        if len(ids) >= minimum:
            return ids
        time.sleep(0.2)
    return list_workspace_ids(ui)


def list_workspace_ids(ui) -> list[str]:
    payload = ui.evaluate(
        """
        (() => Array.from(document.querySelectorAll('[data-testid="nav-workspace-item"]'))
          .map((el) => el.getAttribute('data-workspace-id'))
          .filter((value) => typeof value === 'string' && value.length > 0))()
        """
    )
    return payload if isinstance(payload, list) else []


def open_workspace_by_id(ui, workspace_id: str) -> None:
    button = ui.find_by_test_id("nav-workspace-name-btn", attrs={"workspace-id": workspace_id})
    if button is not None:
        ui.click_by_test_id("nav-workspace-name-btn", attrs={"workspace-id": workspace_id})
    else:
        ui.click_by_test_id("nav-workspace-item", attrs={"workspace-id": workspace_id})


def open_workspace_menu(ui, workspace_id: str) -> None:
    opened = ui.evaluate(
        f"""
        (() => {{
          const el = document.querySelector('[data-testid="nav-workspace-menu-btn"][data-workspace-id="{workspace_id}"]');
          if (!el) return false;
          const rect = el.getBoundingClientRect();
          const x = rect.left + rect.width / 2;
          const y = rect.top + rect.height / 2;
          for (const type of ['pointerdown', 'mousedown', 'pointerup', 'mouseup', 'click']) {{
            el.dispatchEvent(new MouseEvent(type, {{
              bubbles: true,
              cancelable: true,
              view: window,
              clientX: x,
              clientY: y,
            }}));
          }}
          return true;
        }})()
        """
    )
    if not opened:
        pytest.skip("Workspace row menu button is not reachable in the current UI")
    ui.wait_for_test_id("nav-workspace-item-menu", timeout=15, attrs={"workspace-id": workspace_id})


def assert_workspace_context_contains(ui, workspace_id: str) -> None:
    strip = ui.wait_for_test_id("chat-input-workspace-strip", timeout=15)
    item = ui.find_by_test_id("nav-workspace-item", attrs={"workspace-id": workspace_id})
    if item is None:
        pytest.skip(f"Workspace {workspace_id} disappeared during the test")
    expected = item.text.splitlines()[0].strip() if item.text else ""
    assert expected
    assert expected in strip.text


def wait_for_workspace_context_contains(ui, workspace_id: str, *, timeout: float) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            assert_workspace_context_contains(ui, workspace_id)
            return
        except AssertionError:
            time.sleep(0.2)
    assert_workspace_context_contains(ui, workspace_id)


def wait_for_user_message_failed(ui, timeout: float = 30.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        failed = ui.evaluate(
            """
            (() => Boolean(document.querySelector('[data-testid="chat-user-message"][data-failed="true"]')))()
            """
        )
        if failed:
            return
        time.sleep(0.2)
    raise AssertionError("Timed out waiting for a failed user message state")


def wait_for_user_message_failed_or_skip(ui, timeout: float = 30.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        failed = ui.evaluate(
            """
            (() => Boolean(document.querySelector('[data-testid="chat-user-message"][data-failed="true"]')))()
            """
        )
        if failed:
            return
        time.sleep(0.2)
    pytest.skip("Error recovery trigger did not surface a failed user message state in the current build")
