[中文](mock-session-ui-cases-CN.md) | **English**

# BitFun Mock Session UI Cases

These cases focus on session-scene UI rendering and interaction after BitFun
receives deterministic mock LLM responses. The goal is to verify visible,
interactive conversation artifacts such as thinking panels, tool calls, shell
commands, file changes, and mini apps.

All cases assume:

1. BitFun is started on the target platform.
2. A mock model is already configured and selectable in the session scene.
3. The test sends a prompt containing a `[MOCK_SCENARIO]` block.

## Shared Base Flow

Steps:

1. Open the session scene.
2. Select the expected mock model.
3. Fill the chat input.
4. Click send.
5. Wait for the expected artifact or final response.

Shared locators:

| Element name | data-testid | Notes |
|---|---|---|
| Session scene root | `session-scene` | Session-scoped content root. |
| Chat input container | `chat-input-container` | Composer root. |
| Chat input editable region | `chat-input-textarea` | Real editable node. |
| Chat send button | `chat-input-send-btn` | Send action. |
| Chat model selector button | `chat-model-selector-btn` | Opens model menu. |
| Chat model selector menu | `chat-model-selector-menu` | Dropdown root. |
| Chat model selector option | `chat-model-selector-option` | Pair with `data-model-name`. |
| FlowChat messages region | `flowchat-messages` | Conversation host. |
| FlowChat message item | `flowchat-message-item` | Pair with `data-item-type`, `data-turn-id`. |
| User message | `chat-user-message` | Pair with `data-status`, `data-failed`. |
| User message content | `chat-user-message-content` | User prompt text. |
| Assistant message | `chat-assistant-message` | Pair with `data-status`, `data-streaming`. |
| Assistant message content | `chat-assistant-message-content` | Final assistant text. |

## TC-MOCK-001 Simple Answer

Scenario id:

`simple_answer`

Purpose:

- Verify the basic send/receive flow.
- Verify that a normal assistant response renders successfully.

Mock JSON shape:

```json
{
  "scenario_id": "simple_answer",
  "mode": "chat_completions",
  "stream": false,
  "turns": [
    {
      "assistant": {
        "thinking": ["Recognize simple_answer scenario", "Return deterministic text"],
        "final_text": "This is the fixed response from the BitFun Mock LLM Server."
      }
    }
  ]
}
```

UI assertions:

- A user message appears with `data-status != error`.
- An assistant message appears.
- `chat-assistant-message-content` contains the fixed response text.

Required additional locators:

| Element name | data-testid | Notes |
|---|---|---|
| Assistant message | `chat-assistant-message` | Pair with `data-status`, `data-streaming`. |
| Assistant message content | `chat-assistant-message-content` | Final rendered answer. |

## TC-MOCK-002 Thinking Panel

Scenario id:

`thinking_panel_demo`

Purpose:

- Verify that reasoning/thinking content appears in session UI.
- Verify that the thinking section can be expanded or collapsed if BitFun
  renders it behind a toggle.

Mock JSON shape:

```json
{
  "scenario_id": "thinking_panel_demo",
  "mode": "chat_completions",
  "stream": true,
  "turns": [
    {
      "assistant": {
        "thinking": [
          "Inspect the task and identify the main goal.",
          "Plan the response before answering."
        ],
        "final_text": "Here is the final answer after reasoning.",
        "stream_chunks": [
          "Here is the final answer ",
          "after reasoning."
        ]
      }
    }
  ]
}
```

UI assertions:

- A visible thinking entry or panel appears.
- Thinking text is rendered.
- If BitFun uses a toggle, expand/collapse works.
- Final assistant text still renders normally.

Required additional locators:

| Element name | data-testid | Notes |
|---|---|---|
| Thinking panel root | `chat-thinking-panel` | Root for reasoning display. |
| Thinking toggle | `chat-thinking-toggle` | Expand/collapse control when present. |
| Thinking content | `chat-thinking-content` | Rendered reasoning text. |

## TC-MOCK-003 Tool Call Trace

Scenario id:

`tool_trace_demo`

Purpose:

- Verify that BitFun renders tool calls.
- Verify that BitFun can continue from a first response with `tool_calls` to a
  second final assistant response.

Mock JSON shape:

```json
{
  "scenario_id": "tool_trace_demo",
  "mode": "chat_completions",
  "stream": true,
  "turns": [
    {
      "assistant": {
        "thinking": [
          "Inspect the workspace before answering.",
          "Call BitFun tools to read the README and check git status."
        ],
        "tool_calls": [
          {
            "id": "call_readme",
            "name": "read_file",
            "arguments": {
              "path": "README.md"
            }
          },
          {
            "id": "call_git_status",
            "name": "exec_command",
            "arguments": {
              "command": "git status --short"
            }
          }
        ],
        "final_text": ""
      }
    },
    {
      "assistant": {
        "thinking": [
          "The requested BitFun tools have completed.",
          "Return a deterministic final answer for the demo test."
        ],
        "final_text": "Mock tool calls completed through BitFun tools."
      }
    }
  ]
}
```

UI assertions:

- Tool call cards appear.
- Tool names are correct.
- Tool arguments are viewable.
- Final assistant response appears after the tool phase.

Required additional locators:

| Element name | data-testid | Notes |
|---|---|---|
| Tool call group | `chat-tool-call-group` | Container for tool calls in one round. |
| Tool call item | `chat-tool-call-item` | Pair with `data-tool-name`, `data-tool-call-id`. |
| Tool call arguments | `chat-tool-call-arguments` | Expanded parameter payload. |
| Tool call toggle | `chat-tool-call-toggle` | Expand/collapse control when present. |

