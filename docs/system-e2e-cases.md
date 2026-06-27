[中文](system-e2e-cases-CN.md) | **English**

# BitFun System E2E Cases

This document defines 13 end-to-end system test cases in an automation-ready
format. Each case is scoped so it can be implemented with deterministic test
data, stable locators, and clear cleanup expectations.

## Conventions

- Use unique test prefixes for created entities, for example
  `E2E-Model-<timestamp>`, `E2E-Session-A`, `E2E-Workspace-A`.
- Prefer deterministic mock scenarios when possible.
- If a case modifies persistent settings or creates data, either restore the
  original value in the same case or use an isolated test namespace.
- If a required locator is missing, treat that as a test implementation blocker,
  not a product pass.

## Readiness Labels

- `Ready`: Can be implemented now with current test data and interaction patterns.
- `Need Locators`: Business flow is clear, but stable UI locators are still missing.
- `Need Test Mechanism`: The flow still lacks a deterministic trigger, reset path,
  or isolated test fixture, so automation would be unstable even if locators exist.

## E2E-001 Mock Session Interaction

Status:

`Ready`

Missing items:

- None blocking for the current ready coverage.

### Preconditions

1. BitFun launches successfully on the target device.
2. A mock model is already configured and selectable in the session model selector.
3. The mock server exposes these scenarios:
   `simple_answer`, `thinking_panel_demo`, `shell_command_demo`,
   `file_change_demo`, and `tool_trace_demo`.
4. Required session locators already exist:
   `session-scene`, `chat-input-textarea`, `chat-input-send-btn`,
   `chat-model-selector-btn`, `chat-model-selector-option`,
   `chat-thinking-panel`, `chat-thinking-toggle`, `chat-thinking-content`,
   `chat-explore-group`, `chat-explore-group-toggle`,
   `chat-file-change-card`, `chat-file-change-toggle`,
   `chat-file-change-preview`.

### Execution Steps

1. Open the session scene.
2. Select the mock model.
3. Send the `simple_answer` prompt and wait for the final response.
4. Send the `thinking_panel_demo` prompt and verify the thinking panel can be expanded and collapsed.
5. Send the `shell_command_demo` prompt and verify the explore/tool group can be expanded and collapsed.
6. Send the `file_change_demo` prompt and verify the file change card can be expanded and collapsed.
7. Send the `tool_trace_demo` prompt and verify the session still completes normally afterward.

### Expected Results

1. Every prompt transitions from pending to completed without hanging.
2. The correct assistant response appears after each scenario.
3. The thinking panel, explore group, and file change card all render and support basic expand/collapse interaction.
4. The input becomes usable again after each round and the later rounds are not blocked by earlier artifacts.

## E2E-002 Model Configuration Lifecycle

Status:

`Ready`

Missing items:

- None blocking for the current ready flow.

### Preconditions

1. The Settings entry is reachable from the footer menu.
2. A test model backend is available and responds to:
   `/models`, `/chat/completions`, and connection test requests.
3. Required locators already exist:
   `settings-nav-tab`, `settings-model-create-first-config-btn`,
   `settings-model-provider-name-input`, `settings-model-api-key-input`,
   `settings-model-base-url-input`, `settings-model-select-btn`,
   `settings-model-option`, `settings-model-save-btn`,
   `settings-model-row`, `settings-model-test-status`,
   `chat-model-selector-btn`, `chat-model-selector-option`.

### Execution Steps

1. Open Settings and switch to the Models tab.
2. Create a new provider config backed by the mock server `/models` endpoint.
3. Fetch remote models from the backend and select the deterministic mock model option.
4. Save the configuration.
5. Wait for connection test success.
6. Return to the session scene and confirm the saved model is selectable.

### Expected Results

1. The provider config is created successfully.
2. Remote model discovery returns selectable options.
3. Save succeeds and the config appears in the model list.
4. Connection test status becomes success.
5. The saved model can be selected in chat.

## E2E-003 Session Management Lifecycle

Status:

`Ready`

Missing items:

- None blocking for core create/rename/switch/delete coverage.

### Preconditions

1. At least one usable workspace exists.
2. At least one usable model exists for sending messages.
3. Required locators already exist:
   `nav-session-item`, `nav-session-menu-btn`, `nav-session-menu`,
   `nav-session-menu-rename`, `nav-session-menu-delete`,
   `chat-input-textarea`, `chat-input-send-btn`.

### Execution Steps

1. Create session A and send a unique message.
2. Create session B and send a different unique message.
3. Rename session A using the session menu.
4. Switch from session B back to session A and verify the message history.
5. Switch back to session B and verify its different history.
6. Delete session A.
7. Verify session B remains usable and can still send a message.

### Expected Results

1. Sessions A and B are created independently.
2. Session rename persists in the nav list.
3. Switching sessions restores the correct history.
4. Deleting session A removes it from the list.
5. Deleting one session does not damage the remaining session.

## E2E-004 Workspace And Session Binding

