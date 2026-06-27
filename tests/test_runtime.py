import pytest

from piloop import runtime


def test_console_is_pure_registry_read():
    out = runtime.console("example")
    assert out["pi"] == "example"
    assert out["ble_name"] == "piloop-XXXX"
    assert "connect ble piloop-XXXX" in out["hint"]


@pytest.mark.asyncio
async def test_status_reports_reachable_uptime_load_and_shell(monkeypatch):
    async def fake_run(pi, command, check=True):
        if command.startswith("uptime"):
            return "up 2 hours, 5 minutes\n"
        if "loadavg" in command:
            return "0.14 0.09 0.05 1/123 4567\n"
        if "is-active" in command:
            return "active\n"
        return ""
    monkeypatch.setattr(runtime.T, "run", fake_run)
    out = await runtime.status("example")
    assert out["pi"] == "example"
    assert out["reachable"] is True
    assert out["uptime"] == "up 2 hours, 5 minutes"
    assert out["load"] == "0.14"
    assert out["ble_shell"] is True


@pytest.mark.asyncio
async def test_status_unreachable(monkeypatch):
    async def fake_run(pi, command, check=True):
        raise runtime.T.SSHError("no route")
    monkeypatch.setattr(runtime.T, "run", fake_run)
    out = await runtime.status("example")
    assert out["reachable"] is False
    assert out["uptime"] is None
    assert out["ble_shell"] is None


@pytest.mark.asyncio
async def test_exec_returns_output(monkeypatch):
    seen = {}
    async def fake_run(pi, command, check=True):
        seen["command"] = command
        seen["check"] = check
        return "hello\n"
    monkeypatch.setattr(runtime.T, "run", fake_run)
    out = await runtime.exec("example", "echo hello")
    assert out["pi"] == "example"
    assert out["command"] == "echo hello"
    assert out["output"] == "hello\n"
    assert seen["command"] == "echo hello"
    assert seen["check"] is False  # nonzero exit is a result, not an error


@pytest.mark.asyncio
async def test_reboot_issues_command(monkeypatch):
    seen = {}
    async def fake_run(pi, command, check=True):
        seen["command"] = command
        return ""
    monkeypatch.setattr(runtime.T, "run", fake_run)
    out = await runtime.reboot("example")
    assert out["rebooting"] is True
    assert "reboot" in seen["command"]
