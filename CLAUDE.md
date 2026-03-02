# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

`pokedesk` is a home automation and monitoring infrastructure project (Pokémon-themed hostnames). It manages multiple services deployed on a Raspberry Pi-based Docker Swarm cluster and standalone Pi kiosks.

## Infrastructure

**Docker Swarm Cluster:**
- Manager: `charmander.local` (192.168.1.58) — run `./deploy.sh` from here or remotely
- Worker: `psyduck.local` — where services actually run
- Registry: `registry.digitalocean.com/pokedesk-cr/`

**Standalone Raspberry Pis:**
- `squirtle.local` — piano timer kiosk display
- `pupitarpi.local` — metrics/node_exporter target (scraped by Prometheus)

## Key Commands

### Deploy services to Docker Swarm
```bash
cd apps
./deploy.sh         # Checks node health, deploys ha-monitoring stack
```

### Build and push a Docker image
```bash
cd apps/ha-monitoring
docker build -t registry.digitalocean.com/pokedesk-cr/ha-monitoring:latest .
docker push registry.digitalocean.com/pokedesk-cr/ha-monitoring:latest
```

### Test services locally
```bash
cd apps
docker-compose up -d
docker-compose logs -f
docker-compose down
```

### cutiepie (home display server)
```bash
cd apps/cutiepie
uv sync                          # Install dependencies
uv run python dev_server.py      # Development (auto-reload)
uv run python server.py          # Production
```
Server runs at `http://localhost:8080`. Requires env vars: `HA_TOKEN`, `HA_URL`, `CAMERA_ENTITY_ID`.

### Piano timer — deploy to squirtle.local
```bash
cd apps/piano-timer/deploy
./deploy.sh    # Copies scripts to squirtle.local via SSH and shows menu
```

### Pi setup / initialization
```bash
# First-time Pi setup
./init/setup.sh <hostname>    # Copies SSH key, WiFi config, reboots Pi
```

## Project Structure

```
apps/
  ha-monitoring/      # Python cron service: pings Home Assistant, sends Telegram alerts on failure
  whoop-collector/    # Whoop fitness API collector (deployed as separate metrics stack)
  cutiepie/           # aiohttp display server: shows metrics page, switches to camera on motion
  metrics-display/    # Scripts for Chromium kiosk on a Pi display (scroll automation)
  monitoring/         # Prometheus config targeting pupitarpi.local:9100
  piano-timer/        # Kiosk scripts and watchdog for squirtle.local (low-RAM Pi)
  docker-compose.yml          # Main swarm stack (ha-monitoring service)
  docker-compose.metrics.yml  # Metrics stack (whoop-collector service)
  deploy.sh                   # Swarm deployment script
conf/
  wpa_supplicant.conf  # WiFi config template for Pi setup
init/
  install.sh           # Installs Docker on a Pi
  setup.sh             # Copies SSH keys and WiFi config, reboots
```

## Service Architecture

**ha-monitoring**: Python service (`run.py`) in a Docker container. Runs via cron every minute, pings and HTTP-checks `HOME_ASSISTANT_IP`, sends Telegram notifications when either check fails.

**whoop-collector**: Collects Whoop fitness data and stores to PostgreSQL. Deployed as a separate stack (`docker-compose.metrics.yml`) with its own `whoop-collector` overlay network.

**cutiepie**: aiohttp web server that polls Home Assistant for motion/person sensor state. Serves an `index.html` that displays metrics by default and switches to camera stream on detection.

**piano-timer**: Tiered kiosk implementation for a memory-constrained Pi (428MB RAM). Uses a smart watchdog service (`memory-watchdog.service`) that restarts the browser when memory/swap thresholds are exceeded.

## Environment Variables

Services read from a `.env` file in `apps/` (never committed). Key variables:
- `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` — Telegram alerts
- `HOME_ASSISTANT_IP` — Home Assistant instance
- `WHOOP_CLIENT_ID`, `WHOOP_CLIENT_SECRET`, `WHOOP_ACCESS_TOKEN`, `WHOOP_REFRESH_TOKEN`, `DATABASE_URL` — Whoop collector
- `HA_TOKEN`, `HA_URL`, `CAMERA_ENTITY_ID` — cutiepie display server

## Swarm Troubleshooting

```bash
# Rejoin worker after certificate expiry
ssh pi@psyduck.local "docker swarm leave --force"
ssh pi@charmander.local "docker swarm join-token worker"
ssh pi@psyduck.local "docker swarm join --token <token> charmander.local:2377"

# Update service env without full redeploy
docker service update --env-add KEY=value ha-monitoring_monitoring

# View live logs
docker service logs ha-monitoring_monitoring -f
```
