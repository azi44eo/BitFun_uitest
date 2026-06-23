[中文](system-e2e-cases-CN.md) | **English**

# BitFun System E2E Cases

This document defines 10 end-to-end system test cases in an automation-ready
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

- Continue filling session artifact locators as each UI block becomes testable.

### Preconditions

1. BitFun launches successfully on the target device.
2. A mock model is already configured and selectable in the session model selector.
3. The mock server exposes these scenarios:
   `simple_answer`, `thinking_panel_demo`, `tool_trace_demo`,
   `shell_command_demo`, `file_change_demo`, `miniapp_demo`.
4. Required session locators already exist:
   `session-scene`, `chat-input-textarea`, `chat-input-send-btn`,
   `chat-model-selector-btn`, `chat-model-selector-option`,
   `chat-assistant-message-content`.

### Execution Steps

1. Open the session scene.
2. Select the mock model.
3. Send the `simple_answer` prompt and wait for the final response.
4. Send the `thinking_panel_demo` prompt and verify the thinking panel flow.
5. Send the `tool_trace_demo` prompt and verify the tool trace flow.
6. Send the `shell_command_demo` prompt and verify the shell result flow.
7. Send the `file_change_demo` prompt and verify the file change flow.
8. Send the `miniapp_demo` prompt and verify the miniapp result flow.

### Expected Results

1. Every prompt transitions from pending to completed without hanging.
2. The correct assistant response appears after each scenario.
3. Thinking, tool trace, shell result, file change, and miniapp artifacts render
   in the same conversation in the expected order.
4. Expanding one artifact does not break the rest of the session UI.

## E2E-002 Model Configuration Lifecycle

Status:

`Ready`

Missing items:

- None blocking for the core create/edit/save/use flow.

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
2. Create a new provider config with a unique provider name.
3. Fetch remote models from the backend and select one remote model.
4. Add one custom model name if the flow supports it.
5. Save the configuration.
6. Wait for connection test success.
7. Reopen the saved config and update one editable field, such as provider name.
8. Save again and verify the updated value persists.
9. Return to the session scene and confirm the saved model is selectable.

### Expected Results

1. The provider config is created successfully.
2. Remote model discovery returns selectable options.
3. Save succeeds and the config appears in the model list.
4. Connection test status becomes success.
5. Edited values persist after reopening.
6. The saved model can be selected in chat.

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

`Need Test Mechanism`

Missing items:

- Two stable test workspace fixtures or documented fixture paths.
- A deterministic setup/reset rule for workspace A and workspace B.
- Confirmation that workspace-scoped session creation locators are complete.

### Preconditions

1. Two isolated test workspaces are available or can be created.
2. A usable model exists for sending messages.
3. Required locators already exist:
   `nav-workspace-item`, `nav-workspace-name-btn`,
   `nav-workspace-session-region`, `nav-session-item`,
   `chat-input-workspace-strip`.

### Execution Steps

1. Open workspace A and create session A1.
2. Send a unique message in session A1.
3. Open workspace B and create session B1.
4. Send a different unique message in session B1.
5. Verify the nav tree shows A1 under workspace A and B1 under workspace B.
6. Reopen A1 and verify the workspace strip shows workspace A.
7. Reopen B1 and verify the workspace strip shows workspace B.

### Expected Results

1. Sessions stay attached to the correct workspace.
2. The nav tree and session UI agree on the current workspace context.
3. Switching workspaces does not mix session histories.

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

`Need Test Mechanism`

Missing items:

- Two specific saveable settings to standardize across runs.
- A restore rule for returning changed settings to their original values.
- Locator confirmation for the chosen save controls.

### Preconditions

1. Settings can be opened from the footer menu.
2. At least two saveable settings are available across different tabs.
3. Required locators already exist:
   `settings-scene`, `settings-nav`, `settings-nav-tab`,
   plus save controls for the selected tabs.

### Execution Steps

1. Open Settings.
2. Change one value in Basics.
3. Switch to another tab, such as Editor or Keyboard, and change one value there.
4. Save both changes.
5. Close Settings.
6. Reopen Settings and revisit both tabs.
7. Verify both values persist.

### Expected Results

1. Cross-tab navigation is stable.
2. Saving succeeds without losing unrelated settings.
3. Reopening Settings shows the updated values.

## E2E-007 Agent And Skill Discovery Flow

Status:

`Need Locators`

Missing items:

- Stable locators for the chosen agent card and primary agent action.
- Stable locators for the chosen skill card and primary skill action.
- A deterministic choice of which agent/skill the test will target.

### Preconditions

1. Agents and Skills navigation entries are visible.
2. At least one agent card and one skill card are available.
3. Required locators already exist for both scenes and their primary cards/actions.

### Execution Steps

1. Open the Agents scene.
2. Verify at least one agent card is visible.
3. Open one non-destructive agent action, such as details or configure.
4. Return to navigation and open the Skills scene.
5. Switch between Installed and Discover.
6. Verify at least one skill card is visible.
7. Trigger one non-destructive skill action, such as details or reveal path.

### Expected Results

1. Agents and Skills scenes both load correctly.
2. Cards are visible and actionable.
3. Non-destructive actions complete without breaking navigation.

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

`Need Test Mechanism`

Missing items:

- One deterministic failure trigger.
- One deterministic recovery path.
- A clear product-supported retry/resend interaction path.
- Locator confirmation for failed message and retry controls.

### Preconditions

1. A deterministic failure mode is available, such as an invalid model config or
   a mock scenario that forces an error.
2. A recovery mode is also available, such as restoring a valid model config.
3. Required locators already exist:
   `chat-user-message`, `chat-user-message-content`,
   and any retry / resend controls used by the product.

### Execution Steps

1. Trigger a request failure from a session.
2. Wait for the failed state to appear in the conversation.
3. Verify the input area remains usable.
4. Restore the backend or model to a valid state.
5. Retry using the product-supported recovery path.
6. Wait for a successful assistant response.
7. Send one additional normal message.

### Expected Results

1. The failed state is clearly visible in the UI.
2. The session remains recoverable.
3. Retrying after recovery succeeds.
4. The conversation continues normally afterward.

## E2E-010 End-To-End Bootstrap To Productive Session

Status:

`Need Test Mechanism`

Missing items:

- A repeatable clean-state reset procedure.
- An isolated workspace/model fixture for first-run setup.
- Confirmation of which first-run locators are stable enough for automation.

### Preconditions

1. The app starts from a clean or isolated first-run state.
2. A test workspace path is available.
3. A deterministic test model backend is available.
4. Required locators already exist for the welcome scene, workspace flow, model
   config flow, and session flow.

### Execution Steps

1. Launch BitFun from a clean state.
2. Complete the minimum first-run flow to open or create a workspace.
3. Complete the minimum model configuration flow.
4. Create the first usable session.
5. Select the configured model.
6. Send the first user prompt.
7. Wait for a successful assistant response.
8. Reopen the app or trigger a state refresh and confirm the created data remains.

### Expected Results

1. The user can get from startup to a productive first session.
2. Workspace, model, and session setup all complete successfully.
3. The first AI response arrives successfully.
4. The created state persists across reopen or refresh.