Status:

`Ready`

Missing items:

- None blocking for the current workspace fixture path.

### Preconditions

1. Two deterministic GitCode-backed test workspaces are prepared by the fixture.
2. A usable model exists for sending messages.
3. Required locators already exist:
   `nav-workspace-item`, `nav-workspace-name-btn`,
   `nav-workspace-menu-btn`, `nav-workspace-menu-create-code-session`,
   `nav-session-item`,
   `chat-input-workspace-strip`.

### Execution Steps

1. Open workspace A and explicitly wait until the workspace strip reflects workspace A.
2. Create a code session under workspace A.
3. Select the mock model and send the `workspace_a_reply` prompt.
4. Open workspace B and explicitly wait until the workspace strip reflects workspace B.
5. Create a code session under workspace B.
6. Select the mock model and send the `workspace_b_reply` prompt.
7. Switch back to the session under workspace A and verify both the workspace strip and assistant reply.
8. Switch back to the session under workspace B and verify both the workspace strip and assistant reply.

### Expected Results

1. Sessions stay attached to the correct workspace.
2. The workspace strip reflects the expected workspace before and after session switching.
3. Switching between the two sessions restores the correct assistant reply without crossing workspace context.

## E2E-005 Notification Center Task Tracking

Status:

`Need Test Mechanism`

Missing items:

- A deterministic long-running task trigger.
- A stable way to know when the task is "running" versus "completed".
- Confirmation that task-related notification locators are complete.

### Preconditions

1. A deterministic long-running scenario or workflow exists.
2. Required locators already exist:
   `notification-button`, `notification-center`,
   `notification-center-active-section`.
3. The chosen action is known to create a background task entry.

### Execution Steps

1. Trigger the long-running action from a session or supported entry point.
2. Observe the notification button state change.
3. Open the notification center.
4. Verify the task appears in the active section while running.
5. Wait for the task to complete.
6. Verify the notification entry updates or disappears according to product behavior.
7. Close the notification center.

### Expected Results

1. The notification button reflects active work.
2. The notification center shows the background task while it is running.
3. The task state updates correctly when the work completes.
4. Opening and closing the notification center does not interrupt the task.

## E2E-006 Settings Navigation And Persistence

Status:

`Ready`

Missing items:

- None blocking for the current ready coverage.

### Preconditions

1. Settings can be opened from the footer menu.
2. The Appearance tab exposes deterministic font size preset controls.
3. Required locators already exist:
   `settings-scene`, `settings-nav`, `settings-nav-tab`,
   `appearance-font-size-group`, `appearance-font-size-option`.

### Execution Steps

1. Open Settings and switch to the Appearance tab.
2. Read the currently selected UI font size level.
3. Click a different non-custom font size preset.
4. Re-open the Models tab and then return to the Appearance tab.
5. Read the selected font size level again.
6. Verify that the selected level persisted.

### Expected Results

1. Navigation from Models to Appearance and back is stable.
2. A different font size preset can be selected through stable appearance locators.
3. Re-entering the Appearance tab shows the updated preset still selected.

## E2E-007 Agent And Skill Discovery Flow

Status:

`Ready`

Missing items:

- None blocking for the current detail-panel flow.

### Preconditions

1. Agents and Skills navigation entries are visible.
2. At least one visible agent card and one visible installed skill card are available.
3. Required locators already exist for both scenes, list items, detail panels, and close actions.

### Execution Steps

1. Open the Agents scene.
2. Verify at least one agent card is visible.
3. Open one visible agent card and verify the agent detail panel.
4. Close the agent detail panel.
5. Open the Skills scene.
6. Open one visible installed skill card and verify the skill detail panel.
7. Close the skill detail panel.

### Expected Results

1. Agents and Skills scenes both load correctly.
2. One agent detail panel and one skill detail panel can be opened and closed.
3. Opening and closing these non-destructive panels does not break scene navigation.

## E2E-008 Shell And Browser Panel Integration

Status:

`Need Locators`

Missing items:

- Stable locators for shell panel mounted state.
- Stable locators for browser panel mounted state.
- A clear, non-fragile assertion anchor for "panel opened successfully".

### Preconditions

1. Footer shell and browser entry points are available.
2. A session with visible history already exists.
3. Required locators already exist for shell open/close and browser open/close flows.

### Execution Steps

1. Open a session and confirm an existing conversation is visible.
2. Open the shell panel from the footer.
3. Verify the shell panel mounts successfully.
4. Switch to the browser panel from the footer.
5. Verify the browser panel mounts successfully.
6. Return to the original session scene.
7. Send one more chat message.

### Expected Results

1. Shell and browser panels both open correctly.
2. Switching panels does not reset the session.
3. The original session remains interactive after returning.

## E2E-009 Error Recovery In Session UI

Status:

`Ready`

Missing items:

- None blocking for the current ready recovery path.

### Preconditions

