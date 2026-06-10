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
```

If several WebViews are running, the OH adapter selects the CDP target whose
`title` or `url` contains `BitFun`. You can override it with
`BITFUN_OH_DEVTOOLS_SOCKET`.

Each test case starts BitFun before running and closes it during teardown with:

```text
aa force-stop com.develop.opensource.ohpcd.bitfun
bm clean -d -n com.develop.opensource.ohpcd.bitfun
```

Set `BITFUN_KEEP_APP_OPEN=1` when you want to keep the app open after a failure
for manual inspection. In that mode teardown also skips the data cleanup.

By default the OH adapter cleans app data before each test, waits 5 seconds
after startup, and clicks the startup system permission dialog's Allow button
when it appears. Useful overrides:

```powershell
$env:BITFUN_OH_CLEAN_APP_DATA = "0"
$env:BITFUN_OH_STARTUP_WAIT_SECONDS = "5"
$env:BITFUN_OH_PERMISSION_WAIT_SECONDS = "10"
$env:BITFUN_OH_APP_CLEAN_COMMAND = "bm clean -d -n com.develop.opensource.ohpcd.bitfun"
```
