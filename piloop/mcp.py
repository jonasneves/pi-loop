"""MCP wrapper over the same runtime verbs — opt-in (`pip install '.[mcp]'`).
Thin: each tool calls runtime and returns its data or a success string. The
impl functions are split out so they're unit-testable without a live server."""
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
    """Reachable? agent loop up? last tick? One structured read over SSH."""
    return await R.status(pi)


@mcp.tool()
async def deploy(pi: str) -> str:
    """rsync the repo's agent/ to the Pi and restart the loop."""
    from piloop.cli import REPO_AGENT_DIR
    await R.deploy(pi, REPO_AGENT_DIR)
    return f"{pi}: deployed and restarted."


@mcp.tool()
async def console(pi: str) -> str:
    """The ble_name to connect to from tab-device (the host doesn't stream BLE)."""
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


def main() -> None:
    mcp.run()
