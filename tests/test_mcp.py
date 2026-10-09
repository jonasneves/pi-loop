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


def test_relay_refuses_to_start_without_an_allow_list(monkeypatch):
    import pytest
    from piloop import mcp as M
    monkeypatch.setattr("sys.argv", ["piloop-mcp", "--relay"])
    monkeypatch.delenv("PILOOP_RELAY_ALLOW", raising=False)
    with pytest.raises(SystemExit) as exc:
        M.main()
    assert "PILOOP_RELAY_ALLOW" in str(exc.value)


def test_relay_allow_list_parses_logins():
    from piloop import mcp as M
    assert M.relay_allow({"PILOOP_RELAY_ALLOW": " jonasneves , "}) == ["jonasneves"]
    assert M.relay_allow({}) == []
