[English](e2e-ready-run-guide.md) | **中文**

# BitFun Ready E2E 执行指南

本文档说明如何在另一台机器上执行当前可稳定通过的 10 条 E2E 用例。

当前这 10 条用例位于：

- [tests/test_system_e2e_ready.py](C:\Workspace\00_code\00_bitfun\bitfun_uitest\tests\test_system_e2e_ready.py)

当前会被单独放到另一个文件中的 3 条非 ready 用例位于：

- [tests/test_system_e2e_skipped.py](C:\Workspace\00_code\00_bitfun\bitfun_uitest\tests\test_system_e2e_skipped.py)

## 1. 适用场景

本指南默认你是在一台 Windows 主机上执行测试，并通过 `hdc` 驱动一台 OH 设备上的 BitFun。

这 10 条 ready E2E 的目标是：

- mock 会话链路
- 模型配置链路
- 工作区和会话基础链路
- 设置页持久化
- Agent / Skill 基础导航
- Shell 面板入口
- 错误恢复
- 冷启动到首个有效会话

## 2. 机器前提

目标机器至少需要满足以下条件：

1. 已安装 Python 3.10 或兼容版本
2. 已安装 `git`
3. 已安装 `hdc`
4. 已连接一台可用的 OH 设备
5. 已在 OH 设备上安装可测试的 BitFun 包
6. 该机器可以访问：
   - GitHub：用于拉取 `bitfun_uitest`
   - GitCode：用于拉取测试工程 `bitfun-test-project`

## 3. 拉取代码

```powershell
git clone https://github.com/azi44eo/BitFun_uitest.git
cd BitFun_uitest
```

如果你已经有代码仓，也可以直接更新：

```powershell
git pull
```

## 4. 安装依赖

```powershell
python -m pip install -r requirements.txt
```

## 5. 检查设备连接

先确认 `hdc` 可用：

```powershell
hdc list targets
```

如果有多台设备，建议显式指定目标：

```powershell
$env:HDC_TARGET = "<你的设备ID>"
```

如果 `hdc` 不在系统 PATH 中，也可以指定路径：

```powershell
$env:HDC = "hdc"
```

## 6. 检查 BitFun 包信息

默认测试使用这些 OH 启动参数：

- bundle: `com.develop.opensource.ohpcd.bitfun`
- module: `entry`
- ability: `EntryAbility`

如果你的测试包不同，需要先设置环境变量：

```powershell
$env:BITFUN_OH_BUNDLE = "com.develop.opensource.ohpcd.bitfun"
$env:BITFUN_OH_MODULE = "entry"
$env:BITFUN_OH_ABILITY = "EntryAbility"
```

## 7. 测试工程说明

`tests/test_system_e2e_ready.py` 中的工作区相关用例会自动准备测试工程。

默认使用的测试工程地址是：

```text
https://gitcode.com/weixin_53033691/bitfun-test-project.git
```

测试运行时会：

1. 在主机侧拉取或复用本地缓存目录 `.tmp_bitfun_test_project`
2. 把该工程同步到 OH 设备
3. 在 BitFun 中作为两个测试工作区打开

如果目标机器访问 GitCode 有问题，可以改用可访问的镜像地址：

```powershell
$env:BITFUN_TEST_PROJECT_GIT_URL = "https://gitcode.com/weixin_53033691/bitfun-test-project.git"
```

如果你已经提前准备好了 `.tmp_bitfun_test_project` 本地目录，测试也会优先复用该目录。

## 8. mock server 说明

这 10 条 ready E2E 会自动依赖仓库内置 mock LLM server。

pytest 启动后会自动：

1. 在主机侧启动 mock server
2. 自动建立 OH 设备到主机的反向端口映射
3. 在测试期间把 BitFun mock 模型配置到应用中

通常不需要你手工起 mock server。

默认设备侧端口为：

```text
18787
```

如果端口冲突，可以改：

```powershell
$env:BITFUN_MOCK_LLM_DEVICE_PORT = "18788"
```

或：

```powershell
python -m pytest -q tests/test_system_e2e_ready.py --mock-llm-device-port=18788
```

## 9. 推荐环境变量

推荐至少设置这些环境变量：

```powershell
$env:BITFUN_TEST_PLATFORM = "oh"
$env:HDC = "hdc"
$env:BITFUN_KEEP_APP_OPEN = "0"
```

如果要在失败后保留现场方便观察：

```powershell
$env:BITFUN_KEEP_APP_OPEN = "1"
```

如果你的机器上 ArkWeb 目标识别不稳定，也可以指定：

```powershell
$env:BITFUN_OH_TARGET_HINT = "BitFun"
```

## 10. 执行 ready E2E

直接执行：

```powershell
python -m pytest -q tests/test_system_e2e_ready.py
```

当前这条命令预期结果是：

- `10 passed`
- `0 failed`
- `0 skipped`

## 11. 执行非 ready E2E

这 3 条当前不计入 ready 集合，如果你要单独验证：

```powershell
python -m pytest -q tests/test_system_e2e_skipped.py
```

这 3 条当前依赖的产品能力还不稳定，可能会出现 `skip`。

## 12. 常见问题

### 12.1 `Mock server is not reachable from OH device`

先检查：

```powershell
hdc fport ls
```

如果端口映射异常，重新执行整条 pytest 命令即可，session fixture 会重新建立 reverse 端口。

### 12.2 GitCode 测试工程拉不下来

先检查目标机器是否能访问：

```powershell
git ls-remote https://gitcode.com/weixin_53033691/bitfun-test-project.git
```

如果不通：

1. 换可访问网络
2. 配置 `BITFUN_TEST_PROJECT_GIT_URL`
3. 或手工把工程准备到本地 `.tmp_bitfun_test_project`

### 12.3 设备上权限弹窗阻塞

测试驱动会自动点一次系统权限弹窗的“允许”。

如果设备首次安装环境特殊，仍然建议先手工打开一次 BitFun，完成系统权限授权后再跑 E2E。

### 12.4 想保留失败现场

```powershell
$env:BITFUN_KEEP_APP_OPEN = "1"
python -m pytest -q tests/test_system_e2e_ready.py
```

## 13. 建议执行顺序

在新机器首次接入时，建议按下面顺序执行：

1. 先跑 mock server 纯本地校验

```powershell
python -m pytest -q tests/test_mock_llm_session.py
```

2. 再跑 OH mock UI 基础校验

```powershell
python -m pytest -q tests/test_mock_llm_oh_demo.py
```

3. 最后跑 ready E2E

```powershell
python -m pytest -q tests/test_system_e2e_ready.py
```

## 14. 当前 ready E2E 列表

当前 ready 文件中的 10 条用例是：

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
