# Personal Agent Setup Plan — OpenClaw + MetaClaw

## Decision Summary

- **OpenClaw** — Full personal AI agent runtime (messaging, tools, automations)
- **MetaClaw** — Transparent learning proxy that wraps OpenClaw, making it smarter over time
- These are complementary: MetaClaw sits on top of OpenClaw as a learning layer

## Infrastructure

- **Host:** `eevee.local` — Raspberry Pi 5 (dedicated to personal agents, isolated from Swarm)
- **Setup:** Two Docker containers on eevee — one per person
- **Why isolated:** Keeps unpredictable agent behavior off the home monitoring Swarm (charmander/psyduck)

| Container | User | Gateway Port | MetaClaw Proxy Port | Config Volume |
|---|---|---|---|---|
| `dobby` | Sam | 18789 | 30000 | `/opt/claw/sam/` |
| `hedwig` | Charu | 18790 | 30001 | `/opt/claw/charu/` |

Each container gets:
- Its own OpenClaw Gateway + config + Markdown memory
- Its own API keys and connected accounts (messaging, calendar, etc.)
- Its own MetaClaw proxy and skill files (Phase 2)
- Sandbox mode enabled independently

## Evaluation

### OpenClaw

| Attribute | Details |
|---|---|
| Purpose | Personal AI agent that acts on your behalf across apps |
| GitHub Stars | 328,000+ |
| License | MIT |
| Integrations | 23 messaging platforms, 50+ tool integrations, 100+ built-in skills |
| Architecture | Local Gateway WebSocket control plane (`ws://127.0.0.1:18789`) |
| Memory | Local Markdown files (never leaves your machine) |
| Autonomy | Heartbeats (30 min checks), cron jobs, webhooks |
| Skill Marketplace | ClawHub (700+ skills) |
| Setup | `npm install -g openclaw@latest` or install script; requires Node.js 24+ |
| Security Concerns | ClawHavoc incident (341 malicious ClawHub skills); CVE-2026-25253 (RCE, CVSS 8.8); 21K exposed instances; 35K email breach. Use sandbox mode. |

### MetaClaw

| Attribute | Details |
|---|---|
| Purpose | Proxy layer that makes any agent learn and evolve from conversations |
| GitHub Stars | 2,246 |
| License | MIT |
| Age | Created March 9, 2026 (very new) |
| Architecture | Async proxy on port 30000; intercepts traffic, injects skills, optional RL |
| Modes | `skills_only` (no GPU), `rl` (LoRA fine-tuning), `madmax` (scheduled RL) |
| Compatible With | OpenClaw, CoPaw, IronClaw, NanoClaw, NemoClaw, and more |
| Setup | `pip install -e .` then `metaclaw setup` (auto-detects OpenClaw) |
| Security Concerns | Path traversal RCE found and patched; project is <2 weeks old |

## Rollout Plan

### Phase 0 — Provision eevee

- Install Docker on eevee: `./init/install.sh` (or via `setup.sh eevee`)
- Create directory structure:
  ```
  /opt/claw/
    sam/          # Sam's config, memory, skills
    charu/      # Charu's config, memory, skills
  ```
- Set up `docker-compose.claw.yml` in `apps/claw/` with both containers
- Keep eevee **off the Swarm** — standalone Docker host, not a swarm node

### Phase 1 — OpenClaw (Sandbox Mode)

- Deploy both containers on eevee via compose
- Both run in **sandbox mode** (restricted permissions)
- Connect each instance to its own messaging channels and accounts
- Telegram: use separate bot tokens (ha-monitoring alerts use a different bot)
- Get comfortable with basic agent interactions before relaxing sandbox

### Phase 2 — MetaClaw (Skills Only)

- Add MetaClaw as a sidecar or baked into each container
- Each instance runs its own MetaClaw proxy (ports 30000 / 30001)
- Use `skills_only` mode — no GPU needed, Pi 5 handles this fine
- Skill files stored per-user in `/opt/claw/{sam,charu}/skills/`
- Relevant skills injected transparently on each conversation turn

### Phase 3 — MetaClaw RL (Optional, Later)

- Upgrade to `rl` or `madmax` mode for actual model fine-tuning
- `madmax` schedules training during sleep/idle/meetings (Google Calendar integration)
- Requires LoRA training backend (Tinker or MinT) — offloaded to cloud, not on the Pi
- Only pursue this after Phase 1 and 2 are stable

## Security Checklist

- [ ] Run both OpenClaw instances in sandbox mode initially
- [ ] Never expose eevee's Gateway ports (18789/18790) to public network
- [ ] Firewall eevee to only accept connections from LAN
- [ ] Audit all ClawHub skills before installation
- [ ] Keep OpenClaw and MetaClaw updated (both have had security patches)
- [ ] Don't give agent access to sensitive systems without guardrails
- [ ] Review MetaClaw skill files periodically (`/opt/claw/{sam,charu}/skills/`)
- [ ] Use separate API keys per instance — if one is compromised, revoke independently
- [ ] Keep eevee off the Docker Swarm to isolate from home monitoring infra
