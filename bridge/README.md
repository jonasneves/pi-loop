# bridge — PTY ↔ BLE Nordic UART

Runs a command under a PTY and exposes its console over BLE NUS, for tab-device.

## Smoke test (on a Pi with BlueZ)

    sudo pip install bless
    BLE_NAME=piloop-test sudo -E python bridge.py -- bash

Then in tab-device (Chromium): `connect ble piloop-test`, `use <id>`. You should
get an interactive bash shell over BLE. Type `ls` — output streams back.

If advertising fails or BlueZ rejects the GATT registration, switch to the
dbus-next fallback (see design doc, section "On-Pi BLE bridge").
