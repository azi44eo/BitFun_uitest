from __future__ import annotations

import json
import os
import time
import urllib.request
from typing import Any

import pytest


def test_mock_llm_session_starts_and_loads_scenarios(mock_llm_server_session):
    health = _get_json(f"http://127.0.0.1:{mock_llm_server_session['host_port']}/health")
    assert health["status"] == "ok"
    assert health["scenarios_dir"] == mock_llm_server_session["scenarios_dir"]
    assert health["scenario_count"] >= 3

    scenarios = _get_json(f"{mock_llm_server_session['host_base_url']}/scenarios")
    assert {
        "simple_answer",
        "tool_trace_demo",
        "file_and_miniapp_demo",
        "thinking_panel_demo",
        "shell_command_demo",
        "file_change_demo",
        "miniapp_demo",
        "long_task_demo",
        "error_then_success",
    } <= set(scenarios["data"])

    models = _get_json(f"{mock_llm_server_session['host_base_url']}/models")
    assert {"bitfun-mock", "bitfun-mock-tools", "bitfun-mock-files"} <= {
        item["id"] for item in models["data"]
    }

    models_alias = _get_json(f"http://127.0.0.1:{mock_llm_server_session['host_port']}/models")
    assert {item["id"] for item in models_alias["data"]} == {item["id"] for item in models["data"]}

    assert os.environ["BITFUN_TEST_LLM_BASE_URL"] == mock_llm_server_session["bitfun_base_url"]
    assert os.environ["BITFUN_TEST_LLM_MODEL"] == "bitfun-mock"
    assert os.environ["BITFUN_TEST_LLM_API_KEY"] == "mock-key"


def test_mock_llm_chat_completion_uses_scenario(mock_llm_server_session):
    payload = {
        "model": "bitfun-mock",
        "stream": False,
        "messages": [
            {
                "role": "user",
                "content": "[MOCK_SCENARIO]\nid=simple_answer\n[/MOCK_SCENARIO]",
            }
        ],
    }

    response = _post_json(f"{mock_llm_server_session['host_base_url']}/chat/completions", payload)
    message = response["choices"][0]["message"]

    assert message["content"] == "这是 BitFun Mock LLM Server 的固定回答。"
    assert "simple_answer" in message["reasoning_content"]
    assert message["bitfun_mock"]["scenario_id"] == "simple_answer"


def test_mock_llm_chat_completion_can_drive_two_step_tool_flow(mock_llm_server_session):
    first_payload = {
        "model": "bitfun-mock-tools",
        "stream": False,
        "messages": [
            {
                "role": "user",
                "content": "[MOCK_SCENARIO]\nid=tool_trace_demo\n[/MOCK_SCENARIO]",
            }
        ],
    }

    first_response = _post_json(f"{mock_llm_server_session['host_base_url']}/chat/completions", first_payload)
    first_message = first_response["choices"][0]["message"]

    assert first_response["choices"][0]["finish_reason"] == "tool_calls"
    assert [call["function"]["name"] for call in first_message["tool_calls"]] == ["read_file", "exec_command"]

    second_payload = {
        "model": "bitfun-mock-tools",
        "stream": False,
        "messages": [
            {
                "role": "user",
                "content": "[MOCK_SCENARIO]\nid=tool_trace_demo\n[/MOCK_SCENARIO]",
            },
            {
                "role": "tool",
                "tool_call_id": "call_readme",
                "content": "# README",
            },
        ],
    }

    second_response = _post_json(f"{mock_llm_server_session['host_base_url']}/chat/completions", second_payload)
    second_message = second_response["choices"][0]["message"]

    assert second_response["choices"][0]["finish_reason"] == "stop"
    assert second_message["content"] == "Mock tool calls completed through BitFun tools."


def test_mock_llm_shell_command_demo_uses_standard_bash_tool(mock_llm_server_session):
    first_payload = {
        "model": "bitfun-mock",
        "stream": False,
        "messages": [
            {
                "role": "user",
                "content": "[MOCK_SCENARIO]\nid=shell_command_demo\n[/MOCK_SCENARIO]",
            }
        ],
    }

    first_response = _post_json(f"{mock_llm_server_session['host_base_url']}/chat/completions", first_payload)
    first_message = first_response["choices"][0]["message"]

    assert first_response["choices"][0]["finish_reason"] == "tool_calls"
    assert first_message["tool_calls"][0]["function"]["name"] == "Bash"

    second_payload = {
        "model": "bitfun-mock",
        "stream": False,
        "messages": [
            {
                "role": "user",
                "content": "[MOCK_SCENARIO]\nid=shell_command_demo\n[/MOCK_SCENARIO]",
            },
            {
                "role": "tool",
                "tool_call_id": "call_bash_mock_status",
                "content": "M README.md",
            },
        ],
    }

    second_response = _post_json(f"{mock_llm_server_session['host_base_url']}/chat/completions", second_payload)
    assert second_response["choices"][0]["message"]["content"] == "Rendered one shell command result."


