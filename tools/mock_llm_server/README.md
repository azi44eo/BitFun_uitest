# bitfun-mock-llm-server

BitFun UI 自动化测试专用的 Mock LLM Server。

它提供一个本地 OpenAI-compatible 接口，接收 BitFun 发来的模型请求，但不调用任何真实大模型。服务会从请求消息里的 `[MOCK_SCENARIO]` 标记解析 `scenario_id`，读取本地场景 JSON 文件，并返回固定、可重复、可预测的响应，方便稳定验证 BitFun UI 对 thinking、tool call、shell command、文件修改、miniapp、流式输出等内容的展示。

## 技术栈

第一版使用 Python + FastAPI。

原因：

- 本地启动简单，接口调试方便。
- JSON 场景加载和校验直接。
- FastAPI/StreamingResponse 很适合实现 OpenAI 风格的 SSE 流式输出。
- 后续和 pytest 自动化测试生态贴合。

## 目录结构

```text
.
├── config/
│   └── server.example.json
├── src/
│   └── bitfun_mock_llm_server/
│       ├── api/routes.py
│       ├── config.py
│       ├── main.py
│       ├── request_parser.py
│       ├── responses/chat_completions.py
│       └── scenarios/
│           ├── loader.py
│           └── schema.py
├── tests/
│   └── test_request_parser.py
├── pyproject.toml
└── README.md
```

迁移到 BitFun UI 测试仓后，pytest 默认把场景目录设置为仓库根目录下的：

```text
mock_scenarios/
```

## 启动

推荐使用虚拟环境：

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
python3 -m bitfun_mock_llm_server
```

默认监听：

```text
http://127.0.0.1:8787
```

也可以直接用 uvicorn：

```bash
uvicorn bitfun_mock_llm_server.main:app --host 127.0.0.1 --port 8787
```

如果没有执行 `pip install -e .`，需要设置：

```bash
PYTHONPATH=src uvicorn bitfun_mock_llm_server.main:app --host 127.0.0.1 --port 8787
```

## 配置

默认读取 `config/server.example.json`。在测试仓内由 `conftest.py` 通过环境变量覆盖 host、port 和场景目录：

```json
{
  "host": "127.0.0.1",
  "port": 8787,
  "scenarios_dir": "scenarios",
  "default_scenario_id": "simple_answer",
  "strict_scenario": false
}
```

可用环境变量覆盖：

- `BITFUN_MOCK_CONFIG`: 配置文件路径
- `BITFUN_MOCK_HOST`: 服务 host
- `BITFUN_MOCK_PORT`: 服务 port
- `BITFUN_MOCK_SCENARIOS_DIR`: 场景目录
- `BITFUN_MOCK_DEFAULT_SCENARIO`: 默认场景 ID
- `BITFUN_MOCK_STRICT_SCENARIO`: 是否强制请求必须包含场景标记

## 接口

### 健康检查

```bash
curl http://127.0.0.1:8787/health
```

返回示例：

```json
{
  "status": "ok",
  "service": "bitfun-mock-llm-server",
  "scenarios_dir": "scenarios",
  "scenario_count": 3
}
```

### 场景列表

```bash
curl http://127.0.0.1:8787/v1/scenarios
```

### OpenAI Chat Completions

接口路径：

```text
POST /v1/chat/completions
```

BitFun 可以把模型 base URL 指到：

```text
http://127.0.0.1:8787/v1
```

## scenario_id 怎么传

推荐在 user message 中加入短标记：

```text
[MOCK_SCENARIO]
id=tool_trace_demo
[/MOCK_SCENARIO]
```

可选指定 turn：

```text
[MOCK_SCENARIO]
id=tool_trace_demo
turn=0
[/MOCK_SCENARIO]
```

服务也支持测试代码直接传：

```json
{
  "scenario_id": "tool_trace_demo",
  "messages": []
}
```

或：

```json
{
  "metadata": {
    "mock_scenario_id": "tool_trace_demo",
    "mock_turn_index": 0
  },
  "messages": []
}
```

## 非流式请求示例

```bash
curl http://127.0.0.1:8787/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "bitfun-mock",
    "stream": false,
    "messages": [
      {
        "role": "user",
        "content": "[MOCK_SCENARIO]\nid=simple_answer\n[/MOCK_SCENARIO]"
      }
    ]
  }'
