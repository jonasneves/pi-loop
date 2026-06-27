#!/bin/bash -e
# Inside the rootfs: install on-Pi Python deps and enable services.

raspi-config nonint do_wifi_country US || true
systemctl enable bluetooth || true

# On-Pi Python dep: just the BLE peripheral lib (no Agent SDK — the brain is
# external; the Pi only exposes a shell).
pip3 install --break-system-packages bless

systemctl enable usb-gadget.service
systemctl enable serial-getty@ttyGS0.service
# The BLE shell bridge: exposes /bin/bash over Nordic UART to tab-device.
systemctl enable piloop-bridge.service
