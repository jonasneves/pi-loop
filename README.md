# pi-loop

A Raspberry Pi that runs a Claude Agent SDK loop on itself — and lets you watch
it think in a browser terminal over Bluetooth.

The Pi runs an agent loop (`agent/loop.py`, task in `agent/config.toml`). Its
console is bridged over BLE Nordic UART to [tab-device](https://jonasneves.com/tab-device/)'s
xterm, so you `connect ble piloop` in a Chromium tab and see the loop live. A
host CLI operates the Pi over SSH; a USB-gadget channel recovers it when BLE and
WiFi are both down.

Sibling of [esp32-loop](https://github.com/jonasneves/esp32-loop): the same
host-side three-tier split (runtime / CLI / MCP + a TOML device registry),
re-pointed from flashing a board to operating a Pi that hosts the agent.

## Host CLI

    pip install -e .
    piloop pis                  # list registered Pis (pis/*.toml)
    piloop scan --ble           # discover Pis: mDNS + BLE advert scan
    piloop status <name>        # reachable? agent up? last tick?
    piloop deploy <name>        # rsync agent/ + restart the loop
    piloop logs <name>          # stream the agent's journald log
    piloop console <name>       # prints the ble_name to connect from tab-device
    piloop reboot <name>
    piloop ssh <name>

`console` is a pointer, not a stream: the console lives on BLE and tab-device is
its client, so the host just tells you what to `connect ble`.

## Register a Pi

Copy `pis/example.toml` to `pis/<name>.toml` and set `ssh_host` + `ble_name`.

## The image

`image/stage-piloop` is a pi-gen custom stage that bakes the agent loop, the BLE
bridge, and a USB-gadget recovery channel. Build it via the `build-image` GitHub
Action (`workflow_dispatch`, or tag `image-v*` for a released `.img`), flash it,
drop your `ANTHROPIC_API_KEY` into `/etc/piloop/agent.env`, and boot.

## The agent is a framework, not an app

`loop.py` carries no task — it reads `config.toml` (prompt, allowed tools,
cadence). Swap the config and the same image runs a different job.

## What binds

- **Chromium + secure context** for tab-device (Web Bluetooth).
- **BLE is low-bandwidth and starts late** — it's the watch-it-think surface, not
  a boot console or a bulk channel. SSH is the high-bandwidth path; the
  USB-gadget serial (`ssh pi@10.55.0.1`, console on `/dev/ttyGS0`) is recovery.
- **`ANTHROPIC_API_KEY`** lives on the Pi (`/etc/piloop/agent.env`), never in the repo.