def test_mock_llm_file_change_demo_uses_standard_write_tool(mock_llm_server_session):
    first_payload = {
        "model": "bitfun-mock",
        "stream": False,
        "messages": [
            {
                "role": "user",
                "content": "[MOCK_SCENARIO]\nid=file_change_demo\n[/MOCK_SCENARIO]",
            }
        ],
    }

    first_response = _post_json(f"{mock_llm_server_session['host_base_url']}/chat/completions", first_payload)
    first_message = first_response["choices"][0]["message"]

    assert first_response["choices"][0]["finish_reason"] == "tool_calls"
    assert first_message["tool_calls"][0]["function"]["name"] == "Write"
    assert ".bitfun-ui-test/mock-file-change/App.tsx" in first_message["tool_calls"][0]["function"]["arguments"]

    second_payload = {
        "model": "bitfun-mock",
        "stream": False,
        "messages": [
            {
                "role": "user",
                "content": "[MOCK_SCENARIO]\nid=file_change_demo\n[/MOCK_SCENARIO]",
            },
            {
                "role": "tool",
                "tool_call_id": "call_write_mock_file",
                "content": "Successfully created .bitfun-ui-test/mock-file-change/App.tsx",
            },
        ],
    }

    second_response = _post_json(f"{mock_llm_server_session['host_base_url']}/chat/completions", second_payload)
    assert second_response["choices"][0]["message"]["content"] == "Rendered one file change result."


def test_mock_llm_miniapp_demo_uses_standard_init_miniapp_tool(mock_llm_server_session):
    first_payload = {
        "model": "bitfun-mock",
        "stream": False,
        "messages": [
            {
                "role": "user",
                "content": "[MOCK_SCENARIO]\nid=miniapp_demo\n[/MOCK_SCENARIO]",
            }
        ],
    }

    first_response = _post_json(f"{mock_llm_server_session['host_base_url']}/chat/completions", first_payload)
    first_message = first_response["choices"][0]["message"]

    assert first_response["choices"][0]["finish_reason"] == "tool_calls"
    assert first_message["tool_calls"][0]["function"]["name"] == "InitMiniApp"
    assert "BitFun Mock Mini App" in first_message["tool_calls"][0]["function"]["arguments"]

    second_payload = {
        "model": "bitfun-mock",
        "stream": False,
        "messages": [
            {
                "role": "user",
                "content": "[MOCK_SCENARIO]\nid=miniapp_demo\n[/MOCK_SCENARIO]",
            },
            {
                "role": "tool",
                "tool_call_id": "call_init_miniapp_mock",
                "content": "MiniApp skeleton created",
            },
        ],
    }

    second_response = _post_json(f"{mock_llm_server_session['host_base_url']}/chat/completions", second_payload)
    assert second_response["choices"][0]["message"]["content"] == "Rendered one mini app result."


def test_mock_llm_supports_auxiliary_tool_probe_and_title_generation(mock_llm_server_session):
    tool_probe = {
        "model": "bitfun-mock",
        "stream": False,
        "messages": [
            {"role": "user", "content": "Call the get_weather tool for city=Beijing. Do not answer with plain text."}
        ],
        "tool_choice": "auto",
        "tools": [
            {
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "Get the weather of a city",
                    "parameters": {
                        "type": "object",
                        "properties": {"city": {"type": "string"}},
                        "required": ["city"],
                    },
                },
            }
        ],
    }

    first_tool_response = _post_json(f"{mock_llm_server_session['host_base_url']}/chat/completions", tool_probe)
    assert first_tool_response["choices"][0]["finish_reason"] == "tool_calls"
    assert first_tool_response["choices"][0]["message"]["tool_calls"][0]["function"]["name"] == "get_weather"

    tool_probe["messages"].append({"role": "tool", "tool_call_id": "call_get_weather", "content": "晴朗"})
    second_tool_response = _post_json(f"{mock_llm_server_session['host_base_url']}/chat/completions", tool_probe)
    assert second_tool_response["choices"][0]["message"]["content"] == "Tool capability probe completed."

    title_payload = {
        "model": "bitfun-mock",
        "stream": False,
        "messages": [
            {
                "role": "system",
                "content": "You are a professional session title generation assistant. Please generate session title.",
            },
            {
                "role": "user",
                "content": "User message: [MOCK_SCENARIO]\nid=simple_answer\n[/MOCK_SCENARIO]",
            },
        ],
    }
    title_response = _post_json(f"{mock_llm_server_session['host_base_url']}/chat/completions", title_payload)
    assert title_response["choices"][0]["message"]["content"] == "Mock 会话"


