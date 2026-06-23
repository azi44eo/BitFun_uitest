[English](system-e2e-cases.md) | **中文**

# BitFun 端到端系统测试用例

本文档将 10 个端到端系统测试用例整理成“可自动化实现”的格式。每个用例都
明确前置条件、可控测试手段、执行步骤和预期结果，避免只停留在业务意图层。

## 约定

- 测试过程中创建的数据应使用唯一前缀，例如：
  `E2E-Model-<timestamp>`、`E2E-Session-A`、`E2E-Workspace-A`。
- 优先使用可重复的 mock 场景。
- 如果用例会修改持久化设置或创建数据，要么在同一用例中恢复，要么使用隔离的
  测试命名空间。
- 如果缺少必需 locator，应视为测试实现阻塞，而不是产品通过。

## 就绪状态说明

- `Ready`：当前已经具备主要测试条件，可以直接开始落自动化。
- `Need Locators`：业务流程已经明确，但稳定 UI locator 还不够。
- `Need Test Mechanism`：还缺少可重复的触发方式、重置方式或隔离测试夹具，即使 locator 齐全也会不稳定。

## E2E-001 Mock 会话交互链路

状态：

`Ready`

当前仍需补充：

- 随着更多会话结果块进入自动化范围，继续补齐对应会话 artifact locator。

### 前置条件

1. BitFun 能在目标设备上正常启动。
2. mock 模型已经配置完成，并且可以在会话模型选择器中被选中。
3. mock server 已提供这些场景：
   `simple_answer`、`thinking_panel_demo`、`tool_trace_demo`、
   `shell_command_demo`、`file_change_demo`、`miniapp_demo`。
4. 已有以下核心 locator：
   `session-scene`、`chat-input-textarea`、`chat-input-send-btn`、
   `chat-model-selector-btn`、`chat-model-selector-option`、
   `chat-assistant-message-content`。

### 执行步骤

1. 打开会话场景。
2. 选择 mock 模型。
3. 发送 `simple_answer` prompt 并等待最终回答。
4. 发送 `thinking_panel_demo` prompt 并验证思考过程展示。
5. 发送 `tool_trace_demo` prompt 并验证工具调用轨迹展示。
6. 发送 `shell_command_demo` prompt 并验证 shell 结果展示。
7. 发送 `file_change_demo` prompt 并验证文件修改展示。
8. 发送 `miniapp_demo` prompt 并验证 miniapp 结果展示。

### 预期结果

1. 每次发送都能从 pending 正常进入 completed。
2. 每个场景的最终 assistant 回答都能正确显示。
3. 思考过程、工具调用、Shell 结果、文件修改和 Mini App 产物都能按预期顺序显示。
4. 展开某一类结果卡片不会破坏整个会话界面。

## E2E-002 模型配置完整生命周期

状态：

`Ready`

当前仍需补充：

- 核心的创建、编辑、保存、使用链路暂无阻塞项。

### 前置条件

1. 可以从底部菜单进入设置页。
2. 测试模型服务端可用，并支持：
   `/models`、`/chat/completions`、连接测试。
3. 已有以下 locator：
   `settings-nav-tab`、`settings-model-create-first-config-btn`、
   `settings-model-provider-name-input`、`settings-model-api-key-input`、
   `settings-model-base-url-input`、`settings-model-select-btn`、
   `settings-model-option`、`settings-model-save-btn`、
   `settings-model-row`、`settings-model-test-status`、
   `chat-model-selector-btn`、`chat-model-selector-option`。

### 执行步骤

1. 打开设置页并切换到模型页签。
2. 使用唯一 provider 名称创建新的模型服务商配置。
3. 从远端模型列表中拉取并选择一个模型。
4. 如果流程支持，再添加一个自定义模型名。
5. 保存配置。
6. 等待连接测试成功。
7. 重新打开该配置，修改一个可编辑字段，例如 provider 名称。
8. 再次保存，并确认修改结果持久化。
9. 回到会话页，确认该模型可以在聊天模型选择器中被选中。

### 预期结果

1. 模型服务商配置创建成功。
2. 远端模型发现成功，返回可选模型。
3. 保存成功后，配置出现在模型列表中。
4. 连接测试状态为 success。
5. 修改后的字段在重新打开后仍然保持。
6. 该模型可以在会话中被实际选用。

## E2E-003 会话管理完整流程

状态：

`Ready`

当前仍需补充：

- 核心的创建、重命名、切换、删除链路暂无阻塞项。

