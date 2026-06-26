from piloop import cli


def test_cmd_console_prints_hint(monkeypatch, capsys):
    args = type("A", (), {"pi": "example"})()
    rc = cli.cmd_console(args)
    out = capsys.readouterr().out
    assert rc == 0
    assert "connect ble piloop-XXXX" in out


def test_cmd_pis_lists(monkeypatch, capsys):
    rc = cli.cmd_pis(type("A", (), {})())
    out = capsys.readouterr().out
    assert rc == 0
    assert "example" in out
