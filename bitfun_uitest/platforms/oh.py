from __future__ import annotations

import json
import os
import re
import socket
import time
import urllib.request
from dataclasses import dataclass
from typing import Any

from bitfun_uitest.platforms.cdp import CdpClient, CdpError
from bitfun_uitest.platforms.dom import DomTestIdMixin
from bitfun_uitest.platforms.hdc import HdcClient, HdcError


@dataclass(frozen=True)
class OhAppConfig:
    bundle: str = "com.develop.opensource.ohpcd.bitfun"
    module: str = "entry"
    ability: str = "EntryAbility"
    target_hint: str = "BitFun"
    startup_wait_seconds: float = 5.0
    devtools_wait_seconds: float = 20.0
    clean_app_data: bool = True
    permission_wait_seconds: float = 10.0

    @classmethod
    def from_env(cls) -> "OhAppConfig":
        return cls(
            bundle=os.environ.get("BITFUN_OH_BUNDLE", cls.bundle),
            module=os.environ.get("BITFUN_OH_MODULE", cls.module),
            ability=os.environ.get("BITFUN_OH_ABILITY", cls.ability),
            target_hint=os.environ.get("BITFUN_OH_TARGET_HINT", cls.target_hint),
            startup_wait_seconds=float(os.environ.get("BITFUN_OH_STARTUP_WAIT_SECONDS", "5")),
            devtools_wait_seconds=float(os.environ.get("BITFUN_OH_DEVTOOLS_WAIT_SECONDS", "20")),
            clean_app_data=_env_bool("BITFUN_OH_CLEAN_APP_DATA", default=True),
            permission_wait_seconds=float(os.environ.get("BITFUN_OH_PERMISSION_WAIT_SECONDS", "10")),
        )


class ArkWebDevtoolsResolver:
    SOCKET_PATTERN = re.compile(r"(?:@)?((?:webview|arkweb)[\w.-]*devtools[\w.-]*remote[\w.-]*(?:_\d+)?)")

    def __init__(self, hdc: HdcClient) -> None:
        self.hdc = hdc

    def wait_for_socket(self, timeout: float, app_pid: str | None = None) -> str:
        explicit = os.environ.get("BITFUN_OH_DEVTOOLS_SOCKET")
        if explicit:
            return self._normalize_socket(explicit)

        deadline = time.monotonic() + timeout
        last_candidates: list[str] = []
        while time.monotonic() < deadline:
            candidates = self.list_sockets()
            last_candidates = candidates
            if app_pid:
                pid_matches = [item for item in candidates if item.endswith(f"_{app_pid}")]
                if pid_matches:
                    return pid_matches[0]
            if candidates:
                return candidates[0]
            time.sleep(0.3)

        raise HdcError(
            "No ArkWeb/WebView DevTools socket found. "
            f"Last candidates: {last_candidates}. Ensure WebView debugging is enabled."
        )

    def list_sockets(self) -> list[str]:
        proc_net_unix = self.hdc.shell("cat /proc/net/unix", timeout=10)
        found: list[str] = []
        for line in proc_net_unix.splitlines():
            match = self.SOCKET_PATTERN.search(line)
            if match:
                socket_name = self._normalize_socket(match.group(1))
                if socket_name not in found:
                    found.append(socket_name)
        return found

    @staticmethod
    def _normalize_socket(socket_name: str) -> str:
        return socket_name.removeprefix("@").removeprefix("localabstract:")


