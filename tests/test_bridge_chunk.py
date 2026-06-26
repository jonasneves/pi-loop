import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "bridge"))
import bridge  # noqa: E402


def test_chunk_respects_mtu():
    data = b"x" * 55
    chunks = list(bridge.chunk(data, 20))
    assert chunks == [b"x" * 20, b"x" * 20, b"x" * 15]


def test_chunk_empty():
    assert list(bridge.chunk(b"", 20)) == []


def test_serial_suffix_extracts_last_4_uppercase():
    assert bridge.serial_suffix("Serial\t: 0000000012ab34cd\n") == "34CD"


def test_serial_suffix_missing_returns_0000():
    assert bridge.serial_suffix("") == "0000"


def test_serial_suffix_no_serial_line():
    assert bridge.serial_suffix("Model\t: Raspberry Pi 4\nRevision\t: c03111\n") == "0000"
