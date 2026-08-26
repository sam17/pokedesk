# SOP — Add a new OpenClaw bot for a family member

Last verified: 2026-05-27 (during Olmec setup for Arpit).

Total operator time: ~15 min if you have the user's answers ready. The new user clicks two links (~2 min).

---

## 0. Collect from the recipient

Forward the message in `apps/claw/onboarding-message.md`'s sibling file `apps/claw/intake-questions.md` if you make one — but the answers needed are:

1. **Bot name + emoji + one-line vibe** (e.g., "Olmec 🗿 — stoic, deadpan, drily helpful")
2. **Their Discord user ID** (18-digit snowflake; right-click profile → Copy User ID with Developer Mode on)
3. **Discord bot token** — they create the bot at https://discord.com/developers/applications → "New Application" → Bot tab → Reset Token. Token format: `MTU…dot…dot…`.
4. **Where they'll talk to it** — DMs only / specific guild ID / both
5. **AI model** — "anthropic shared key" (free for them, fastest) / "ChatGPT Plus via OAuth" / other
6. **Integrations beyond Google Calendar?** — usually skip
7. **qmd notes memory?** — usually yes

Defaults that work for everyone: model = `anthropic/claude-sonnet-4-6`, qmd = on, DMs + guild allowlist, Composio for Google Calendar.

---

## 1. Allocate identifiers

- **Person slug** (eevee dir + Composio user_id): their first name, lowercase. e.g., `arpit`, `april`, `charu`.
- **Bot slug** (container name + env var prefix): the bot's name lowercased. e.g., `olmec`, `dobby`, `hedwig`, `shadowsapphire`.
- **Gateway port** on host: next free in the `1879N` range. Currently used: 18789 (Dobby), 18790 (Hedwig), 18792 (Shadowsapphire), 18793 (Olmec). 18791 reserved for the obsidian-sync server.
- **Composio user_id**: same as person slug. Free-form string; we use first names.

Cross-reference: see `[[project_claw_agents]]` and `[[project_claw_google_calendar_composio]]` in the auto-memory store for which IDs are already in use.

---

## 2. Stop nothing — new bot doesn't affect existing ones

You don't need to stop any other bot. Skip to step 3.

---

## 3. On eevee — scaffold dirs + .env + config + docker-compose

SSH to `pi@eevee.taile01db3.ts.net` and run a Python script that does all of the following atomically (template below; adjust the four variables at the top). Pattern proven during Olmec setup.