class OpenHarmonyDriver(DomTestIdMixin):
    def __init__(self, hdc: HdcClient, app: OhAppConfig) -> None:
        self.hdc = hdc
        self.app = app
        self.fixed_cdp_port = int(os.environ["BITFUN_OH_CDP_PORT"]) if os.environ.get("BITFUN_OH_CDP_PORT") else None
        self._cdp: CdpClient | None = None

    @classmethod
    def from_env(cls) -> "OpenHarmonyDriver":
        return cls(HdcClient(), OhAppConfig.from_env())

    def start(self) -> None:
        if self.app.clean_app_data:
            self._reset_app_data()
        self._start_app()
        time.sleep(self.app.startup_wait_seconds)
        self._allow_startup_permission_dialog()
        self._connect_devtools()
        self.wait_for_test_id("app-layout", timeout=30)

    def close(self) -> None:
        try:
            if self._cdp:
                self._cdp.close()
        finally:
            self._cdp = None
            if not _truthy_env("BITFUN_KEEP_APP_OPEN"):
                self._stop_app()
                if self.app.clean_app_data:
                    self._clean_app_data()

    def evaluate(self, expression: str) -> Any:
        if self._cdp is None:
            raise CdpError("OpenHarmonyDriver.start() must be called before evaluate()")
        return self._cdp.evaluate(expression)

    def _start_app(self) -> None:
        start_command = os.environ.get("BITFUN_OH_APP_START_COMMAND")
        if start_command:
            self.hdc.shell(start_command, timeout=60)
            return

        self.hdc.shell(
            f"aa start -b {self.app.bundle} -m {self.app.module} -a {self.app.ability}",
            timeout=60,
        )

    def _stop_app(self) -> None:
        stop_command = os.environ.get("BITFUN_OH_APP_STOP_COMMAND")
        if stop_command:
            self.hdc.run("shell", stop_command, check=False, timeout=30)
            return

        self.hdc.run("shell", f"aa force-stop {self.app.bundle}", check=False, timeout=30)

    def _reset_app_data(self) -> None:
        self._stop_app()
        self._clean_app_data()

    def _clean_app_data(self) -> None:
        clean_command = os.environ.get("BITFUN_OH_APP_CLEAN_COMMAND")
        if clean_command:
            self.hdc.run("shell", clean_command, check=False, timeout=60)
            return

        self.hdc.run("shell", f"bm clean -d -n {self.app.bundle}", check=False, timeout=60)

    def _allow_startup_permission_dialog(self) -> None:
        deadline = time.monotonic() + self.app.permission_wait_seconds
        while time.monotonic() < deadline:
            target = self._find_permission_allow_button()
            if target is not None:
                x, y = target
                self.hdc.run("shell", f"uitest uiInput click {x} {y}", check=False, timeout=10)
                time.sleep(0.5)
                return
            time.sleep(0.3)

    def _find_permission_allow_button(self) -> tuple[int, int] | None:
        output = self.hdc.run("shell", "uitest dumpLayout", check=False, timeout=10)
        match = re.search(r"DumpLayout saved to:(\S+)", output)
        if not match:
            return None

        try:
            raw_layout = self.hdc.shell(f"cat {match.group(1)}", timeout=10)
            layout = json.loads(raw_layout)
        except Exception:
            return None

        for node in _walk_layout_nodes(layout):
            attrs = node.get("attributes", {})
            labels = {
                str(attrs.get(name, "")).strip()
                for name in ("text", "originalText", "description")
            }
            if labels.intersection({"\u5141\u8bb8", "Allow"}):
                return _bounds_center(attrs.get("bounds", ""))
        return None

    def _connect_devtools(self) -> None:
        explicit_socket = os.environ.get("BITFUN_OH_DEVTOOLS_SOCKET")
        resolver = ArkWebDevtoolsResolver(self.hdc)

        if explicit_socket:
            socket_name = ArkWebDevtoolsResolver._normalize_socket(explicit_socket)
            port = self._forward_socket(socket_name)
            websocket_url = self._discover_websocket_url(port)
            self._cdp = CdpClient(websocket_url)
            self._cdp.connect()
            return

        deadline = time.monotonic() + self.app.devtools_wait_seconds
        last_error: Exception | None = None
        while time.monotonic() < deadline:
            for socket_name in resolver.list_sockets():
                try:
                    port = self._forward_socket(socket_name)
                    websocket_url = self._discover_websocket_url(port)
                    self._cdp = CdpClient(websocket_url)
                    self._cdp.connect()
                    return
                except Exception as error:
                    last_error = error
            time.sleep(0.3)

        raise HdcError(f"Unable to connect BitFun ArkWeb DevTools target: {last_error}")

    def _forward_socket(self, socket_name: str) -> int:
        port = self.fixed_cdp_port if self.fixed_cdp_port is not None else _free_tcp_port()
        self.hdc.fport(port, f"localabstract:{socket_name}")
        return port

    def _discover_websocket_url(self, port: int) -> str:
        try:
            targets = _http_json(port, "/json/list")
        except Exception:
            targets = _http_json(port, "/json")
        if not isinstance(targets, list) or not targets:
            raise CdpError("No ArkWeb CDP targets returned")

        chosen = self._choose_target(targets)
        raw_url = chosen.get("webSocketDebuggerUrl")
        if not raw_url:
            raise CdpError(f"Chosen CDP target does not expose webSocketDebuggerUrl: {chosen}")
        return re.sub(r"^ws://[^/]+", f"ws://127.0.0.1:{port}", raw_url)

    def _choose_target(self, targets: list[dict[str, Any]]) -> dict[str, Any]:
        hint = self.app.target_hint.lower()
        for target in targets:
            haystack = f"{target.get('title', '')} {target.get('url', '')}".lower()
            if hint and hint in haystack:
                return target
        for target in targets:
            haystack = f"{target.get('title', '')} {target.get('url', '')}".lower()
            if "tauri://localhost" in haystack:
                return target
        raise CdpError(f"No BitFun CDP target found. Targets: {json.dumps(targets, ensure_ascii=False)}")


def _free_tcp_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _http_json(port: int, path: str) -> Any:
    url = f"http://127.0.0.1:{port}{path}"
    with urllib.request.urlopen(url, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def _truthy_env(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes", "on"}


def _env_bool(name: str, *, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    normalized = raw.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    return default


def _walk_layout_nodes(node: dict[str, Any]) -> list[dict[str, Any]]:
    nodes = [node]
    for child in node.get("children", []) or []:
        if isinstance(child, dict):
            nodes.extend(_walk_layout_nodes(child))
    return nodes


def _bounds_center(bounds: str) -> tuple[int, int] | None:
    match = re.match(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", bounds)
    if not match:
        return None
    left, top, right, bottom = (int(value) for value in match.groups())
    return ((left + right) // 2, (top + bottom) // 2)
