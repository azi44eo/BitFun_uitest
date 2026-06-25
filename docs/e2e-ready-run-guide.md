[中文](e2e-ready-run-guide-CN.md) | **English**

# BitFun Ready E2E Run Guide

This document explains how to run the current 10 stable ready E2E cases on another machine.

The 10 ready E2E tests live in:

- [tests/test_system_e2e_ready.py](C:\Workspace\00_code\00_bitfun\bitfun_uitest\tests\test_system_e2e_ready.py)

The 3 non-ready cases that were split out live in:

- [tests/test_system_e2e_skipped.py](C:\Workspace\00_code\00_bitfun\bitfun_uitest\tests\test_system_e2e_skipped.py)

## 1. Scope

This guide assumes:

- a Windows host machine
- `hdc` driving an OH device
- BitFun installed on the OH device

The ready E2E set covers:

- mock conversation flow
- model configuration
- workspace and session basics
- settings persistence
- agent / skill navigation
- shell panel entry
- error recovery
- cold start bootstrap

## 2. Machine Prerequisites

The target machine should have:

1. Python 3.10 or a compatible version
2. `git`
3. `hdc`
4. one reachable OH device
5. a testable BitFun build installed on that device
6. network access to:
   - GitHub for this test repo
   - GitCode for the test workspace fixture repo

## 3. Clone the Repo

```powershell
git clone https://github.com/azi44eo/BitFun_uitest.git
cd BitFun_uitest
```

Or update an existing checkout:

```powershell
git pull
```

## 4. Install Dependencies

```powershell
python -m pip install -r requirements.txt
```

## 5. Verify Device Connectivity

Check that `hdc` can see your device:

```powershell
hdc list targets
```

If you have multiple devices, set one explicitly:

```powershell
$env:HDC_TARGET = "<your-device-id>"
```

If `hdc` is not on PATH, point to it explicitly:

```powershell
$env:HDC = "hdc"
```

## 6. Verify BitFun Package Info

The default OH launch values are:

- bundle: `com.develop.opensource.ohpcd.bitfun`
- module: `entry`
- ability: `EntryAbility`

If your package differs, set:

```powershell
$env:BITFUN_OH_BUNDLE = "com.develop.opensource.ohpcd.bitfun"
$env:BITFUN_OH_MODULE = "entry"
$env:BITFUN_OH_ABILITY = "EntryAbility"
```

## 7. Test Workspace Fixture

The workspace-related ready E2E cases automatically prepare a test project.

The default fixture repo is:

```text
https://gitcode.com/weixin_53033691/bitfun-test-project.git
```

During the run, the fixture will:

1. clone or reuse `.tmp_bitfun_test_project` on the host
2. sync it to the OH device
3. open it in BitFun as two test workspaces

If GitCode access is restricted on that machine, override the URL:

```powershell
$env:BITFUN_TEST_PROJECT_GIT_URL = "https://gitcode.com/weixin_53033691/bitfun-test-project.git"
```

If `.tmp_bitfun_test_project` already exists locally, the fixture will reuse it.

## 8. Mock Server Behavior

The ready E2E suite uses the built-in mock LLM server in this repo.

Pytest will automatically:

1. start the mock server on the host
2. create reverse port mapping for the OH device
3. configure the BitFun mock model inside the app

You do not normally need to start the mock server manually.

The default device-side port is:

```text
18787
```

If needed, change it with:

```powershell
$env:BITFUN_MOCK_LLM_DEVICE_PORT = "18788"
```

or:

```powershell
python -m pytest -q tests/test_system_e2e_ready.py --mock-llm-device-port=18788
```

## 9. Recommended Environment Variables

At minimum, set:

```powershell
$env:BITFUN_TEST_PLATFORM = "oh"
$env:HDC = "hdc"
$env:BITFUN_KEEP_APP_OPEN = "0"
```

If you want to keep the app open after a failure:

```powershell
$env:BITFUN_KEEP_APP_OPEN = "1"
```

If CDP target detection is noisy on that machine:

```powershell
$env:BITFUN_OH_TARGET_HINT = "BitFun"
```

## 10. Run the Ready E2E Suite

Run:

```powershell
python -m pytest -q tests/test_system_e2e_ready.py
```

The current expected result is:

- `10 passed`
- `0 failed`
- `0 skipped`

## 11. Run the Non-Ready E2E Suite

If you want to check the non-ready cases separately:

```powershell
python -m pytest -q tests/test_system_e2e_skipped.py
```

These 3 tests still depend on unstable product-side behavior and may skip.

## 12. Common Problems

### 12.1 `Mock server is not reachable from OH device`

Check:

```powershell
hdc fport ls
```

Then rerun pytest. The session fixture will rebuild the reverse mapping.

### 12.2 The GitCode test repo cannot be cloned

Check connectivity:

```powershell
git ls-remote https://gitcode.com/weixin_53033691/bitfun-test-project.git
```

If that fails:

1. switch to a reachable network
2. override `BITFUN_TEST_PROJECT_GIT_URL`
3. or pre-create `.tmp_bitfun_test_project` locally

### 12.3 A device permission dialog blocks startup

The OH driver attempts to click the startup Allow button automatically.

If the environment is brand new, it is still a good idea to open BitFun once manually and complete any system permission prompts before running the E2E suite.

### 12.4 Keep the failed app state open

```powershell
$env:BITFUN_KEEP_APP_OPEN = "1"
python -m pytest -q tests/test_system_e2e_ready.py
```

## 13. Recommended First-Time Execution Order

On a new machine, use this order:

1. mock server local validation

```powershell
python -m pytest -q tests/test_mock_llm_session.py
```

2. OH mock UI validation

```powershell
python -m pytest -q tests/test_mock_llm_oh_demo.py
```

3. ready E2E validation

```powershell
python -m pytest -q tests/test_system_e2e_ready.py
```

## 14. Current Ready E2E List

The 10 ready E2E tests are:

1. `test_e2e_001_mock_session_interaction`
2. `test_e2e_002_model_configuration_lifecycle`
3. `test_e2e_003_session_management_lifecycle`
4. `test_e2e_004_workspace_and_session_binding`
5. `test_e2e_006_settings_navigation_and_persistence`
6. `test_e2e_007_agent_and_skill_discovery_flow`
7. `test_e2e_011_skills_tab_navigation`
8. `test_e2e_012_shell_panel_entry`
9. `test_e2e_009_session_error_recovery`
10. `test_e2e_010_cold_start_to_productive_session`