```python
PERSON       = "arpit"       # dir + Composio user_id
BOT          = "olmec"       # container + env var prefix
PORT         = 18793         # gateway host port
DISCORD_TOKEN = "MTU…"       # from step 0
DISCORD_USER  = "289…"       # from step 0
GUILD_ID      = "150…"       # from step 0 (or None for DM-only)
BOT_NAME      = "Olmec"
BOT_EMOJI     = "🗿"
BOT_THEME     = "stoic, deadpan, drily helpful — speaks in short sentences with the occasional cryptic wisdom"

import json, os, secrets, datetime, shutil

# 3a. Make dirs
for sub in ["config", "workspace", "mcp-auth"]:
    p = f"/opt/claw/{PERSON}/{sub}"
    os.makedirs(p, exist_ok=True)
    shutil.chown(p, user="pi", group="pi")

# 3b. Append tokens to /opt/claw/.env (generate gateway token)
gw_token = secrets.token_hex(32)
env_path = "/opt/claw/.env"
with open(env_path) as f: env = f.read()
adds = []
upper_bot = BOT.upper()
if f"{upper_bot}_GATEWAY_TOKEN=" not in env: adds.append(f"{upper_bot}_GATEWAY_TOKEN={gw_token}\n")
if f"{upper_bot}_DISCORD_TOKEN=" not in env: adds.append(f"{upper_bot}_DISCORD_TOKEN={DISCORD_TOKEN}\n")
if adds:
    if not env.endswith("\n"): adds.insert(0, "\n")
    with open(env_path, "a") as f: f.writelines(adds)

# 3c. Write openclaw.json (+ .last-good)
cfg = {
  "agents": {
    "defaults": {
      "model": {"primary": "anthropic/claude-sonnet-4-6"},
      "sandbox": {"mode": "off"},
      "memorySearch": {"enabled": True}
    },
    "list": [{
      "id": "main",
      "identity": {"name": BOT_NAME, "theme": BOT_THEME, "emoji": BOT_EMOJI}
    }]
  },
  "channels": {
    "discord": {
      "enabled": True,
      "token": {"source": "env", "provider": "default", "id": f"{upper_bot}_DISCORD_TOKEN"},
      "dmPolicy": "allowlist",
      "dm": {"allowFrom": [DISCORD_USER]},
      "groupPolicy": "allowlist",
      "guilds": ({GUILD_ID: {"requireMention": False, "users": [DISCORD_USER]}} if GUILD_ID else {})
    }
  },
  "memory": {
    "backend": "qmd",
    "citations": "auto",
    "qmd": {
      "paths": [{"name": "notes", "path": "/home/node/.openclaw/workspace/notes", "pattern": "**/*.md"}],
      "sessions": {"enabled": True},
      "update": {"startup": "immediate"}
    }
  },
  "gateway": {
    "mode": "local", "port": 18789, "bind": "lan",
    "tls": {"enabled": True, "certPath": "/home/node/.openclaw/certs/cert.pem", "keyPath": "/home/node/.openclaw/certs/key.pem"},
    "controlUi": {
      "allowedOrigins": [f"https://eevee.local:{PORT}", f"https://192.168.1.63:{PORT}", f"https://eevee:{PORT}", f"https://100.72.77.73:{PORT}"],
      "dangerouslyAllowHostHeaderOriginFallback": True
    }
  },
  "mcp": {
    "servers": {
      "google-calendar": {
        "command": "npx",
        "args": [
          "-y", "mcp-remote",
          f"https://backend.composio.dev/v3/mcp/e7b26074-5f91-4e95-ada0-e9c056828c99/mcp?user_id={PERSON}",
          "--header", "x-api-key:${COMPOSIO_API_KEY}"
        ]
      }
    }
  },
  "meta": {
    "lastTouchedVersion": "manual",
    "lastTouchedAt": datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%S.") + ("%03d" % (datetime.datetime.now(datetime.UTC).microsecond // 1000)) + "Z"
  }
}
out = json.dumps(cfg, indent=2) + "\n"
for p in [f"/opt/claw/{PERSON}/config/openclaw.json", f"/opt/claw/{PERSON}/config/openclaw.json.last-good"]:
    with open(p, "w") as f: f.write(out)
    os.chmod(p, 0o600); shutil.chown(p, user="pi", group="pi")

# 3d. Append service block to /opt/claw/docker-compose.yml (skip if already there)
compose_path = "/opt/claw/docker-compose.yml"
with open(compose_path) as f: compose = f.read()
if f"container_name: {BOT}" not in compose:
    shutil.copy2(compose_path, compose_path + ".bak." + BOT + "." + datetime.datetime.now(datetime.UTC).strftime("%Y%m%dT%H%M%SZ"))
    block = f"""
  # ── {BOT_NAME} ({PERSON.capitalize()}'s agent) ────────────────────────────
  {BOT}:
    build: .
    image: pokedesk/openclaw:latest
    container_name: {BOT}
    restart: unless-stopped
    ports:
      - "{PORT}:18789"
    environment:
      - ANTHROPIC_API_KEY=${{ANTHROPIC_API_KEY}}
      - OPENCLAW_GATEWAY_TOKEN=${{{upper_bot}_GATEWAY_TOKEN}}
      - OPENCLAW_GATEWAY_BIND=lan
      - OPENCLAW_NO_RESPAWN=1
      - NODE_COMPILE_CACHE=/var/tmp/openclaw-compile-cache
      - {upper_bot}_DISCORD_TOKEN=${{{upper_bot}_DISCORD_TOKEN}}
      - NODE_EXTRA_CA_CERTS=/home/node/.openclaw/certs/cert.pem
      - TZ=${{TZ:-Asia/Kolkata}}
    volumes:
      - /opt/claw/{PERSON}/config:/home/node/.openclaw
      - /opt/claw/{PERSON}/workspace:/home/node/.openclaw/workspace
      - /opt/claw/certs:/home/node/.openclaw/certs:ro
      - /opt/claw/{PERSON}/mcp-auth:/home/node/.mcp-auth
    healthcheck:
      test: ["CMD", "curl", "-sf", "--insecure", "https://127.0.0.1:18789/healthz"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 90s
"""
    if not compose.endswith("\n"): compose += "\n"
    with open(compose_path, "w") as f: f.write(compose + block)
```

---

## 4. Mirror in the repo

Create `apps/claw/<person>/config/openclaw.json` with the same content but **no** `meta` block (runtime auto-populates it on first boot). Append the same docker-compose block to `apps/claw/docker-compose.yml`.

Commit later when you're ready.

---

## 5. Boot the new bot

```
ssh pi@eevee.taile01db3.ts.net 'cd /opt/claw && docker compose up -d <bot>'
sleep 15
ssh pi@eevee.taile01db3.ts.net 'docker logs --tail 30 <bot>'
```

Expect to see `[gateway] ready` and `[discord] starting provider (@<BotName>)`.

---

