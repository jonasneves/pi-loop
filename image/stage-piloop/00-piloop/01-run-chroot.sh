#!/bin/bash -e
# Inside the rootfs: install on-Pi Python deps and enable services.

raspi-config nonint do_wifi_country US || true
systemctl enable bluetooth || true

# On-Pi Python deps: the Agent SDK + the BLE peripheral lib.
pip3 install --break-system-packages claude-agent-sdk bless

systemctl enable usb-gadget.service
systemctl enable serial-getty@ttyGS0.service
# Default: the bridge (BLE console). It forks the loop as its child, so do NOT
# also enable piloop-agent.service (that's the headless alternative).
systemctl enable piloop-bridge.service
