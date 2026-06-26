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