## 6. 🚨 Discord intent gotcha (THE one thing that bites every time)

If the recipient just created the Discord bot, **Message Content Intent** and **Server Members Intent** are OFF by default. Bot connects to Discord but can't read message content — log shows:

```
[discord] gateway closed with code 4014 (missing privileged gateway intents).
```

Tell the recipient:
> Discord Developer Portal → your bot → Bot tab (left sidebar) → scroll to "Privileged Gateway Intents" → toggle ON "Message Content Intent" and "Server Members Intent" → Save Changes.

Bot reconnects automatically; no restart needed. Verify by greping logs for `Discord Message Content Intent is limited; bots under 100 servers can use it without verification.` (that wording = OK).

Also: bot must have been *invited* to the guild via an OAuth URL with `bot` scope + `Send Messages` + `Read Message History` permissions. If the bot doesn't show up in the guild's member list, the recipient skipped the invite step.

---

## 7. Wire up Google Calendar via Composio

(Composio = OAuth broker — they own the Google-verified OAuth client so users get a clean consent flow.)

```
COMPOSIO_API_KEY=<your-composio-api-key>  # see [[project_claw_google_calendar_composio]] memory
AUTH_CONFIG=ac_qd_-JoiPtxWU

curl -X POST -H "x-api-key: $COMPOSIO_API_KEY" -H "Content-Type: application/json" \
  https://backend.composio.dev/api/v3/connected_accounts/link \
  -d '{"auth_config_id":"'$AUTH_CONFIG'","user_id":"<person-slug>"}'
```

Returns `redirect_url` (expires in ~20 min). Send it to the recipient with:

> Click this link to give your bot access to your Google Calendar — sign in with your Google and approve. That's it.

Then verify:

```
curl -H "x-api-key: $COMPOSIO_API_KEY" \
  https://backend.composio.dev/api/v3/connected_accounts/<connected_account_id> | jq .status
```

Expect `"ACTIVE"`. If `"EXPIRED"`, regenerate the link with the same curl.

The bot's `mcp.servers.google-calendar` block (from step 3c) already points at `user_id=<person-slug>`, so once the connection is ACTIVE the bot can immediately call calendar tools — no restart needed.

---

## 8. Send the onboarding message

Forward `apps/claw/onboarding-message.md` (or its current rendering) via WhatsApp. Customize names/examples if needed.

---

## 9. Update memory

After successful setup, append a line to `MEMORY.md` index referencing the new bot, and update `project_claw_agents.md` to list them.

---

## Reference state (as of 2026-05-27)

| Person | Bot | Container | Port | Composio user_id | Connection ID |
|---|---|---|---|---|---|
| Sam | Dobby | dobby | 18789 | sam | ca_A_WM8l30IKCv (ACTIVE) |
| Charu | Hedwig | hedwig | 18790 | charu | (regenerated, possibly EXPIRED) |
| Divya | Shadowsapphire | shadowsapphire | 18792 | divya | ca_KD7Smz5LrDCZ (ACTIVE) |
| Arpit | Olmec | olmec | 18793 | arpit | not connected yet |

Shared infra:
- Composio account: API key in `/opt/claw/.env` as `COMPOSIO_API_KEY` (do not commit); auth config + MCP server id stored alongside it
- eevee: `pi@eevee.taile01db3.ts.net`
- Compose dir: `/opt/claw/`, env file: `/opt/claw/.env`
- Stale GCP-flow artifacts to clean up later: `/opt/claw/auth/google-oauth-client.json`, `/opt/claw/bin/auth-gcal.sh`, port mappings 3334/3335 on shadowsapphire/hedwig

---

## Common gotchas (chronological order, by the bite they delivered)

1. **Editing `openclaw.json` on a running container reverts** — runtime checks meta block + `.last-good` sidecar, treats foreign edits as corruption. Always stop container OR write both files atomically with a bumped `meta.lastTouchedAt`. See `[[feedback_openclaw_config_edits]]`.
2. **Self-hosted GCP OAuth verification is a dead end** for family-scale use — Google requires verification for sensitive Calendar scopes; Test User mode has 7-day refresh expiry. Use Composio.
3. **Discord Message Content Intent off by default** for newly-created bots — see step 6.
4. **`localhost` vs `127.0.0.1` in Desktop OAuth callbacks** — abandoned (we use Composio now), but for any future direct OAuth: Google may reject `localhost`.
5. **mcp-remote stdin closes too fast** if you feed JSON-RPC via `printf` without a trailing `sleep` — proxy exits before auth flow completes. Mostly irrelevant now (Composio is HTTP MCP, no callback dance) but documented for posterity.
6. **Composio backend can flake** (occasional 401 "Failed to fetch API key information from DB") — wait it out; status.composio.dev shows incidents.
