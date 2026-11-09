# Runbook — eevee SD → NVMe SSD migration (as-built)

**Done 2026-11-10.** eevee (Pi 5) moved off its **failing SD card** onto a **Crucial P310 500 GB NVMe** in a **SunFounder Pironman 5** case. The dying SD caused 6–8 min `sync` stalls, kernel `hung_task` warnings, ~366 s OpenClaw boots, and recurring freezes/lockups.

## Results (A/B)

| Metric | Dying SD | NVMe |
|---|---|---|
| OpenClaw gateway boot | **366 s** | **16 s** |
| `sync` under write | **6–8 min stalls** | **0.8 s** |
| Disk sequential read | 87 MB/s | **890 MB/s** (PCIe Gen3) |
| Kernel hung_task / IO errors | 11 | **0** |

## What was done

1. **Backup first** (Mac): `~/eevee-backup-2026-11-09/opt-claw-cutover.tar` (23 GB, containers stopped = consistent) + `~/eevee-backup-2026-10-31/opt-claw.tar` (25 GB). Excluded dropbox/codex-home/junk.
2. **Assemble**: P310 into the Pironman M.2 slot, SD left in (needed to boot once — no NVMe enclosure available).
3. **Flash** Pi OS Lite arm64 → `/dev/nvme0n1` in-place (streamed `curl … | xz -d | dd`), booted from the SD. *(Fresh install, NOT a clone — avoids copying the card's corruption; data restored from SD afterward.)*
4. **Headless config** via `/boot/firmware/custom.toml` (hostname, user, SSH keys, WiFi). ⚠️ see gotcha below.
5. **Boot order** → NVMe-first, SD fallback: EEPROM `BOOT_ORDER=0xf416` (`rpi-eeprom-config --edit`, flashed via flashrom; verify by reading the chip, not the boot-time cache).
6. **Restore** `/opt/claw` locally from the SD (`rsync`, containers stopped), **excluding codex-home** (fresh rebuild) and junk/dropbox.
7. **Docker + rebuild image** (`pokedesk/openclaw:latest` from the Dockerfile), `docker compose up`.
8. **PCIe Gen3**: `dtparam=pciex1` + `dtparam=pciex1_gen=3` in `/boot/firmware/config.txt` (link speed 8 GT/s).
9. **Tailscale** reinstalled + `tailscale up` → node `eevee` (IP `100.95.147.59`). Old `100.72.77.73` deleted.
10. **Maestral** reinstalled (see pins below), synced to `/opt/claw/sam/dropbox`, autostart + `loginctl enable-linger pi`.

## Gotchas (read before any future rebuild)

- **No NVMe enclosure** → can't flash from the Mac; must boot the SD once to flash the NVMe in place. If the SD won't boot, you're stuck without an enclosure.
- **`custom.toml` only partially applied** on Debian 13 (trixie): WiFi connected, but **user/SSH/hostname fell back to defaults (`pi`/`raspberry`, SSH off)**. Required a **monitor + keyboard once** to enable SSH + (since first-boot skipped it) install the SSH key via a password login + `expect`.
- **Do NOT exclude `config/**/node_modules` on restore.** OpenClaw's `discord`/`acpx` plugins live under `config/npm/projects/*/node_modules/@openclaw/*`; excluding them → "plugin not installed" + no Discord. Only *workspace* node_modules are safe to skip.
- **Do NOT restore codex-home** → triggers the codex state-DB backfill wedge (every turn 408s). Let the container recreate it; codex auth lives separately at `sam/config/.codex/auth.json`.
- **WiFi band matters.** A bare `nmcli dev wifi connect` picked **5 GHz @ 51% which flapped constantly** (dropped SSH + Dobby's Discord). Fix: lock to 2.4 GHz — `nmcli con modify Azkaban 802-11-wireless.band bg` — plus powersave off (`/etc/NetworkManager/conf.d/wifi-powersave-off.conf`). No ethernet at the Pi.
- **Maestral on Python 3.13 (ARM, headless)** needs dependency pins: `pipx inject maestral 'dropbox==11.36.2' --force` (v12 breaks with an `extra_headers` TypeError) and `pipx inject maestral 'setuptools==70.3.0' --force` (newer setuptools dropped `pkg_resources`). Plaintext-keyring is expected.
- **macOS `openrsync` is broken** for `--exclude` and `--rsync-path=sudo` — use tar-over-ssh, or restore locally from the SD (not over the network).
- **Docker group GID** on the fresh OS differs (was 984, now 985) — fix `group_add` in `docker-compose.yml` or Dobby can't use the docker socket.

## Post-migration follow-ups
- [ ] Wipe/remove the old SD after ~1 week of stable NVMe running (currently left in as cold-boot fallback).
- [ ] Rotate the chat-exposed Metabase API key + Dashverse deploy token.
- [ ] Give Dobby its own ChatGPT/codex account (ends the shared-account token-rotation breakage).