```

返回核心结构：

```json
{
  "object": "chat.completion",
  "choices": [
    {
      "message": {
        "role": "assistant",
        "content": "这是 BitFun Mock LLM Server 的固定回答。",
        "reasoning_content": "识别到 simple_answer 场景\n返回固定文本",
        "tool_calls": [],
        "bitfun_mock": {
          "scenario_id": "simple_answer"
        }
      }
    }
  ]
}
```

## 流式请求示例

```bash
curl -N http://127.0.0.1:8787/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "bitfun-mock",
    "stream": true,
    "messages": [
      {
        "role": "user",
        "content": "[MOCK_SCENARIO]\nid=tool_trace_demo\n[/MOCK_SCENARIO]"
      }
    ]
  }'
```

返回为 OpenAI Chat Completions 风格 SSE：

```text
data: {"object":"chat.completion.chunk","choices":[{"delta":{"role":"assistant"}}]}

data: {"object":"chat.completion.chunk","choices":[{"delta":{"reasoning_content":"先检查项目结构\n"}}]}

data: {"object":"chat.completion.chunk","choices":[{"delta":{"tool_calls":[...]}}]}

data: [DONE]
```

## 场景 schema

场景文件放在测试仓根目录的 `mock_scenarios/<scenario_id>.json`。独立运行工具时，也可以通过 `BITFUN_MOCK_SCENARIOS_DIR` 指定其他目录。

示例：

```json
{
  "scenario_id": "tool_trace_demo",
  "description": "展示 thinking、tool call、shell command 的固定响应。",
  "mode": "chat_completions",
  "stream": true,
  "turns": [
    {
      "assistant": {
        "thinking": ["先检查项目结构", "然后读取关键文件"],
        "tool_calls": [
          {
            "id": "call_readme",
            "name": "read_file",
            "arguments": {
              "path": "README.md"
            }
          }
        ],
        "shell_commands": [
          {
            "command": "git status --short",
            "output": " M README.md\n?? src/\n",
            "exit_code": 0
          }
        ],
        "file_changes": [],
        "miniapp": null,
        "final_text": "我已经检查了项目结构。",
        "stream_chunks": ["我已经检查了", "项目结构。"]
      }
    }
  ]
}
```

字段说明：

- `scenario_id`: 场景 ID，必须和文件名保持一致，便于维护。
- `description`: 场景用途，建议写测试目标。
- `mode`: 当前只支持 `chat_completions`。
- `stream` / `default_stream`: 场景默认是否流式。请求体里的 `stream` 优先级更高。
- `turns`: 多轮响应定义。第一版默认使用 `turn=0`。
- `thinking`: 映射到非流式 `message.reasoning_content`，流式 `delta.reasoning_content`。
- `tool_calls`: 映射到 OpenAI `tool_calls`。
- `shell_commands`: 放在扩展字段 `bitfun_mock.shell_commands`，用于 BitFun UI 测试展示。
- `file_changes`: 放在扩展字段 `bitfun_mock.file_changes`。
- `miniapp`: 放在扩展字段 `bitfun_mock.miniapp`。
- `final_text`: assistant 最终文本。
- `stream_chunks`: 流式 content 分片。不写则一次性输出 `final_text`。

## 怎么添加新场景

1. 在测试仓根目录 `mock_scenarios/` 下新增 `<scenario_id>.json`。
2. 设置 `scenario_id`、`description`、`turns[0].assistant`。
3. 在 BitFun 测试输入里加入：

```text
[MOCK_SCENARIO]
id=<scenario_id>
[/MOCK_SCENARIO]
```

4. 调用 `/v1/chat/completions` 验证返回。

建议场景名贴近 UI 测试目标，例如：

- `thinking_panel_basic`
- `tool_call_multiple`
- `shell_command_failed`
- `file_diff_create_modify`
- `miniapp_generation_basic`
- `streaming_markdown_incremental`

## 最小验证

```bash
python3 -m compileall src tests
pytest
```
