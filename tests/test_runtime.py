import pytest

from piloop import runtime


def test_console_is_pure_registry_read():
    out = runtime.console("example")
    assert out["pi"] == "example"
    assert out["ble_name"] == "piloop-XXXX"
    assert "connect ble piloop-XXXX" in out["hint"]


@pytest.mark.asyncio
async def test_status_reports_reachable_and_agent(monkeypatch):
    async def fake_run(pi, command, check=True):
        if "is-active" in command:
            return "active\n"
        if "show" in command:  # last tick from journald
            return "Tue 2026-06-26 10:00:01\n"
        return ""
    monkeypatch.setattr(runtime.T, "run", fake_run)
    out = await runtime.status("example")
    assert out["pi"] == "example"
    assert out["reachable"] is True
    assert out["agent_active"] is True
    assert out["last_tick"]


@pytest.mark.asyncio
async def test_status_unreachable(monkeypatch):
    async def fake_run(pi, command, check=True):
        raise runtime.T.SSHError("no route")
    monkeypatch.setattr(runtime.T, "run", fake_run)
    out = await runtime.status("example")
    assert out["reachable"] is False
    assert out["agent_active"] is None


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
