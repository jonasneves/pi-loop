"""The Agent SDK harness — the substrate half of pi-loop. Reads config.toml,
runs the configured task on the configured cadence, and prints everything to
stdout (which the bridge's PTY mirrors out over BLE to tab-device).

This file carries NO task knowledge. Swap config.toml and the same loop runs a
different job. That's the whole 'substrate, not app' contract."""
import asyncio
import os
import sys
import tomllib
from pathlib import Path

VALID_CADENCE = {"one-shot", "interval", "continuous"}
_UNITS = {"s": 1, "m": 60, "h": 3600}


def parse_every(s: str) -> float:
    unit = s[-1]
    if unit not in _UNITS:
        raise ValueError(f"bad interval '{s}' — use 30s / 5m / 2h")
    return float(s[:-1]) * _UNITS[unit]


def load_config(path: Path) -> dict:
    data = tomllib.loads(Path(path).read_text())
    task, tools = data.get("task", {}), data.get("tools", {})
    cadence = task.get("cadence", "one-shot")
    if cadence not in VALID_CADENCE:
        raise ValueError(f"cadence must be one of {sorted(VALID_CADENCE)}")
    return {
        "prompt": task["prompt"],
        "cadence": cadence,
        "every": task.get("every"),
        "allow": tools.get("allow", []),
    }


async def run_once(cfg: dict, client) -> None:
    """One agent turn. `client` is a claude_agent_sdk client; injected so the
    cadence logic is testable without the SDK."""
    async for msg in client.query(cfg["prompt"]):
        print(msg, flush=True)


async def main() -> None:
    cfg = load_config(Path(__file__).parent / "config.toml")
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ANTHROPIC_API_KEY not set — the loop can't run.", file=sys.stderr)
        raise SystemExit(1)

    from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions
    options = ClaudeAgentOptions(
        system_prompt=cfg["prompt"], allowed_tools=cfg["allow"])

    async with ClaudeSDKClient(options=options) as client:
        if cfg["cadence"] == "one-shot":
            await run_once(cfg, client)
        elif cfg["cadence"] == "interval":
            period = parse_every(cfg["every"])
            while True:
                await run_once(cfg, client)
                await asyncio.sleep(period)
        else:  # continuous
            while True:
                await run_once(cfg, client)


if __name__ == "__main__":
    asyncio.run(main())
