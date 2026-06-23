[English](mock-session-ui-cases.md) | **中文**

# BitFun Mock 会话界面测试场景

这些场景聚焦于：BitFun 在接收可预测的 mock LLM 响应后，会话场景中的 UI
渲染和交互是否正确。目标是验证会话中可见、可交互的内容，例如思考过程、
工具调用、Shell 命令、文件修改和 Mini App。

所有场景都默认满足以下前提：

1. BitFun 已在目标平台启动。
2. mock 模型已经在会话场景中配置并可选。
3. 测试发送的 prompt 中包含 `[MOCK_SCENARIO]` 标记块。

## 共用基础流程

步骤：

1. 打开会话场景。
2. 选择预期的 mock 模型。
3. 填写聊天输入框。
4. 点击发送。
5. 等待预期的交互产物或最终响应。

共用定位点：

| 元素名称 | data-testid | 说明 |
|---|---|---|
| 会话场景根节点 | `session-scene` | 会话场景内容根节点。 |
| 聊天输入容器 | `chat-input-container` | 输入区根容器。 |
| 聊天输入可编辑区域 | `chat-input-textarea` | 真正接收输入的可编辑节点。 |
| 发送按钮 | `chat-input-send-btn` | 发送动作。 |
| 聊天模型选择按钮 | `chat-model-selector-btn` | 打开模型菜单。 |
| 聊天模型菜单 | `chat-model-selector-menu` | 下拉菜单根节点。 |
| 聊天模型选项 | `chat-model-selector-option` | 配合 `data-model-name` 使用。 |
| FlowChat 消息区域 | `flowchat-messages` | 会话消息宿主区域。 |
| FlowChat 消息项 | `flowchat-message-item` | 配合 `data-item-type`、`data-turn-id` 使用。 |
| 用户消息 | `chat-user-message` | 配合 `data-status`、`data-failed` 使用。 |
| 用户消息内容 | `chat-user-message-content` | 用户 prompt 文本。 |
| 助手消息 | `chat-assistant-message` | 配合 `data-status`、`data-streaming` 使用。 |
| 助手消息内容 | `chat-assistant-message-content` | 最终渲染的回答文本。 |

## TC-MOCK-001 普通回答

场景 id：

`simple_answer`

目标：

- 验证最基本的发送 / 接收链路。
- 验证普通 assistant 响应能正确渲染。

Mock JSON 结构：

```json
{
  "scenario_id": "simple_answer",
  "mode": "chat_completions",
  "stream": false,
  "turns": [
    {
      "assistant": {
        "thinking": ["识别 simple_answer 场景", "返回固定文本"],
        "final_text": "这是 BitFun Mock LLM Server 的固定回答。"
      }
    }
  ]
}
```

UI 断言：

- 出现一条用户消息，且 `data-status != error`。
- 出现一条助手消息。
- `chat-assistant-message-content` 包含固定回答文本。

需要补充的额外定位点：

| 元素名称 | data-testid | 说明 |
|---|---|---|
| 助手消息 | `chat-assistant-message` | 配合 `data-status`、`data-streaming` 使用。 |
| 助手消息内容 | `chat-assistant-message-content` | 最终回答文本。 |

## TC-MOCK-002 思考过程面板

场景 id：

`thinking_panel_demo`

目标：

- 验证 reasoning / thinking 内容会出现在会话 UI 中。
- 如果 BitFun 用折叠区展示思考过程，验证展开 / 收起交互是否正常。

Mock JSON 结构：

```json
{
  "scenario_id": "thinking_panel_demo",
  "mode": "chat_completions",
  "stream": true,
  "turns": [
    {
      "assistant": {
        "thinking": [
          "先分析任务目标。",
          "再组织最终回答。"
        ],
        "final_text": "这是带思考过程的最终回答。",
        "stream_chunks": [
          "这是带思考过程的",
          "最终回答。"
        ]
      }
    }
  ]
}
```

UI 断言：

- 出现思考过程面板或入口。
- 思考文本可以看到。
- 如果有展开按钮，展开 / 收起状态能切换。
- 最终助手回答仍然能正常显示。

需要补充的额外定位点：

| 元素名称 | data-testid | 说明 |
|---|---|---|
| 思考过程根节点 | `chat-thinking-panel` | 推理内容区域根节点。 |
| 思考过程切换按钮 | `chat-thinking-toggle` | 展开 / 收起控制。 |
| 思考过程内容 | `chat-thinking-content` | 渲染出来的 reasoning 文本。 |

## TC-MOCK-003 工具调用轨迹

场景 id：

`tool_trace_demo`

目标：

- 验证 BitFun 能展示工具调用。
- 验证 BitFun 能从第一轮 `tool_calls` 继续走到第二轮最终回答。

Mock JSON 结构：

```json
{
  "scenario_id": "tool_trace_demo",
  "mode": "chat_completions",
  "stream": true,
  "turns": [
    {
      "assistant": {
        "thinking": [
          "先检查工作区。",
          "再调用工具读取 README 和 git 状态。"
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
          "工具调用已完成。",
          "返回固定的最终回答。"
        ],
        "final_text": "Mock tool calls completed through BitFun tools."
      }
    }
  ]
}
```

UI 断言：

- 出现工具调用卡片。
- 工具名称正确。
- 工具参数可查看。
- 第二阶段最终回答会在工具调用之后出现。

需要补充的额外定位点：

