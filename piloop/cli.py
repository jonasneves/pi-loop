"""piloop — operate Raspberry Pis that run an agent loop on themselves.

Each verb is a thin renderer over runtime's data. The console verb prints the
ble_name to hand to tab-device; everything else is SSH."""
import argparse
import asyncio
from pathlib import Path

from piloop import pis as B
from piloop import runtime as R
from piloop import transport as T

REPO_AGENT_DIR = Path(__file__).resolve().parent.parent / "agent"


def cmd_pis(args) -> int:
    names = B.list_pis()
    if not names:
        print("no pis registered. Add pis/<name>.toml (see pis/example.toml).")
        return 0
    for n in names:
        p = B.load_pi(n)
        print(f"  {n:<16} {p['ssh_host']:<22} ble={p['ble_name']}")
    return 0


def cmd_scan(args) -> int:
    out = asyncio.run(R.scan(args.seconds, args.ble))
    if not out["mdns"] and not out["ble"]:
        print("nothing found (mDNS sweep + BLE scan empty).")
        return 0
    for r in out["mdns"]:
        print(f"  mdns  {r['host']:<24} {r['address']}")
    for r in out["ble"]:
        print(f"  ble   {r['name']:<24} {r['address']}  rssi={r['rssi']}")
    return 0


def cmd_status(args) -> int:
    out = asyncio.run(R.status(args.pi))
    if not out["reachable"]:
        print(f"{args.pi} ({out['ssh_host']}): unreachable")
        return 1
    agent = "up" if out["agent_active"] else "down"
    print(f"{args.pi} ({out['ssh_host']}): reachable  agent={agent}  "
          f"last-tick={out['last_tick'] or '—'}")
    return 0


def cmd_deploy(args) -> int:
    try:
        R_out = asyncio.run(R.deploy(args.pi, REPO_AGENT_DIR))
    except T.SSHError as e:
        print(str(e))
        return 1
    print(f"{args.pi}: deployed agent/ and restarted the loop.")
    return 0


def cmd_logs(args) -> int:
    async def go():
        async for line in R.logs(args.pi):
            print(line)
    try:
        asyncio.run(go())
    except KeyboardInterrupt:
        return 0
    except T.SSHError as e:
        print(str(e))
        return 1
    return 0


def cmd_console(args) -> int:
    out = R.console(args.pi)
    print(out["hint"])
    return 0


def cmd_reboot(args) -> int:
    asyncio.run(R.reboot(args.pi))
    print(f"{args.pi}: reboot issued.")
    return 0


def cmd_ssh(args) -> int:
    p = B.load_pi(args.pi)
    import subprocess
    return subprocess.call(["ssh", f"{p['user']}@{p['ssh_host']}"])


def main() -> None:
    p = argparse.ArgumentParser(prog="piloop", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("pis", help="list registered Pis").set_defaults(fn=cmd_pis)

    s = sub.add_parser("scan", help="discover Pis (mDNS + optional BLE)")
    s.add_argument("--seconds", type=float, default=3)
    s.add_argument("--ble", action="store_true", help="also BLE-scan for bridges")
    s.set_defaults(fn=cmd_scan)

    for name, fn, helptext in [
        ("status", cmd_status, "reachable? agent up? last tick?"),
        ("deploy", cmd_deploy, "rsync agent/ + restart the loop"),
        ("logs", cmd_logs, "stream the agent's journald log"),
        ("console", cmd_console, "print the ble_name for tab-device"),
        ("reboot", cmd_reboot, "sudo reboot"),
        ("ssh", cmd_ssh, "interactive shell"),
    ]:
        sp = sub.add_parser(name, help=helptext)
        sp.add_argument("pi")
        sp.set_defaults(fn=fn)

    args = p.parse_args()
    raise SystemExit(args.fn(args))
