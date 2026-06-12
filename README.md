# BitFun UI Test

Pytest-based UI automation for BitFun across OpenHarmony, Windows, and macOS.

The test cases use one platform-neutral API:

```python
ui.wait_for_test_id("notification-button")
ui.click_by_test_id("notification-button")
ui.wait_for_test_id("notification-center")
```

Platform differences live in the driver layer:

- `oh`: start BitFun through `hdc`, connect ArkWeb DevTools/CDP, execute JavaScript in the WebView.
- `win`: planned Selenium/WebDriver adapter for BitFun embedded WebDriver.
- `mac`: planned Selenium/WebDriver adapter for BitFun embedded WebDriver.

## Install

```powershell
python -m pip install -r requirements.txt
```

## Run OpenHarmony Demo

```powershell
python -m pytest --platform=oh
```

## Local Config

Secrets for integration cases live in a local JSON file that is ignored by git.
By default the test runner reads `local-config.json`; override it with
`--local-config` or `BITFUN_LOCAL_CONFIG`.

```json
{
  "models": {
    "openbitfun": {
      "api_key": "sk-..."
    }
  }
}
```

## Mock LLM Server

This test repo contains an internal mock LLM server under:

```text
tools/mock_llm_server/
```

When pytest starts, `conftest.py` automatically starts the server during session
setup and keeps it alive for all test cases. When pytest exits, the fixture
removes any HDC reverse port mapping it created and stops the server.

For OH runs, the fixture also creates an HDC reverse port mapping:

```text
OH 127.0.0.1:<device_port> -> Windows 127.0.0.1:<host_port>
```

The BitFun model config should use these environment variables:

```powershell
$env:BITFUN_TEST_LLM_BASE_URL
$env:BITFUN_TEST_LLM_MODEL
$env:BITFUN_TEST_LLM_API_KEY
```

During OH tests, `BITFUN_TEST_LLM_BASE_URL` is set to:

```text
http://127.0.0.1:18787/v1
```

For Windows/macOS test runs, it points directly to the host-side random port
chosen by pytest.

The device-side port can be changed:

```powershell
python -m pytest --platform=oh --mock-llm-device-port=18788
```

or:

```powershell
$env:BITFUN_MOCK_LLM_DEVICE_PORT = "18788"
```

Mock scenarios live in:

```text
mock_scenarios/
```

Select a scenario from the prompt sent to BitFun:

```text
[MOCK_SCENARIO]
id=tool_trace_demo
[/MOCK_SCENARIO]
```

For local validation without HDC port mapping:

```powershell
$env:BITFUN_MOCK_LLM_SKIP_HDC = "1"
python -m pytest -q tests/test_mock_llm_session.py tests/test_hdc_client.py tests/test_oh_start_command.py
```

On bash:

```bash
BITFUN_MOCK_LLM_SKIP_HDC=1 python3 -m pytest -q tests/test_mock_llm_session.py tests/test_hdc_client.py tests/test_oh_start_command.py
```

`BITFUN_TEST_LLM_BASE_URL`, `BITFUN_TEST_LLM_MODEL`, and
`BITFUN_TEST_LLM_API_KEY` are set in the pytest process before the `ui` fixture
starts BitFun. If the OH app needs these values as ability parameters, append
your actual `aa start` parameter syntax with `BITFUN_OH_APP_START_EXTRA_ARGS`.
The value supports these placeholders:

```text
{llm_base_url}
{llm_model}
{llm_api_key}
{bundle}
{module}
{ability}
```

Example:

```powershell
$env:BITFUN_OH_APP_START_EXTRA_ARGS = "--ps llmBaseUrl {llm_base_url} --ps llmModel {llm_model} --ps llmApiKey {llm_api_key}"
python -m pytest --platform=oh
```

If the full app start command needs to be replaced, use
`BITFUN_OH_APP_START_COMMAND` with the same placeholders.

The OH launcher uses:

```text
bundle:  com.develop.opensource.ohpcd.bitfun
module:  entry
ability: EntryAbility
```

Useful environment variables:

```powershell
$env:BITFUN_TEST_PLATFORM = "oh"
$env:HDC = "hdc"
$env:HDC_TARGET = "<optional-device-id>"
$env:BITFUN_OH_BUNDLE = "com.develop.opensource.ohpcd.bitfun"
$env:BITFUN_OH_MODULE = "entry"
$env:BITFUN_OH_ABILITY = "EntryAbility"
$env:BITFUN_OH_APP_STOP_COMMAND = "<optional custom hdc shell stop command>"
$env:BITFUN_OH_DEVTOOLS_SOCKET = "webview_devtools_remote_<pid>"
$env:BITFUN_OH_TARGET_HINT = "BitFun"
$env:BITFUN_KEEP_APP_OPEN = "1"
$env:BITFUN_MOCK_LLM_DEVICE_PORT = "18787"
$env:BITFUN_OH_APP_START_EXTRA_ARGS = "--ps llmBaseUrl {llm_base_url}"
```

If several WebViews are running, the OH adapter selects the CDP target whose
`title` or `url` contains `BitFun`. You can override it with
`BITFUN_OH_DEVTOOLS_SOCKET`.

Each test case cleans BitFun data before startup:

```text
bm clean -d -n com.develop.opensource.ohpcd.bitfun
```

During teardown each test case closes BitFun with:

```text
aa force-stop com.develop.opensource.ohpcd.bitfun
```

Set `BITFUN_KEEP_APP_OPEN=1` when you want to keep the app open after a failure
for manual inspection.

By default the OH adapter cleans app data before each test, waits 5 seconds
after startup, and clicks the startup system permission dialog's Allow button
when it appears. Useful overrides:

```powershell
$env:BITFUN_OH_CLEAN_APP_DATA = "0"
$env:BITFUN_OH_STARTUP_WAIT_SECONDS = "5"
$env:BITFUN_OH_PERMISSION_WAIT_SECONDS = "10"
$env:BITFUN_OH_APP_CLEAN_COMMAND = "bm clean -d -n com.develop.opensource.ohpcd.bitfun"
```
