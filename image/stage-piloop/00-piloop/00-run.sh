#!/bin/bash -e
# Host context (has ROOTFS_DIR): drop pi-loop's on-Pi files into the rootfs.
# Repo dirs agent/, bridge/, deploy/ are copied straight in; the USB-gadget boot
# patches are lifted from hub wholesale.

REPO="$(cd "$(dirname "$0")/../../.." && pwd)"   # repo root from the stage dir

# --- agent loop + bridge ---
install -d "${ROOTFS_DIR}/opt/piloop/agent" "${ROOTFS_DIR}/opt/piloop/bridge"
cp "${REPO}/agent/"*.py "${REPO}/agent/config.toml" "${ROOTFS_DIR}/opt/piloop/agent/"
cp "${REPO}/bridge/bridge.py"                        "${ROOTFS_DIR}/opt/piloop/bridge/"

# --- systemd units ---
install -m 0644 "${REPO}/deploy/piloop-agent.service"  "${ROOTFS_DIR}/etc/systemd/system/piloop-agent.service"
install -m 0644 "${REPO}/deploy/piloop-bridge.service" "${ROOTFS_DIR}/etc/systemd/system/piloop-bridge.service"

# --- USB-gadget recovery (lifted from hub) ---
install -m 0755 "${REPO}/deploy/usb-gadget-setup.sh" "${ROOTFS_DIR}/usr/local/bin/usb-gadget-setup.sh"
install -m 0644 "${REPO}/deploy/usb-gadget.service"  "${ROOTFS_DIR}/etc/systemd/system/usb-gadget.service"

# dwc2 peripheral mode + libcomposite (hub's guard logic verbatim).
CONFIG="${ROOTFS_DIR}/boot/firmware/config.txt"
CMDLINE="${ROOTFS_DIR}/boot/firmware/cmdline.txt"
grep -q 'dr_mode=peripheral' "$CONFIG" || \
  printf '\n[all]\ndtoverlay=dwc2,dr_mode=peripheral\n' >> "$CONFIG"
grep -q 'modules-load=dwc2' "$CMDLINE" || \
  sed -i 's/\brootwait\b/rootwait modules-load=dwc2,libcomposite/' "$CMDLINE"

# usb0 = 10.55.0.1/24 shared (ssh pi@10.55.0.1 over the cable).
install -d -m 0700 "${ROOTFS_DIR}/etc/NetworkManager/system-connections"
cat > "${ROOTFS_DIR}/etc/NetworkManager/system-connections/usb-gadget.nmconnection" <<'NMEOF'
[connection]
id=usb-gadget
type=ethernet
interface-name=usb0
autoconnect=true

[ethernet]

[ipv4]
method=shared
address1=10.55.0.1/24

[ipv6]
method=ignore
NMEOF
chmod 600 "${ROOTFS_DIR}/etc/NetworkManager/system-connections/usb-gadget.nmconnection"

# Autologin on the USB-ACM serial console (physical cable = auth boundary).
install -d -m 0755 "${ROOTFS_DIR}/etc/systemd/system/serial-getty@ttyGS0.service.d"
cat > "${ROOTFS_DIR}/etc/systemd/system/serial-getty@ttyGS0.service.d/autologin.conf" <<'AUTOEOF'
[Service]
ExecStart=
ExecStart=-/sbin/agetty --autologin pi --keep-baud 115200,57600,38400,9600 %I $TERM
AUTOEOF

# Agent env file placeholder — the API key is dropped here out-of-band (never
# baked into the repo or image). Empty file so EnvironmentFile=- finds something.
install -d -m 0755 "${ROOTFS_DIR}/etc/piloop"
echo "# ANTHROPIC_API_KEY=...   (drop the real key here; never commit it)" \
  > "${ROOTFS_DIR}/etc/piloop/agent.env"
chmod 600 "${ROOTFS_DIR}/etc/piloop/agent.env"
