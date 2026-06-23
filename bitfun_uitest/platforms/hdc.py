from __future__ import annotations

import os
import subprocess


class HdcError(RuntimeError):
    pass


class HdcClient:
    def __init__(self, executable: str | None = None, target: str | None = None) -> None:
        self.executable = executable or os.environ.get("HDC", "hdc")
        self.target = target or os.environ.get("HDC_TARGET")

    def run(self, *args: str, check: bool = True, timeout: int = 30) -> str:
        command = [self.executable]
        if self.target:
            command.extend(["-t", self.target])
        command.extend(args)

        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
        output = (completed.stdout or "") + (completed.stderr or "")
        if check and completed.returncode != 0:
            raise HdcError(f"hdc failed ({completed.returncode}): {' '.join(command)}\n{output}")
        return output

    def shell(self, command: str, *, timeout: int = 30) -> str:
        return self.run("shell", command, timeout=timeout)

    def file_send(self, local: str, remote: str, *, timeout: int = 120) -> None:
        self.run("file", "send", local, remote, timeout=timeout)

    def fport(self, local_tcp_port: int, remote: str) -> None:
        self.run("fport", f"tcp:{local_tcp_port}", remote, timeout=10)

    def rport(self, device_tcp_port: int, host_tcp_port: int) -> None:
        self.run("rport", f"tcp:{device_tcp_port}", f"tcp:{host_tcp_port}", timeout=10)

    def remove_rport(self, device_tcp_port: int) -> None:
        rules = self.run("fport", "ls", check=False, timeout=10)
        needle = f"tcp:{device_tcp_port}"
        for line in rules.splitlines():
            parts = line.strip().split()
            if len(parts) < 4 or parts[-1] != "[Reverse]":
                continue
            if parts[1] != needle:
                continue
            self.run("fport", "rm", parts[1], parts[2], check=False, timeout=10)
