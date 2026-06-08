from __future__ import annotations

import json
import threading
from typing import Any


class CdpError(RuntimeError):
    pass


class CdpClient:
    def __init__(self, websocket_url: str, timeout: float = 10.0) -> None:
        self.websocket_url = websocket_url
        self.timeout = timeout
        self._next_id = 0
        self._lock = threading.Lock()
        self._socket: Any | None = None

    def connect(self) -> None:
        try:
            import websocket
        except ModuleNotFoundError as error:
            raise CdpError(
                "Missing dependency 'websocket-client'. Install with: "
                "python -m pip install -r requirements.txt"
            ) from error

        self._socket = websocket.create_connection(self.websocket_url, timeout=self.timeout)
        self.call("Runtime.enable")

    def close(self) -> None:
        if self._socket is not None:
            self._socket.close()
            self._socket = None

    def call(self, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        if self._socket is None:
            raise CdpError("CDP socket is not connected")

        with self._lock:
            self._next_id += 1
            request_id = self._next_id
            self._socket.send(json.dumps({"id": request_id, "method": method, "params": params or {}}))

            while True:
                message = json.loads(self._socket.recv())
                if message.get("id") != request_id:
                    continue
                if "error" in message:
                    raise CdpError(f"CDP {method} failed: {message['error']}")
                return message.get("result", {})

    def evaluate(self, expression: str) -> Any:
        result = self.call(
            "Runtime.evaluate",
            {
                "expression": expression,
                "awaitPromise": True,
                "returnByValue": True,
                "userGesture": True,
            },
        )
        if "exceptionDetails" in result:
            raise CdpError(f"JavaScript evaluation failed: {result['exceptionDetails']}")
        return result.get("result", {}).get("value")

