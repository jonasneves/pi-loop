import pytest

mcp_mod = pytest.importorskip("piloop.mcp")


@pytest.mark.asyncio
async def test_console_tool_returns_hint():
    out = await mcp_mod._console_impl("example")
    assert "connect ble piloop-XXXX" in out


@pytest.mark.asyncio
async def test_exec_tool_returns_output(monkeypatch):
    async def fake_exec(pi, command):
        return {"pi": pi, "command": command, "output": "ok\n"}
    monkeypatch.setattr(mcp_mod.R, "exec", fake_exec)
    out = await mcp_mod.exec("example", "echo ok")
    assert out["output"] == "ok\n"
