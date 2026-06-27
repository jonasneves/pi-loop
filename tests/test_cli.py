from piloop import cli


def test_cmd_console_prints_hint(monkeypatch, capsys):
    args = type("A", (), {"pi": "example"})()
    rc = cli.cmd_console(args)
    out = capsys.readouterr().out
    assert rc == 0
    assert "connect ble piloop-XXXX" in out


def test_cmd_exec_prints_output(monkeypatch, capsys):
    async def fake_exec(pi, command):
        return {"pi": pi, "command": command, "output": "hi\n"}
    monkeypatch.setattr(cli.R, "exec", fake_exec)
    args = type("A", (), {"pi": "example", "command": ["echo", "hi"]})()
    rc = cli.cmd_exec(args)
    out = capsys.readouterr().out
    assert rc == 0
    assert out == "hi\n"


def test_cmd_exec_empty_command_is_usage_error(capsys):
    args = type("A", (), {"pi": "example", "command": []})()
    rc = cli.cmd_exec(args)
    assert rc == 2
    assert "usage" in capsys.readouterr().out


def test_cmd_pis_lists(monkeypatch, capsys):
    rc = cli.cmd_pis(type("A", (), {})())
    out = capsys.readouterr().out
    assert rc == 0
    assert "example" in out
