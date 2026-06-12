from __future__ import annotations

import json
import os
import urllib.request
from typing import Any


def test_mock_llm_session_starts_and_loads_scenarios(mock_llm_server_session):
    health = _get_json(f"http://127.0.0.1:{mock_llm_server_session['host_port']}/health")
    assert health["status"] == "ok"
    assert health["scenarios_dir"] == mock_llm_server_session["scenarios_dir"]
    assert health["scenario_count"] >= 3

    scenarios = _get_json(f"{mock_llm_server_session['host_base_url']}/scenarios")
    assert {"simple_answer", "tool_trace_demo", "file_and_miniapp_demo"} <= set(scenarios["data"])

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


def _get_json(url: str) -> dict[str, Any]:
    with urllib.request.urlopen(url, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


def _post_json(url: str, payload: dict[str, Any]) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))
