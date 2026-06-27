# pi-loop

A Raspberry Pi as a **controllable arm** — reachable two ways, so a controller
never loses its grip: over **WiFi** (SSH, high-bandwidth) and over **BLE** (a
Nordic UART login shell, proximity, always-on). When WiFi drops, BLE is the
out-of-band channel you fix it through.

This is [esp32-loop](https://github.com/jonasneves/esp32-loop) for a full Linux
Pi: the same host-side three-tier split — `runtime` (data-returning verbs) /
`cli` + `mcp` (the two formatting front-ends) / a TOML device registry —
re-pointed from flashing a board to operating a Pi. The Pi runs no brain of its
own; it just exposes a shell on both transports.

## Host CLI — the WiFi control surface

    pip install -e .
    piloop pis                  # list registered Pis (pis/*.toml)
    piloop scan --ble           # discover Pis: mDNS + BLE advert scan
    piloop status <name>        # reachable? uptime, load, BLE shell up?
    piloop exec <name> <cmd>    # run a command over SSH, print its output
    piloop console <name>       # prints the ble_name to connect from tab-device
    piloop reboot <name>
    piloop ssh <name>           # interactive shell

`exec` is the primitive: run a command, get its output. `console` is a pointer,
not a stream — the BLE shell lives on the Pi and [tab-device](https://jonasneves.com/tab-device/)
is its client, so the host just tells you what to `connect ble`.

The same verbs are exposed over MCP (`pip install '.[mcp]'`, `piloop-mcp`), so an
agent can drive a Pi over WiFi as tools.

## The BLE shell — out-of-band recovery

The image runs `bridge.py` as a systemd service: it forks `/bin/bash` under a
PTY and mirrors it to a Nordic UART (NUS) GATT service. tab-device binds NUS by
characteristic property, so it gets a live root shell over Bluetooth with zero
config. WiFi down? `connect ble piloop-XXXX` in a Chromium tab and re-provision
from there. Below that, the USB-gadget serial (`ssh pi@10.55.0.1`, console on
`/dev/ttyGS0`) is the deeper recovery path when even BLE is down.

## Register a Pi

Copy `pis/example.toml` to `pis/<name>.toml` and set `ssh_host` + `ble_name`.
The bridge advertises `piloop-<SUFFIX>` where SUFFIX = the last 4 of the CPU
serial (uppercase) — a real persistent device property, not app-side state.

## The image

`image/stage-piloop` is a pi-gen custom stage that bakes the BLE shell bridge
and a USB-gadget recovery channel. Build it via the `build-image` GitHub Action
(`workflow_dispatch`, or tag `image-v*` for a released `.img`), flash it, and
boot. No secret goes on the Pi — the brain is external.

## What binds

- **Chromium + secure context** for tab-device (Web Bluetooth).
- **Two transports, never one.** WiFi (SSH) is the high-bandwidth path; BLE is
  low-bandwidth and starts late (BlueZ boots late), so it's the proximity /
  out-of-band channel, not a bulk pipe. The USB-gadget serial is the floor.
- **The Pi holds no brain and no secret.** It exposes a shell; whatever drives
  it lives elsewhere.
