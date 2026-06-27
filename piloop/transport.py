"""Host→Pi transport. SSH (asyncssh) carries the high-bandwidth ops — exec,
reboot, shell. Discovery finds Pis two ways: mDNS (an _ssh._tcp sweep) and a BLE
advert scan (the bridge's NUS advertisement). The BLE shell itself is NOT here —
tab-device owns that channel; the host only ever names the ble_name."""
import asyncio

import asyncssh


class SSHError(Exception):
    """A command exited nonzero, or the connection failed."""


async def run(pi: dict, command: str, *, check: bool = True) -> str:
    try:
        async with asyncssh.connect(
            pi["ssh_host"], username=pi["user"], known_hosts=None
        ) as conn:
            result = await conn.run(command)
    except (OSError, asyncssh.Error) as e:
        raise SSHError(f"{pi['ssh_host']}: {e}")
    if check and result.exit_status != 0:
        raise SSHError(f"{pi['ssh_host']}: `{command}` exited {result.exit_status}: "
                       f"{result.stderr.strip()}")
    return result.stdout


async def discover_mdns(seconds: float = 3) -> list[dict]:
    """Pis advertising _ssh._tcp on the LAN. Best-effort; empty if none."""
    from zeroconf import ServiceBrowser, Zeroconf

    found: dict[str, dict] = {}

    class _Listener:
        def add_service(self, zc, type_, name):
            info = zc.get_service_info(type_, name)
            if info and info.parsed_addresses():
                found[name] = {"host": info.server.rstrip("."),
                               "address": info.parsed_addresses()[0]}
        def update_service(self, *a): pass
        def remove_service(self, *a): pass

    zc = Zeroconf()
    try:
        ServiceBrowser(zc, "_ssh._tcp.local.", _Listener())
        await asyncio.sleep(seconds)
    finally:
        zc.close()
    return list(found.values())


async def scan_ble(seconds: float = 6, name: str | None = None) -> list[dict]:
    """BLE advert scan — is a bridge advertising? Mirrors esp32-loop's scan."""
    from bleak import BleakScanner

    found = await BleakScanner.discover(timeout=seconds, return_adv=True)
    rows = [
        {"rssi": adv.rssi, "name": adv.local_name or "", "address": addr}
        for addr, (_dev, adv) in found.items()
        if not name or (adv.local_name and name.lower() in adv.local_name.lower())
    ]
    rows.sort(key=lambda r: r["rssi"], reverse=True)
    return rows