1. The mock server exposes the deterministic `error_then_success` scenario.
2. A mock model is already configured and selectable.
3. Required locators already exist for the normal session input flow.

### Execution Steps

1. Trigger `error_then_success` with a unique `run_id`.
2. Wait for the scenario to recover and return the final successful assistant response.
3. Verify no failed user message marker remains in the conversation.
4. Verify the input becomes usable again.
5. Send one additional normal `simple_answer` prompt.

### Expected Results

1. The scenario completes with its deterministic recovery response.
2. The session does not remain stuck in a failed-message state.
3. The chat input becomes usable again after recovery.
4. The conversation continues normally afterward.

## E2E-010 End-To-End Bootstrap To Productive Session

Status:

`Ready`

Missing items:

- None blocking for the current fixture-driven bootstrap flow.

### Preconditions

1. The app starts from a clean state with the GitCode test workspace fixture prepared.
2. A deterministic test model backend is available.
3. Required locators already exist for workspace selection, model configuration,
   session creation, and chat input flow.

### Execution Steps

1. Launch BitFun from a clean state with fixture workspaces available.
2. Configure the mock model.
3. Open the first prepared workspace.
4. Create the first usable code session.
5. Select the configured model.
6. Send the first `simple_answer` prompt.
7. Wait for the successful assistant response.

### Expected Results

1. The app can move from a clean launch to a productive first code session.
2. Workspace, model, and session setup all complete successfully.
3. The first AI response arrives successfully.

## E2E-011 Skills Tab Navigation

Status:

`Ready`

Missing items:

- None blocking for installed/discover tab switching coverage.

### Preconditions

1. The Agents/Skills navigation entry is visible.
2. The Skills scene can be opened from the shared Agents/Skills entry.
3. Required locators already exist:
   `agent-skill-entry`, `skill-tab`, `agent-skill-panel`,
   `skills-tab-installed`, `skills-tab-discover`,
   `skills-installed-panel`,
   `skills-discover-panel`,
   and at least one stable installed/discover content surface.

### Execution Steps

1. Open the shared Agents/Skills navigation group.
2. Enter the Skills scene from the `skill-tab`.
3. Verify the Installed tab is present and the installed panel is rendered.
4. Switch to the Discover tab.
5. Verify the discover panel is rendered and that at least one discover surface is visible, such as search, content, list, or empty state.
6. Switch back to the Installed tab.
7. Verify the installed panel is rendered again and that at least one installed surface is visible, such as content, list, item, or empty state.

### Expected Results

1. The Skills scene opens successfully from the shared navigation entry.
2. Installed and Discover tabs are both visible and clickable.
3. Switching tabs updates the rendered main panel correctly.
4. Returning to Installed restores a valid installed surface without breaking the scene.

## E2E-012 Shell Panel Entry

Status:

`Ready`

Missing items:

- None blocking for basic shell panel entry coverage.

### Preconditions

1. The footer shell entry is visible in the current app shell.
2. Required locators already exist:
   `shell-panel-entry`, `shell-panel`, `shell-panel-title`.

### Execution Steps

1. Click the footer shell entry.
2. Wait for the shell panel to become visible.
3. Verify the shell panel title is visible.

### Expected Results

1. The shell entry opens the shell panel successfully.
2. The shell panel becomes visible instead of staying hidden in the DOM only.
3. The shell panel header/title renders correctly after opening.

## E2E-013 Mock Artifact Card Expansion

Status:

`Ready`

Missing items:

- None blocking for implementing card expansion assertions.
- Product-side rendering issues should fail this case instead of being treated as locator blockers.

### Preconditions

1. A mock model is already configured and selectable in the session scene.
2. The mock server exposes:
   `shell_command_demo`, `file_change_demo`, and `miniapp_demo`.
3. Required locators already exist:
   `chat-shell-command-card`, `chat-shell-command-toggle`,
   `chat-shell-command-text`, `chat-shell-command-output`,
   `chat-shell-command-exit-code`,
   `chat-file-change-card`, `chat-file-change-toggle`,
   `chat-file-change-path`, `chat-file-change-action`,
   `chat-file-change-preview`,
   `chat-miniapp-card`, `chat-miniapp-title`,
   `chat-miniapp-file-list`, `chat-miniapp-file-row`.

### Execution Steps

1. Open the session scene and select the mock model.
2. Send the `shell_command_demo` prompt.
3. Wait for the shell result card, expand it, and verify command text, output, and exit code.
4. Send the `file_change_demo` prompt.
5. Wait for the file change card, expand it, and verify file path, action, and preview.
6. Send the `miniapp_demo` prompt.
7. Wait for the miniapp card, expand it, and verify title, file list, and file row.

### Expected Results

1. Each artifact card is rendered in the conversation after its corresponding mock scenario finishes.
2. Expanding a collapsed card reveals the expected detail region instead of leaving it hidden.
3. Shell command output, file preview content, and miniapp file list all render correctly after expansion.
4. If any artifact card fails to render or expand, the case fails instead of silently skipping.
