import pytest

from piloop import pis


def test_list_pis_finds_example():
    assert "example" in pis.list_pis()


def test_load_pi_returns_schema():
    p = pis.load_pi("example")
    assert p["name"] == "example"
    assert p["ssh_host"] == "example.local"
    assert p["user"] == "pi"
    assert p["ble_name"] == "piloop-XXXX"
    assert "notes" in p


def test_load_unknown_pi_exits():
    with pytest.raises(SystemExit):
        pis.load_pi("nope")