### 前置条件

1. 至少存在一个可用工作区。
2. 至少存在一个可用模型，可以用于发送消息。
3. 已有以下 locator：
   `nav-session-item`、`nav-session-menu-btn`、`nav-session-menu`、
   `nav-session-menu-rename`、`nav-session-menu-delete`、
   `chat-input-textarea`、`chat-input-send-btn`。

### 执行步骤

1. 创建会话 A，并发送一条唯一消息。
2. 创建会话 B，并发送另一条唯一消息。
3. 通过会话菜单将会话 A 重命名。
4. 从会话 B 切回会话 A，检查消息历史。
5. 再切回会话 B，检查其消息历史。
6. 删除会话 A。
7. 验证会话 B 仍然可用，并能继续发送消息。

### 预期结果

1. 会话 A 和会话 B 独立创建成功。
2. 会话重命名会立即在列表中反映，并持久化。
3. 在不同会话之间切换时，消息历史不会串。
4. 删除会话 A 后，它从列表中消失。
5. 删除一个会话不会破坏另一个会话。

## E2E-004 工作区与会话绑定关系

状态：

`Need Test Mechanism`

当前仍需补充：

- 两个稳定的测试工作区夹具，或文档化的固定测试路径。
- 工作区 A / B 的初始化和清理规则。
- 工作区内创建会话所依赖 locator 的完整性确认。

### 前置条件

1. 两个隔离的测试工作区已经存在，或者可以被创建。
2. 已有可用模型可以发送消息。
3. 已有以下 locator：
   `nav-workspace-item`、`nav-workspace-name-btn`、
   `nav-workspace-session-region`、`nav-session-item`、
   `chat-input-workspace-strip`。

### 执行步骤

1. 打开工作区 A，在其下创建会话 A1。
2. 在 A1 中发送一条唯一消息。
3. 打开工作区 B，在其下创建会话 B1。
4. 在 B1 中发送另一条唯一消息。
5. 验证导航树中 A1 属于工作区 A，B1 属于工作区 B。
6. 重新打开 A1，检查工作区提示条显示为工作区 A。
7. 重新打开 B1，检查工作区提示条显示为工作区 B。

### 预期结果

1. 会话始终绑定在正确的工作区下。
2. 导航树和会话 UI 中的工作区上下文一致。
3. 切换工作区不会导致消息历史混乱。

## E2E-005 通知中心任务跟踪

状态：

`Need Test Mechanism`

当前仍需补充：

- 一个可重复触发的长耗时任务入口。
- 一个可稳定判断任务“运行中 / 已完成”的状态机制。
- 任务通知相关 locator 的完整性确认。

### 前置条件

1. 存在一个可重复触发的长耗时 mock 场景或后台任务路径。
2. 已有以下 locator：
   `notification-button`、`notification-center`、
   `notification-center-active-section`。
3. 所选动作已知会创建可见的后台任务项。

### 执行步骤

1. 从会话或其他入口触发长耗时动作。
2. 观察通知按钮状态变化。
3. 打开通知中心。
4. 验证运行中的任务出现在活动任务区。
5. 等待任务完成。
6. 检查任务项是否按产品设计更新或移除。
7. 关闭通知中心。

### 预期结果

1. 通知按钮能够反映活动任务状态。
2. 通知中心在任务运行时显示对应任务项。
3. 任务完成后，通知状态更新正确。
4. 打开和关闭通知中心不会中断后台任务。

## E2E-006 设置页导航与持久化

状态：

`Need Test Mechanism`

当前仍需补充：

- 两个固定、稳定、易恢复的设置项，作为统一测试对象。
- 明确的设置恢复规则。
- 这些设置项对应保存控件的 locator 确认。

### 前置条件

1. 可以从底部菜单打开设置页。
2. 至少两个不同页签中存在可保存设置项。
3. 已有以下 locator：
   `settings-scene`、`settings-nav`、`settings-nav-tab`，
   以及各页签对应的保存控件。

### 执行步骤

1. 打开设置页。
2. 在基础设置页修改一个可保存项。
3. 切换到另一个页签，例如编辑器或快捷键，再修改一个可保存项。
4. 保存修改。
5. 关闭设置页。
6. 重新打开设置页，并回到刚修改的两个页签。
7. 检查修改后的值是否仍然存在。

### 预期结果

1. 跨页签导航稳定。
2. 保存不会误伤未修改的配置项。
3. 重新打开设置页后，修改值仍然正确。

## E2E-007 Agent 与 Skill 发现流程

