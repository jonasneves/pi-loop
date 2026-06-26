import pytest

from piloop import transport


def test_ssh_error_is_exception():
    assert issubclass(transport.SSHError, Exception)


@pytest.mark.asyncio
async def test_run_builds_connection_from_pi(monkeypatch):
    calls = {}

    class FakeResult:
        exit_status = 0
        stdout = "ok\n"
        stderr = ""

    class FakeConn:
        async def __aenter__(self): return self
        async def __aexit__(self, *a): return False
        async def run(self, command):
            calls["command"] = command
            return FakeResult()

    def fake_connect(host, username=None, known_hosts=None):
        calls["host"] = host
        calls["username"] = username
        return FakeConn()

    monkeypatch.setattr(transport.asyncssh, "connect", fake_connect)
    pi = {"ssh_host": "rpi5.local", "user": "pi"}
    out = await transport.run(pi, "uptime")
    assert out == "ok\n"
    assert calls["host"] == "rpi5.local"
    assert calls["username"] == "pi"
    assert calls["command"] == "uptime"


@pytest.mark.asyncio
async def test_run_raises_on_nonzero(monkeypatch):
    class FakeResult:
        exit_status = 1
        stdout = ""
        stderr = "boom\n"

    class FakeConn:
        async def __aenter__(self): return self
        async def __aexit__(self, *a): return False
        async def run(self, command): return FakeResult()

    monkeypatch.setattr(transport.asyncssh, "connect", lambda *a, **k: FakeConn())
    with pytest.raises(transport.SSHError):
        await transport.run({"ssh_host": "x", "user": "pi"}, "false")
