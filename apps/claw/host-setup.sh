#!/usr/bin/env bash
#
# Host-level setup for eevee (Raspberry Pi 5) after a FRESH Pi OS Lite install.
# Run AFTER flashing the OS and restoring /opt/claw (see RUNBOOK-ssd-migration.md).
# Captures the host config that makes eevee fast + stable on NVMe/WiFi.
#
# NO SECRETS live here. The WiFi PSK is read from $WIFI_PSK (env) or entered
# manually — never hardcode it.  Usage:  WIFI_PSK=xxxx ./host-setup.sh
#
set -euo pipefail

WIFI_SSID="${WIFI_SSID:-Azkaban}"

echo "== 1. WiFi: lock to 2.4GHz + disable power-save (the flapping fix) =="
# The onboard Pi 5 WiFi on 5GHz was weak (~51%) and flapped constantly, dropping
# SSH and Dobby's Discord. 2.4GHz is stable. Power-save must also be off.
sudo tee /etc/NetworkManager/conf.d/wifi-powersave-off.conf >/dev/null <<'CONF'
[connection]
wifi.powersave = 2
CONF
if nmcli -t -f NAME con show 2>/dev/null | grep -qx "$WIFI_SSID"; then
  sudo nmcli con modify "$WIFI_SSID" 802-11-wireless.band bg \
       802-11-wireless.powersave 2 connection.autoconnect yes
  sudo nmcli con up "$WIFI_SSID" || true
elif [ -n "${WIFI_PSK:-}" ]; then
  sudo nmcli dev wifi connect "$WIFI_SSID" password "$WIFI_PSK"
  sudo nmcli con modify "$WIFI_SSID" 802-11-wireless.band bg \
       802-11-wireless.powersave 2 connection.autoconnect yes
else
  echo "   ! '$WIFI_SSID' not configured and WIFI_PSK not set."
  echo "     Connect once (nmcli dev wifi connect '$WIFI_SSID' password <psk>) then re-run."
fi

echo "== 2. PCIe Gen3 for the NVMe (8 GT/s, ~890 MB/s) =="
if ! grep -q 'pciex1_gen=3' /boot/firmware/config.txt; then
  printf '\n# NVMe PCIe Gen3\ndtparam=pciex1\ndtparam=pciex1_gen=3\n' \
    | sudo tee -a /boot/firmware/config.txt >/dev/null
fi

echo "== 3. Passwordless sudo for pi =="
echo 'pi ALL=(ALL) NOPASSWD: ALL' | sudo tee /etc/sudoers.d/010-pi-nopasswd >/dev/null
sudo chmod 440 /etc/sudoers.d/010-pi-nopasswd
sudo visudo -c -f /etc/sudoers.d/010-pi-nopasswd

echo
echo "== Manual / interactive steps (NOT automated here) =="
cat <<'NOTES'
4. EEPROM boot order -> NVMe first, SD fallback (BOOT_ORDER=0xf416):
     sudo EDITOR="sed -i 's/^BOOT_ORDER=.*/BOOT_ORDER=0xf416/'" rpi-eeprom-config --edit
   Verify by reading the chip (not the boot-time cache):
     sudo flashrom -p linux_spi:dev=/dev/spidev10.0,spispeed=16000 -r /tmp/e.bin && \
       sudo rpi-eeprom-config /tmp/e.bin | grep BOOT_ORDER

5. Maestral (Dropbox) — needs dep pins on Python 3.13 (ARM, headless):
     sudo apt-get install -y pipx
     pipx install maestral
     pipx inject maestral 'dropbox==11.36.2' --force     # v12 breaks: extra_headers TypeError
     pipx inject maestral 'setuptools==70.3.0' --force    # newer setuptools dropped pkg_resources
     maestral config set path /opt/claw/sam/dropbox
     maestral auth link          # interactive: open URL, paste auth code
     maestral start
     maestral autostart -Y && sudo loginctl enable-linger pi

6. Tailscale:
     curl -fsSL https://tailscale.com/install.sh | sudo sh
     sudo tailscale up --hostname=eevee
NOTES

echo
echo "Done. Reboot to apply PCIe Gen3 + config.txt changes:  sudo reboot"
