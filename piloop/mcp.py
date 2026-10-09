"""MCP wrapper over the same runtime verbs — opt-in (`pip install '.[mcp]'`).
Thin: each tool calls runtime and returns its data or a success string. The
impl functions are split out so they're unit-testable without a live server.

This is the brain's WiFi control surface: the external agent reaches a Pi over
SSH through these tools when WiFi is up, and falls back to the BLE shell
(via `console` → tab-device) when it isn't."""
import os
import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from piloop import pis as B
from piloop import runtime as R

mcp = FastMCP("piloop")


def _pis_impl() -> list[dict]:
    return [B.load_pi(n) for n in B.list_pis()]


async def _console_impl(pi: str) -> str:
    return R.console(pi)["hint"]


@mcp.tool()
def pis() -> list[dict]:
    """List registered Pis (handle, ssh_host, ble_name). Each `name` is the
    handle the other tools take as `pi`."""
    return _pis_impl()


@mcp.tool()
async def status(pi: str) -> dict:
    """Reachable? uptime, load average, and whether the BLE shell is up. One
    structured read over SSH."""
    return await R.status(pi)


@mcp.tool()
async def exec(pi: str, command: str) -> dict:
    """Run a shell command on the Pi over SSH and return its output. The
    high-bandwidth WiFi control primitive — use this to drive the Pi when WiFi
    is up."""
    return await R.exec(pi, command)


@mcp.tool()
async def console(pi: str) -> str:
    """The ble_name to connect to from tab-device — the out-of-band BLE shell
    for when WiFi is down (the host doesn't stream BLE itself)."""
    return await _console_impl(pi)


@mcp.tool()
async def reboot(pi: str) -> str:
    """sudo reboot the Pi."""
    await R.reboot(pi)
    return f"{pi}: reboot issued."


@mcp.tool()
async def scan(seconds: float = 3, ble: bool = False) -> dict:
    """Discover Pis: mDNS sweep + optional BLE advert scan."""
    return await R.scan(seconds, ble)


RELAY_KEY = Path.home() / ".config" / "piloop" / "relay.key"


def relay_key() -> str:
    """This host's private relay key, made on first use (owner-only from creation)."""
    from piloop.relay_client import load_or_create_key
    return load_or_create_key(RELAY_KEY)


def relay_allow(env=os.environ) -> list[str]:
    return [s.strip() for s in env.get("PILOOP_RELAY_ALLOW", "").split(",") if s.strip()]


def main() -> None:
    """stdio by default. `--relay` serves the same tools through the MCP relay
    (relay.kandue.app) to claude.ai, Cursor or VS Code: `exec` is a shell on every
    registered Pi, so it is refused unless PILOOP_RELAY_ALLOW names the GitHub logins
    that may sign in to it."""
    if "--relay" not in sys.argv[1:]:
        mcp.run()
        return
    allow = relay_allow()
    if not allow:
        sys.exit("piloop-mcp --relay: set PILOOP_RELAY_ALLOW=<your-github-login>. The relay answers only "
                 "a caller signed in with GitHub as one of those accounts; exec is a shell on your Pis.")
    import asyncio
    from piloop.relay_client import mcp_url, serve_mcp
    key = relay_key()
    print(f"piloop relay: {mcp_url(key, signed=True)}  (sign-in as {', '.join(allow)})", file=sys.stderr, flush=True)
    asyncio.run(serve_mcp(mcp, key=key, allow=allow, name="piloop",
                          offline="piloop is not reachable: `piloop-mcp --relay` is not running on the host."))
