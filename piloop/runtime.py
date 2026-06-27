"""The verbs — data in, data out, never print. CLI and MCP are the only
formatting layers, so this one source serves both (esp32-loop's rule). Each verb
takes a pi *handle*, resolves it through the registry, and runs over SSH.

The Pi is a controllable arm, not a brain: these verbs are the WiFi control
surface the external brain drives. `exec` is the core primitive (run a command,
get output — esp32-loop's `send`). The `console` verb is the deliberate
asymmetry: a pure registry read handing you the ble_name to type into tab-device
when WiFi is down. The host never speaks BLE — tab-device owns that channel."""
from piloop import pis as B
from piloop import transport as T

# The BLE shell unit: bridge.py forks /bin/bash under a PTY and mirrors it to
# Nordic UART. `status` reports whether that out-of-band channel is up.
SHELL_SERVICE = "piloop-bridge.service"


async def status(pi: str) -> dict:
    p = B.load_pi(pi)
    out = {"pi": pi, "ssh_host": p["ssh_host"], "reachable": False,
           "uptime": None, "load": None, "ble_shell": None}
    try:
        upt = await T.run(p, "uptime -p", check=False)
        out["reachable"] = True
        out["uptime"] = upt.strip() or None
        load = await T.run(p, "cat /proc/loadavg", check=False)
        out["load"] = load.split()[0] if load.strip() else None
        active = await T.run(p, f"systemctl is-active {SHELL_SERVICE}", check=False)
        out["ble_shell"] = active.strip() == "active"
    except T.SSHError:
        pass  # unreachable — absence is the answer, not an error
    return out


async def exec(pi: str, command: str) -> dict:
    """Run a command on the Pi over SSH and return its output. The brain's core
    WiFi control primitive — mirrors esp32-loop's `send`. Nonzero exit is not an
    error here: the output (incl. stderr-less stdout) is the result the caller
    reads. Connection failure still raises SSHError."""
    p = B.load_pi(pi)
    output = await T.run(p, command, check=False)
    return {"pi": pi, "command": command, "output": output}


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
