"""The Pi registry: one TOML per Pi, mirroring esp32-loop's boards/. Maps a
short handle (the filename stem) to its ssh_host + advertised ble_name."""
import tomllib
from pathlib import Path

PIS_DIR = Path(__file__).resolve().parent.parent / "pis"


def list_pis() -> list[str]:
    return sorted(p.stem for p in PIS_DIR.glob("*.toml"))


def load_pi(name: str) -> dict:
    path = PIS_DIR / f"{name}.toml"
    if not path.exists():
        raise SystemExit(
            f"unknown pi '{name}'. known: {', '.join(list_pis()) or '(none)'}"
        )
    data = tomllib.loads(path.read_text())
    pi = data["pi"]
    return {
        "name": name,
        "ssh_host": pi["ssh_host"],
        "user": pi.get("user", "pi"),
        "ble_name": pi["ble_name"],
        "notes": data.get("notes", {}).get("text", "").strip(),
    }
