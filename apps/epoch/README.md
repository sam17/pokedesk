# epoch.me — deployment (on eevee)

Self-hosted deployment of **epoch.me** (the life-metrics app, formerly FxLifeSheet — `metrics.soumyadeep.in`). Migrated off a DigitalOcean droplet onto **eevee** (Raspberry Pi 5) in Nov 2026.

- **App code + images:** `github.com/sam17/epoch.me` — its CI publishes multi-arch images to `registry.digitalocean.com/pokedesk-cr/` (`epoch-viz`, `epoch-backup`, `epoch-telegram`).
- **This dir:** the *deployment* only — compose that pulls those images + wires db, the Cloudflare Tunnel, and backups.

## Architecture
```
Cloudflare edge ──(tunnel: epoch)──> cloudflared ──> viz:8080 ──> db (postgres:15)
metrics.soumyadeep.in                                    ▲             ▲
                                     lifesheet (apps/claw, Discord) ───┘   writes
                                     backup ── pg_dump ─> local + Cloudflare R2 (daily)
```
- `viz` — Rust API + React dashboard (reads `db`).
- `db` — Postgres (the ~21 MB life-metrics data). Not exposed publicly (unlike the old DO box, which had 5432 open to the internet).
- `cloudflared` — remotely-managed tunnel; public hostname `metrics.soumyadeep.in → http://viz:8080` set in the CF Zero Trust dashboard.
- `backup` — daily `pg_dump` → `/opt/backups/fxlifesheet` (30 d) + R2 bucket `epoch-me` (90 d).
- `lifesheet` (Discord bot, lives in `apps/claw/lifesheet`) is the sole writer — it joins the external `epoch` network to reach `epoch-db`.

## First-time setup (eevee)
```bash
# 1. Log in to DO CR so images can be pulled
doctl registry login            # or: docker login registry.digitalocean.com -u <DO_TOKEN> -p <DO_TOKEN>

# 2. Config (gitignored)
cp .env.example .env            # DB_USER/DB_PASS/DB_NAME, CF_TUNNEL_TOKEN
cp backup.env.example backup.env # DATABASE_URL=postgres://USER:PASS@db:5432/DBNAME
# rclone R2 remote at ~/.config/rclone/rclone.conf (remote name: r2) — see epoch.me/backup/README.md

# 3. Bring it up
docker compose up -d

# 4. Restore data into the fresh db (from a dump)
gunzip -c /opt/backups/fxlifesheet/epoch-<ts>.sql.gz | docker exec -i epoch-db psql -U "$DB_USER" -d "$DB_NAME"
```

## Point lifesheet (apps/claw) at the local db
In `apps/claw/lifesheet/docker-compose.yml`, join the external `epoch` network and set
`DATABASE_URL=postgres://USER:PASS@epoch-db:5432/DBNAME`:
```yaml
services:
  lifesheet:
    networks: [default, epoch]
networks:
  epoch:
    external: true
```

## Cutover (DNS)
`metrics.soumyadeep.in` is a **Tunnel** record pointing at the `epoch` tunnel (Cloudflare DNS). The old DO A-record was replaced during migration.

## Notes / A/B
Perf after migration (vs the DO droplet): origin app latency ~2–3× faster (Pi 5 4-core + NVMe vs 1-core droplet), user-perceived through Cloudflare comparable/better. Host-level setup (WiFi 2.4 GHz lock, PCIe Gen3, etc.) is in `apps/claw/host-setup.sh` / `RUNBOOK-ssd-migration.md`.
