"""piloop — operate Raspberry Pis as controllable arms over WiFi (SSH).

The Pi is a device the external brain drives; each verb is a thin renderer over
runtime's data. `exec` runs a command and prints its output (the WiFi control
primitive); `console` prints the ble_name to hand to tab-device for the BLE
out-of-band channel. Everything else is SSH."""
import argparse
import asyncio

from piloop import pis as B
from piloop import runtime as R
from piloop import transport as T


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
    shell = "up" if out["ble_shell"] else "down"
    print(f"{args.pi} ({out['ssh_host']}): reachable  {out['uptime'] or '—'}  "
          f"load={out['load'] or '—'}  ble-shell={shell}")
    return 0


def cmd_exec(args) -> int:
    command = " ".join(args.command).strip()
    if not command:
        print("usage: piloop exec <pi> <command...>")
        return 2
    try:
        out = asyncio.run(R.exec(args.pi, command))
    except T.SSHError as e:
        print(str(e))
        return 1
    text = out["output"]
    if text:
        print(text, end="" if text.endswith("\n") else "\n")
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

    e = sub.add_parser("exec", help="run a command on the Pi over SSH")
    e.add_argument("pi")
    e.add_argument("command", nargs=argparse.REMAINDER, help="command to run")
    e.set_defaults(fn=cmd_exec)

    for name, fn, helptext in [
        ("status", cmd_status, "reachable? uptime, load, BLE shell up?"),
        ("console", cmd_console, "print the ble_name for tab-device"),
        ("reboot", cmd_reboot, "sudo reboot"),
        ("ssh", cmd_ssh, "interactive shell"),
    ]:
        sp = sub.add_parser(name, help=helptext)
        sp.add_argument("pi")
        sp.set_defaults(fn=fn)

    args = p.parse_args()
    raise SystemExit(args.fn(args))
