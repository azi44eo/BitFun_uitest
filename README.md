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

The OH launcher uses:

```text
bundle:  com.huawei.BitFun
module:  entry
ability: EntryAbility
```

Useful environment variables:

```powershell
$env:BITFUN_TEST_PLATFORM = "oh"
$env:HDC = "hdc"
$env:HDC_TARGET = "<optional-device-id>"
$env:BITFUN_OH_BUNDLE = "com.huawei.BitFun"
$env:BITFUN_OH_MODULE = "entry"
$env:BITFUN_OH_ABILITY = "EntryAbility"
$env:BITFUN_OH_DEVTOOLS_SOCKET = "webview_devtools_remote_<pid>"
$env:BITFUN_OH_TARGET_HINT = "BitFun"
```

If several WebViews are running, the OH adapter selects the CDP target whose
`title` or `url` contains `BitFun`. You can override it with
`BITFUN_OH_DEVTOOLS_SOCKET`.

