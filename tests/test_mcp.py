import pytest

mcp_mod = pytest.importorskip("piloop.mcp")


@pytest.mark.asyncio
async def test_console_tool_returns_hint():
    out = await mcp_mod._console_impl("example")
    assert "connect ble piloop-XXXX" in out