| 元素名称 | data-testid | 说明 |
|---|---|---|
| 工具调用组 | `chat-tool-call-group` | 一轮内工具调用容器。 |
| 工具调用项 | `chat-tool-call-item` | 配合 `data-tool-name`、`data-tool-call-id` 使用。 |
| 工具参数区域 | `chat-tool-call-arguments` | 展开的参数详情。 |
| 工具调用切换按钮 | `chat-tool-call-toggle` | 展开 / 收起控制。 |

## TC-MOCK-004 Shell 命令结果

场景 id：

`shell_command_demo`

目标：

- 验证会话中 Shell 命令执行记录的展示。
- 验证命令、输出和退出码的呈现。

Mock JSON 结构：

```json
{
  "scenario_id": "shell_command_demo",
  "mode": "chat_completions",
  "stream": false,
  "turns": [
    {
      "assistant": {
        "thinking": ["返回一个固定的 Shell 命令结果。"],
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

UI 断言：

- 出现 Shell 命令卡片。
- 命令文本正确。
- 输出文本正确。
- 退出码可见，并显示为成功状态。
- 如果有折叠交互，详情可以展开。

需要补充的额外定位点：

| 元素名称 | data-testid | 说明 |
|---|---|---|
| Shell 命令卡片 | `chat-shell-command-card` | 重复项。 |
| Shell 命令文本 | `chat-shell-command-text` | 命令字符串本身。 |
| Shell 输出区域 | `chat-shell-command-output` | stdout / stderr 展示区。 |
| Shell 退出码 | `chat-shell-command-exit-code` | 配合 `data-exit-code`、`data-status` 使用。 |
| Shell 切换按钮 | `chat-shell-command-toggle` | 展开 / 收起详情。 |

## TC-MOCK-005 文件修改

场景 id：

`file_change_demo`

目标：

- 验证文件修改类产物能正确渲染。
- 验证文件路径、动作类型和内容预览交互。

Mock JSON 结构：

```json
{
  "scenario_id": "file_change_demo",
  "mode": "chat_completions",
  "stream": false,
  "turns": [
    {
      "assistant": {
        "thinking": ["返回一个固定的文件修改结果。"],
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

UI 断言：

- 出现文件修改卡片。
- 文件路径正确。
- 动作类型正确。
- 可以打开预览 / 详情。
- 预览内容包含预期文本片段。

需要补充的额外定位点：

| 元素名称 | data-testid | 说明 |
|---|---|---|
| 文件修改卡片 | `chat-file-change-card` | 重复项。 |
| 文件路径 | `chat-file-change-path` | 文件路径标签。 |
| 文件动作类型 | `chat-file-change-action` | 配合 `data-action` 使用。 |
| 文件内容预览 | `chat-file-change-preview` | 代码 / 文本预览区域。 |
| 文件修改切换按钮 | `chat-file-change-toggle` | 展开 / 收起详情。 |

## TC-MOCK-006 Mini App 结果

场景 id：

`miniapp_demo`

目标：

- 验证 BitFun 能展示 Mini App 生成结果。
- 验证用户可以打开或查看生成出来的 Mini App 产物。

Mock JSON 结构：

```json
{
  "scenario_id": "miniapp_demo",
  "mode": "chat_completions",
  "stream": false,
  "turns": [
    {
      "assistant": {
        "thinking": ["准备一个固定的 Mini App 结果。"],
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

UI 断言：

- 出现 Mini App 结果卡片。
- 标题可见。
- 文件列表可见。
- 如果 BitFun 提供打开 / 预览入口，该入口可点击并进入详情。

需要补充的额外定位点：

| 元素名称 | data-testid | 说明 |
|---|---|---|
| Mini App 卡片 | `chat-miniapp-card` | 单个生成结果的根卡片。 |
| Mini App 标题 | `chat-miniapp-title` | 标题文本。 |
| Mini App 文件列表 | `chat-miniapp-file-list` | 文件列表容器。 |
| Mini App 文件行 | `chat-miniapp-file-row` | 配合 `data-path` 使用。 |
| Mini App 打开按钮 | `chat-miniapp-open-btn` | 打开预览或详情。 |

## 实施优先级

建议顺序：

1. `simple_answer`
2. `thinking_panel_demo`
3. `tool_trace_demo`
4. `shell_command_demo`
5. `file_change_demo`
6. `miniapp_demo`

这样前几个场景会更贴近会话页的核心体验，后面再逐步补充更丰富的交互产物验证。

## 当前可能缺失的定位点

根据当前 BitFun Web UI 源码检索结果，下面这些会话交互定位点大概率还没有真正落到前端代码里。对应 demo 测试已经补好，但如果这些 locator 还没实现，测试会自动 `skip`：

| 场景区域 | 可能缺失的 data-testid |
|---|---|
| 思考过程 | `chat-thinking-panel`、`chat-thinking-toggle`、`chat-thinking-content` |
| 工具调用轨迹 | `chat-tool-call-group`、`chat-tool-call-item`、`chat-tool-call-arguments`、`chat-tool-call-toggle` |
| Shell 命令结果 | `chat-shell-command-card`、`chat-shell-command-text`、`chat-shell-command-output`、`chat-shell-command-exit-code`、`chat-shell-command-toggle` |
| 文件修改结果 | `chat-file-change-card`、`chat-file-change-path`、`chat-file-change-action`、`chat-file-change-preview`、`chat-file-change-toggle` |
| Mini App 结果 | `chat-miniapp-card`、`chat-miniapp-title`、`chat-miniapp-file-list`、`chat-miniapp-file-row`、`chat-miniapp-open-btn` |