状态：

`Need Locators`

当前仍需补充：

- 稳定的 agent 卡片 locator 和主要动作 locator。
- 稳定的 skill 卡片 locator 和主要动作 locator。
- 一个固定的 agent / skill 测试目标，避免每次“随便挑一个”。

### 前置条件

1. Agents 和 Skills 导航入口可见。
2. 至少存在一个 agent 卡片和一个 skill 卡片。
3. 对应 scene、页签、卡片和主要按钮的 locator 已补齐。

### 执行步骤

1. 打开 Agents 场景。
2. 验证至少一个 agent 卡片可见。
3. 打开一个非破坏性 agent 动作，例如详情或配置。
4. 返回后打开 Skills 场景。
5. 在 Installed 和 Discover 之间切换。
6. 验证至少一个 skill 卡片可见。
7. 执行一个非破坏性 skill 动作，例如详情或打开路径。

### 预期结果

1. Agents 和 Skills 场景都能正常打开。
2. 卡片可见且可交互。
3. 非破坏性操作完成后，主导航和会话状态不受影响。

## E2E-008 Shell 与 Browser 面板联动

状态：

`Need Locators`

当前仍需补充：

- Shell 面板成功挂载的稳定 locator。
- Browser 面板成功挂载的稳定 locator。
- “面板已打开”对应的明确断言锚点。

### 前置条件

1. 底部 Shell 和 Browser 入口存在。
2. 已有一个带消息历史的会话。
3. 对应 shell/browser 打开与关闭路径的 locator 已补齐。

### 执行步骤

1. 打开一个已有会话，确认历史消息可见。
2. 从底部入口打开 Shell 面板。
3. 验证 Shell 面板加载成功。
4. 切换到 Browser 面板。
5. 验证 Browser 面板加载成功。
6. 返回原会话场景。
7. 再发送一条消息。

### 预期结果

1. Shell 和 Browser 面板都能正常打开。
2. 切换工具面板不会重置会话。
3. 返回会话后，当前会话仍可继续交互。

## E2E-009 会话错误恢复流程

状态：

`Need Test Mechanism`

当前仍需补充：

- 一个稳定可重复的失败触发手段。
- 一个稳定可重复的恢复手段。
- 明确的 retry / resend 产品路径。
- 失败消息和重试控件的 locator 确认。

### 前置条件

1. 存在一个可重复触发失败的手段，例如错误模型配置、错误 API key
   或强制失败的 mock 场景。
2. 同时存在一个可恢复到成功状态的手段，例如恢复有效模型或切回成功 mock 场景。
3. 已有以下 locator：
   `chat-user-message`、`chat-user-message-content`，
   以及产品提供的 retry / resend 控件。

### 执行步骤

1. 在会话中触发一次失败请求。
2. 等待失败状态在会话中显示出来。
3. 检查输入区仍然可用。
4. 恢复模型或服务端到有效状态。
5. 使用产品支持的重试或重新发送路径再次发起请求。
6. 等待一条成功的 assistant 回答。
7. 再发送一条普通消息。

### 预期结果

1. 失败状态在 UI 中清晰可见。
2. 会话不会因失败而不可恢复。
3. 恢复后重试成功。
4. 恢复完成后，会话可以继续正常工作。

## E2E-010 从冷启动到首个有效会话

状态：

`Need Test Mechanism`

当前仍需补充：

- 一套可重复执行的“干净状态重置”流程。
- 一个隔离的首启工作区 / 模型夹具。
- 首启流程关键 locator 的完整性确认。

### 前置条件

1. 应用从干净或隔离的首启状态启动。
2. 已准备一个测试工作区路径。
3. 已准备一个可用的测试模型服务端。
4. 欢迎页、工作区配置、模型配置、会话创建所需 locator 已补齐。

### 执行步骤

1. 以干净状态启动 BitFun。
2. 完成欢迎页或空状态的最小引导流程。
3. 打开或创建测试工作区。
4. 完成最小模型配置。
5. 创建第一个可用会话。
6. 选择已配置好的模型。
7. 发送第一条消息。
8. 等待成功回答。
9. 关闭并重新打开应用，或触发等价状态刷新。
10. 检查工作区、模型和会话是否仍然存在。

### 预期结果

1. 用户可以从冷启动一路走到首个可用会话。
2. 工作区、模型、会话配置都能成功完成。
3. 第一条 AI 回答成功返回。
4. 重开或刷新后，已创建的状态仍然存在。
