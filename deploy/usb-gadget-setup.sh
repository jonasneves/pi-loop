#!/bin/bash
# USB composite gadget (ECM ethernet + ACM serial) via ConfigFS. Runs
# independently of the agent/bridge services so a crashed loop still exposes
# `ssh pi@10.55.0.1` (ECM) and a serial console at /dev/ttyGS0 (ACM).
set -uo pipefail

LOG=/boot/firmware/usb-gadget.log
if [ -d "$(dirname "$LOG")" ] && touch "$LOG" 2>/dev/null; then
  exec >> "$LOG" 2>&1
  _log_path="$LOG"
else
  _log_path="(journal only — /boot/firmware not writable)"
fi
echo "=== usb-gadget-setup $(date -Iseconds) ==="
echo "logging to: $_log_path"
echo "kernel: $(uname -r)"
echo "cmdline: $(cat /proc/cmdline 2>/dev/null)"
lsmod 2>/dev/null | grep -E "^(dwc2|libcomposite|usb_f_)" || echo "  (none loaded yet)"
sync 2>/dev/null || true

set -e

GADGET=/sys/kernel/config/usb_gadget/g1
if [ -d "$GADGET" ]; then
  echo "gadget already configured (idempotent exit)"
  exit 0
fi

for i in $(seq 1 50); do
  if ls /sys/class/udc 2>/dev/null | grep -q .; then
    echo "UDC appeared after $((i * 200))ms: $(ls /sys/class/udc)"
    break
  fi
  sleep 0.2
done
if ! ls /sys/class/udc 2>/dev/null | grep -q .; then
  echo "FAIL: no UDC after 10s — dwc2 not loaded or in host mode"
  exit 1
fi

mkdir -p "$GADGET"
cd "$GADGET"

echo 0x1d6b > idVendor
echo 0x0104 > idProduct
echo 0x0100 > bcdDevice
echo 0x0200 > bcdUSB

mkdir -p strings/0x409
SN=$(awk '/Serial/ { print $NF; exit }' /proc/cpuinfo 2>/dev/null || echo "0000000000")
SUFFIX=$(echo "$SN" | tail -c 5 | tr '[:lower:]' '[:upper:]')
[ -z "$SUFFIX" ] && SUFFIX="0000"
echo "$SN" > strings/0x409/serialnumber
echo "pi-loop" > strings/0x409/manufacturer
echo "piloop-$SUFFIX" > strings/0x409/product

mkdir -p configs/c.1/strings/0x409
echo "ECM + ACM" > configs/c.1/strings/0x409/configuration
echo 250 > configs/c.1/MaxPower

mkdir -p functions/ecm.usb0
mkdir -p functions/acm.usb0

ln -s functions/ecm.usb0 configs/c.1/
ln -s functions/acm.usb0 configs/c.1/

UDC=$(ls /sys/class/udc | head -n 1)
echo "binding gadget to UDC: $UDC"
echo "$UDC" > UDC
echo "bind OK — gadget live at $GADGET, UDC=$UDC"
sync 2>/dev/null || true
