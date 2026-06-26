from pathlib import Path

import pytest

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "agent"))
import loop  # noqa: E402


def test_parse_every():
    assert loop.parse_every("5m") == 300
    assert loop.parse_every("30s") == 30
    assert loop.parse_every("2h") == 7200


def test_load_config_validates(tmp_path):
    cfg_file = tmp_path / "config.toml"
    cfg_file.write_text(
        '[task]\nprompt = "do x"\ncadence = "interval"\nevery = "5m"\n'
        '[tools]\nallow = ["Bash", "Read"]\n')
    cfg = loop.load_config(cfg_file)
    assert cfg["prompt"] == "do x"
    assert cfg["cadence"] == "interval"
    assert cfg["every"] == "5m"
    assert cfg["allow"] == ["Bash", "Read"]


def test_load_config_rejects_bad_cadence(tmp_path):
    cfg_file = tmp_path / "config.toml"
    cfg_file.write_text('[task]\nprompt = "x"\ncadence = "hourly"\n[tools]\nallow = []\n')
    with pytest.raises(ValueError):
        loop.load_config(cfg_file)
