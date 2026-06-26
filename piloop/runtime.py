"""The verbs — data in, data out, never print. CLI and MCP are the only
formatting layers, so this one source serves both (esp32-loop's rule). Each verb
takes a pi *handle*, resolves it through the registry, and runs over SSH.

The console verb is the deliberate asymmetry: it's a pure registry read that
hands you the ble_name to type into tab-device. The host never speaks BLE — the
console lives there, and tab-device is already its client."""
from pathlib import Path

from piloop import pis as B
from piloop import transport as T

AGENT_SERVICE = "piloop-agent.service"
AGENT_DEST = "/opt/piloop/agent"


async def status(pi: str) -> dict:
    p = B.load_pi(pi)
    out = {"pi": pi, "ssh_host": p["ssh_host"], "reachable": False,
           "agent_active": None, "last_tick": None}
    try:
        active = await T.run(p, f"systemctl is-active {AGENT_SERVICE}", check=False)
        out["reachable"] = True
        out["agent_active"] = active.strip() == "active"
        tick = await T.run(
            p, f"systemctl show -p ActiveEnterTimestamp --value {AGENT_SERVICE}",
            check=False)
        out["last_tick"] = tick.strip() or None
    except T.SSHError:
        pass  # unreachable — absence is the answer, not an error
    return out


async def deploy(pi: str, agent_dir: Path) -> dict:
    """rsync the agent dir to the Pi and restart its service. agent_dir is the
    repo's agent/ — loop.py + config.toml. Uses ssh as rsync's transport."""
    p = B.load_pi(pi)
    target = f"{p['user']}@{p['ssh_host']}:{AGENT_DEST}/"
    import asyncio
    proc = await asyncio.create_subprocess_exec(
        "rsync", "-az", "--delete", f"{Path(agent_dir)}/", target,
        "-e", "ssh -o StrictHostKeyChecking=accept-new")
    if await proc.wait() != 0:
        raise T.SSHError(f"{p['ssh_host']}: rsync failed")
    await T.run(p, f"sudo systemctl restart {AGENT_SERVICE}")
    return {"pi": pi, "synced": True}


async def logs(pi: str):
    p = B.load_pi(pi)
    async for line in T.stream(p, f"journalctl -fu {AGENT_SERVICE} -n 40 -o cat"):
        yield line


def console(pi: str) -> dict:
    p = B.load_pi(pi)
    return {"pi": pi, "ble_name": p["ble_name"],
            "hint": f"in tab-device, run: connect ble {p['ble_name']}"}


async def reboot(pi: str) -> dict:
    p = B.load_pi(pi)
    await T.run(p, "sudo reboot", check=False)  # connection drops as it goes down
    return {"pi": pi, "rebooting": True}


async def scan(seconds: float = 3, ble: bool = False) -> dict:
    out = {"mdns": await T.discover_mdns(seconds), "ble": []}
    if ble:
        out["ble"] = await T.scan_ble(seconds, "piloop")
    return out