def test_mock_llm_long_task_demo_uses_standard_task_tool(mock_llm_server_session):
    first_payload = {
        "model": "bitfun-mock",
        "stream": False,
        "messages": [
            {
                "role": "user",
                "content": "[MOCK_SCENARIO]\nid=long_task_demo\n[/MOCK_SCENARIO]",
            }
        ],
    }
    first_response = _post_json(f"{mock_llm_server_session['host_base_url']}/chat/completions", first_payload)
    choice = first_response["choices"][0]
    assert choice["finish_reason"] == "tool_calls"
    tool_call = choice["message"]["tool_calls"][0]
    assert tool_call["function"]["name"] == "Task"
    arguments = json.loads(tool_call["function"]["arguments"])
    assert arguments["subagent_type"] == "Explore"
    assert arguments["run_in_background"] is True
    assert "long_task_child" in arguments["prompt"]

    second_payload = {
        **first_payload,
        "messages": [
            *first_payload["messages"],
            choice["message"],
            {
                "role": "tool",
                "tool_call_id": tool_call["id"],
                "content": "{\"status\":\"started\",\"run_in_background\":true}",
            },
        ],
    }
    second_response = _post_json(f"{mock_llm_server_session['host_base_url']}/chat/completions", second_payload)
    assert second_response["choices"][0]["message"]["content"] == "Long task background task started."


def test_mock_llm_long_task_child_waits_and_then_succeeds(mock_llm_server_session):
    payload = {
        "model": "bitfun-mock",
        "stream": False,
        "messages": [
            {
                "role": "user",
                "content": "[MOCK_SCENARIO]\nid=long_task_child\n[/MOCK_SCENARIO]",
            }
        ],
    }
    started = time.time()
    response = _post_json(
        f"{mock_llm_server_session['host_base_url']}/chat/completions",
        payload,
        timeout=20,
    )
    elapsed = time.time() - started
    assert elapsed >= 11
    assert response["choices"][0]["message"]["content"] == "Background long task child completed."


def test_mock_llm_error_then_success_fails_once_then_recovers(mock_llm_server_session):
    payload = {
        "model": "bitfun-mock",
        "stream": False,
        "messages": [
            {
                "role": "user",
                "content": "[MOCK_SCENARIO]\nid=error_then_success\n[/MOCK_SCENARIO]",
            }
        ],
    }
    request = urllib.request.Request(
        f"{mock_llm_server_session['host_base_url']}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with pytest.raises(Exception):
        urllib.request.urlopen(request, timeout=5)

    response = _post_json(f"{mock_llm_server_session['host_base_url']}/chat/completions", payload)
    assert response["choices"][0]["message"]["content"] == "Recovered successfully after retry."


def test_mock_llm_error_then_success_is_isolated_by_run_id(mock_llm_server_session):
    first_run = _error_then_success_payload("run-a")
    second_run = _error_then_success_payload("run-b")

    _assert_chat_completion_fails(mock_llm_server_session, first_run)
    response = _post_json(f"{mock_llm_server_session['host_base_url']}/chat/completions", first_run)
    assert response["choices"][0]["message"]["content"] == "Recovered successfully after retry."

    _assert_chat_completion_fails(mock_llm_server_session, second_run)
    response = _post_json(f"{mock_llm_server_session['host_base_url']}/chat/completions", second_run)
    assert response["choices"][0]["message"]["content"] == "Recovered successfully after retry."


def test_parse_chat_request_uses_latest_user_mock_marker():
    from bitfun_mock_llm_server.request_parser import parse_chat_request

    payload = {
        "model": "bitfun-mock",
        "stream": False,
        "messages": [
            {
                "role": "user",
                "content": "[MOCK_SCENARIO]\nid=simple_answer\n[/MOCK_SCENARIO]",
            },
            {
                "role": "assistant",
                "content": "This is an old assistant response.",
            },
            {
                "role": "user",
                "content": "[MOCK_SCENARIO]\nid=thinking_panel_demo\n[/MOCK_SCENARIO]",
            },
        ],
    }

    parsed = parse_chat_request(payload, default_scenario_id=None)

    assert parsed.scenario_id == "thinking_panel_demo"
    assert parsed.turn_index == 0


def _error_then_success_payload(run_id: str) -> dict[str, Any]:
    return {
        "model": "bitfun-mock",
        "stream": False,
        "messages": [
            {
                "role": "user",
                "content": f"[MOCK_SCENARIO]\nid=error_then_success\nrun_id={run_id}\n[/MOCK_SCENARIO]",
            }
        ],
    }


def _assert_chat_completion_fails(mock_llm_server_session, payload: dict[str, Any]) -> None:
    request = urllib.request.Request(
        f"{mock_llm_server_session['host_base_url']}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with pytest.raises(Exception):
        urllib.request.urlopen(request, timeout=5)


def _get_json(url: str) -> dict[str, Any]:
    with urllib.request.urlopen(url, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


def _post_json(url: str, payload: dict[str, Any], timeout: int = 5) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))
