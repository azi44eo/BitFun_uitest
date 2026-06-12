from __future__ import annotations

import subprocess
from types import SimpleNamespace

from bitfun_uitest.platforms.hdc import HdcClient


def test_hdc_rport_command_direction_and_cleanup(monkeypatch):
    calls: list[list[str]] = []

    def fake_run(command, **kwargs):
        calls.append(command)
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)

    client = HdcClient(executable="hdc", target="device-1")
    client.rport(device_tcp_port=18787, host_tcp_port=43001)
    client.remove_rport(device_tcp_port=18787)

    assert calls == [
        ["hdc", "-t", "device-1", "rport", "tcp:18787", "tcp:43001"],
        ["hdc", "-t", "device-1", "rport", "rm", "tcp:18787"],
    ]