## TC-MOCK-004 Shell Command Result

Scenario id:

`shell_command_demo`

Purpose:

- Verify that shell command execution records are rendered in the conversation.
- Verify command/output/exit-code presentation.

Mock JSON shape:

```json
{
  "scenario_id": "shell_command_demo",
  "mode": "chat_completions",
  "stream": false,
  "turns": [
    {
      "assistant": {
        "thinking": ["Run a deterministic shell command result block."],
        "shell_commands": [
          {
            "command": "git status --short",
            "output": "M README.md",
            "exit_code": 0
          }
        ],
        "final_text": "Rendered one shell command result."
      }
    }
  ]
}
```

UI assertions:

- A shell-command card appears.
- Command text matches.
- Output text matches.
- Exit code is visible and marked as success.
- If a toggle exists, command details can be expanded.

Required additional locators:

| Element name | data-testid | Notes |
|---|---|---|
| Shell command card | `chat-shell-command-card` | Repeated item. |
| Shell command text | `chat-shell-command-text` | Actual command string. |
| Shell command output | `chat-shell-command-output` | Captured stdout/stderr. |
| Shell command exit code | `chat-shell-command-exit-code` | Pair with `data-exit-code`, `data-status`. |
| Shell command toggle | `chat-shell-command-toggle` | Expand/collapse details. |

## TC-MOCK-005 File Changes

Scenario id:

`file_change_demo`

Purpose:

- Verify that file-change artifacts render correctly.
- Verify file path, action type, and content preview interaction.

Mock JSON shape:

```json
{
  "scenario_id": "file_change_demo",
  "mode": "chat_completions",
  "stream": false,
  "turns": [
    {
      "assistant": {
        "thinking": ["Create a deterministic file-change result."],
        "file_changes": [
          {
            "path": "src/App.tsx",
            "action": "modify",
            "content": "export default function App() { return <main>Hello</main>; }"
          }
        ],
        "final_text": "Rendered one file change result."
      }
    }
  ]
}
```

UI assertions:

- A file-change card appears.
- File path is correct.
- Action type is correct.
- Preview/details can be opened.
- File content preview contains the expected snippet.

Required additional locators:

| Element name | data-testid | Notes |
|---|---|---|
| File change card | `chat-file-change-card` | Repeated item. |
| File change path | `chat-file-change-path` | File path label. |
| File change action | `chat-file-change-action` | Pair with `data-action`. |
| File change preview | `chat-file-change-preview` | Code/text preview. |
| File change toggle | `chat-file-change-toggle` | Expand/collapse details. |

## TC-MOCK-006 Mini App Result

Scenario id:

`miniapp_demo`

Purpose:

- Verify that BitFun renders mini app generation results.
- Verify that the user can open or inspect the generated mini app artifact.

Mock JSON shape:

```json
{
  "scenario_id": "miniapp_demo",
  "mode": "chat_completions",
  "stream": false,
  "turns": [
    {
      "assistant": {
        "thinking": ["Prepare a deterministic mini app result."],
        "miniapp": {
          "title": "BitFun Mock Mini App",
          "files": [
            {
              "path": "src/App.tsx",
              "content": "export default function App() { return <main>BitFun Mock Mini App</main>; }"
            }
          ]
        },
        "final_text": "Rendered one mini app result."
      }
    }
  ]
}
```

UI assertions:

- A mini app result card appears.
- Mini app title is visible.
- File list is visible.
- Open/preview action works if BitFun exposes one.

Required additional locators:

| Element name | data-testid | Notes |
|---|---|---|
| Mini app card | `chat-miniapp-card` | Root card for one generated mini app. |
| Mini app title | `chat-miniapp-title` | Title label. |
| Mini app file list | `chat-miniapp-file-list` | Container for files. |
| Mini app file row | `chat-miniapp-file-row` | Pair with `data-path`. |
| Mini app open button | `chat-miniapp-open-btn` | Opens preview or detail view. |

## Implementation Priority

Recommended delivery order:

1. `simple_answer`
2. `thinking_panel_demo`
3. `tool_trace_demo`
4. `shell_command_demo`
5. `file_change_demo`
6. `miniapp_demo`

This order keeps the early cases closest to the core session experience while
allowing richer artifact tests to layer on top later.

## Current Locator Gaps

Based on the current BitFun web UI source search, the following session-artifact
locators are likely still missing and should be added before the corresponding
demo tests can assert real UI controls instead of skipping:

| Area | Likely missing data-testid |
|---|---|
| Thinking panel | `chat-thinking-panel`, `chat-thinking-toggle`, `chat-thinking-content` |
| Tool call trace | `chat-tool-call-group`, `chat-tool-call-item`, `chat-tool-call-arguments`, `chat-tool-call-toggle` |
| Shell command result | `chat-shell-command-card`, `chat-shell-command-text`, `chat-shell-command-output`, `chat-shell-command-exit-code`, `chat-shell-command-toggle` |
| File change result | `chat-file-change-card`, `chat-file-change-path`, `chat-file-change-action`, `chat-file-change-preview`, `chat-file-change-toggle` |
| Mini app result | `chat-miniapp-card`, `chat-miniapp-title`, `chat-miniapp-file-list`, `chat-miniapp-file-row`, `chat-miniapp-open-btn` |
