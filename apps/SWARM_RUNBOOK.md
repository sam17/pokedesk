# Swarm Cluster Runbook

Notes from debugging and fixing the Docker Swarm cluster (Feb–Mar 2026).

## Incident: Services showing 0/1 replicas

**Symptom:** `docker service ls` on charmander shows `0/1` for all services.

**Root cause:** psyduck (worker) lost connection to the swarm manager. Two sub-causes discovered:

### 1. Docker daemon not running on psyduck

```bash
# Check
ssh pi@psyduck.local "docker info 2>&1 | head -5"

# Fix
ssh pi@psyduck.local "sudo systemctl start docker"
```

### 2. Swarm advertise-addr IP drift (the real problem)

The swarm was initialized with `--advertise-addr 192.168.1.51` (charmander's old DHCP IP). When the IP changed to `.58`, psyduck could no longer reach the manager at `.51:2377`. Rejoining psyduck with the correct IP was a band-aid — the swarm's internal raft log still stored `.51`, so any reconnect attempt would fail again.

**Permanent fix applied (2026-03-01):**

1. Set static IP on charmander via NetworkManager:
   ```bash
   sudo nmcli connection modify preconfigured \
     ipv4.method manual \
     ipv4.addresses 192.168.1.58/24 \
     ipv4.gateway 192.168.1.1 \
     ipv4.dns 192.168.1.1
   sudo nmcli connection up preconfigured
   ```

2. Tore down and reinitialized the swarm with the correct IP:
   ```bash
   # Remove stacks first
   docker stack rm ha-monitoring
   docker stack rm metrics

   # Save registry-auth config content before leaving
   docker config inspect registry-auth --format '{{.Spec.Data}}' > /tmp/registry-auth-b64.txt

   # Leave swarm on both nodes
   ssh pi@psyduck.local "docker swarm leave --force"
   docker swarm leave --force

   # Reinit with correct static IP
   docker swarm init --advertise-addr 192.168.1.58

   # Rejoin psyduck (use token from init output)
   ssh pi@psyduck.local "docker swarm join --token <token> 192.168.1.58:2377"
   ```

3. Recreated the `registry-auth` config:
   ```bash
   cat /tmp/registry-auth-b64.txt | base64 -d | docker config create registry-auth -
   ```

4. Redeployed stacks. **Important:** `docker stack deploy` does NOT support `env_file` — env vars must be set in the shell or added via `docker service update --env-add`:
   ```bash
   # Source .env so ${VAR} substitution works in compose files
   source ~/.env
   docker stack deploy -c docker-compose.yml ha-monitoring
   docker stack deploy -c docker-compose.metrics.yml metrics

   # Then add any vars that didn't come through (check with docker exec <container> env):
   docker service update \
     --env-add DATABASE_URL=<value> \
     --env-add WHOOP_ACCESS_TOKEN=<value> \
     --env-add WHOOP_REFRESH_TOKEN=<value> \
     --env-add WHOOP_CLIENT_ID=<value> \
     --env-add WHOOP_CLIENT_SECRET=<value> \
     metrics_whoop-collector
   ```

## Whoop OAuth token refresh

Access tokens expire in 1 hour. Refresh tokens expire after ~7 days of inactivity. When both expire, manual re-authentication is needed.

### Re-authentication steps

1. Generate authorization URL (run inside the whoop-collector container or locally):
   ```python
   import os, secrets, hashlib, base64
   client_id = os.getenv('WHOOP_CLIENT_ID')  # or hardcode
   code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode().rstrip('=')
   code_challenge = base64.urlsafe_b64encode(
       hashlib.sha256(code_verifier.encode()).digest()
   ).decode().rstrip('=')
   state = secrets.token_urlsafe(32)
   scope = 'offline+read:recovery+read:cycles+read:sleep+read:workout+read:profile'
   redirect = 'http%3A%2F%2Flocalhost%3A8080%2Fcallback'
   url = ('https://api.prod.whoop.com/oauth/oauth2/auth'
       + '?client_id=' + client_id
       + '&redirect_uri=' + redirect
       + '&response_type=code'
       + '&scope=' + scope
       + '&state=' + state
       + '&code_challenge=' + code_challenge
       + '&code_challenge_method=S256')
   print(url)
   print('CODE_VERIFIER=' + code_verifier)
   ```

2. Open URL in browser, log in to Whoop, authorize.

3. Copy the `code=` value from the redirect URL.

4. Exchange for tokens:
   ```python
   import requests
   resp = requests.post('https://api.prod.whoop.com/oauth/oauth2/token', data={
       'grant_type': 'authorization_code',
       'code': '<the code>',
       'redirect_uri': 'http://localhost:8080/callback',
       'client_id': '<client_id>',
       'client_secret': '<client_secret>',
       'code_verifier': '<code_verifier from step 1>',
   })
   print(resp.json())  # contains access_token and refresh_token
   ```

5. Update the running service:
   ```bash
   docker service update \
     --env-add WHOOP_ACCESS_TOKEN=<new_token> \
     --env-add WHOOP_REFRESH_TOKEN=<new_refresh_token> \
     metrics_whoop-collector
   ```

6. Update `apps/.env` on your local machine with the new tokens for future deploys.

### Scope encoding gotcha

Whoop's OAuth server does NOT decode `%3A` (percent-encoded colon) in scope names. The scope parameter must use:
- Literal colons: `read:recovery` (not `read%3Arecovery`)
- `+` for spaces between scopes (not `%20`, not literal spaces)

Example: `scope=offline+read:recovery+read:cycles+read:sleep+read:workout+read:profile`

## Backfilling missed Whoop data

When the collector was down and data is missing:

```bash
# Check for gaps
ssh pi@psyduck.local "docker exec <container> python3 -c \"
import psycopg2, os
conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cur = conn.cursor()
cur.execute(\\\"SELECT DISTINCT matcheddate FROM raw_data WHERE source='whoop' ORDER BY matcheddate DESC LIMIT 30\\\")
for r in cur.fetchall(): print(r[0])
conn.close()
\""

# Backfill a specific date range (e.g., 11 days starting from Feb 9)
docker exec <container> python3 /app/whoop_import.py --date 2026-02-09 --days 11

# Backfill from last data point to today
docker exec <container> python3 /app/whoop_import.py --from-last
```

**Note:** `--from-last` only checks the MAX date in the database. It won't detect interior gaps. Always query distinct dates to verify.

## docker stack deploy vs env_file

`docker stack deploy` silently ignores the `env_file:` directive in compose files. Environment variables set via `${VAR}` substitution in the `environment:` section only work if the variables are exported in the shell at deploy time. After deploying, always verify env vars reached the container:

```bash
docker exec <container> env | grep DATABASE
```

If vars are missing, use `docker service update --env-add` to set them.

## Quick health check

```bash
# Full status check
ssh pi@charmander.local "docker node ls && echo '---' && docker service ls"

# Should show:
# - Both nodes: Ready/Active
# - All services: 1/1 replicas
```
