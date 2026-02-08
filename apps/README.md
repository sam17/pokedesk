# Home Automation Services - Docker Swarm Deployment

This repository contains Docker services for home automation monitoring and data collection, deployed on a Docker Swarm cluster.

## Architecture

**Swarm Cluster:**
- **Manager Node:** `charmander.local` (192.168.1.58)
- **Worker Node:** `psyduck.local`

**Services:**
- **ha-monitoring:** Monitors Home Assistant availability and sends Telegram alerts
- **whoop-collector:** Collects and stores Whoop fitness data

## Prerequisites

- Docker Swarm cluster with 2+ nodes
- Docker registry access (DigitalOcean Container Registry)
- SSH access to swarm nodes
- Environment variables configured in `.env`

## Quick Start

### 1. Configure Environment Variables

Edit `.env` file with your credentials:

```bash
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# Home Assistant Configuration
HOME_ASSISTANT_IP=192.168.1.24

# Whoop API Configuration (if using whoop-collector)
WHOOP_CLIENT_ID=your_client_id
WHOOP_CLIENT_SECRET=your_client_secret
# ... etc
```

### 2. Deploy Services

Make the deployment script executable and run it:

```bash
chmod +x deploy.sh
./deploy.sh
```

The script will:
- ✓ Check Docker daemons on both nodes
- ✓ Verify swarm cluster health
- ✓ Deploy the service stack
- ✓ Show service status

### 3. Verify Deployment

Check service status:

```bash
# On charmander (manager node)
docker stack services ha-monitoring
docker service ps ha-monitoring_monitoring
```

View logs:

```bash
docker service logs ha-monitoring_monitoring -f
```

## Manual Deployment

If you prefer to deploy manually:

```bash
# SSH to swarm manager
ssh pi@charmander.local

# Deploy the stack
docker stack deploy -c docker-compose.yml ha-monitoring

# Check status
docker stack services ha-monitoring
```

## Service Configuration

### ha-monitoring

**Purpose:** Monitors Home Assistant availability via ping and HTTP checks. Sends Telegram notifications on failure.

**Environment Variables:**
- `HOME_ASSISTANT_IP` - IP address of Home Assistant instance
- `TELEGRAM_BOT_TOKEN` - Bot token from @BotFather
- `TELEGRAM_CHAT_ID` - Chat ID for notifications

**Placement:** Runs on worker nodes only

**Schedule:** Runs checks via cron (configured in `ha-monitoring/cronjob`)

### whoop-collector

**Purpose:** Collects Whoop fitness data and stores in database.

**Environment Variables:**
- `WHOOP_CLIENT_ID` - Whoop API client ID
- `WHOOP_CLIENT_SECRET` - Whoop API client secret
- `WHOOP_ACCESS_TOKEN` - OAuth access token
- `WHOOP_REFRESH_TOKEN` - OAuth refresh token
- `DATABASE_URL` - PostgreSQL connection string

**Placement:** Runs on worker nodes only

## Troubleshooting

### Services Not Starting

1. **Check node status:**
   ```bash
   docker node ls
   ```
   All nodes should show "Ready" status.

2. **Check if Docker is running on worker:**
   ```bash
   ssh pi@psyduck.local "docker info"
   ```
   If not running:
   ```bash
   ssh pi@psyduck.local "sudo systemctl start docker"
   ```

3. **Check for stale nodes:**
   ```bash
   docker node ls
   ```
   Remove stale nodes:
   ```bash
   docker node rm <node-id>
   ```

### Expired Swarm Certificates

If you see certificate expiration errors in Docker logs:

```bash
# On the worker node with expired cert
ssh pi@psyduck.local "docker swarm leave --force"

# Get join token from manager
ssh pi@charmander.local "docker swarm join-token worker"

# Rejoin the worker
ssh pi@psyduck.local "docker swarm join --token <token> charmander.local:2377"
```

### Service Stuck in Pending State

Check service constraints and errors:

```bash
docker service ps ha-monitoring_monitoring --no-trunc
```

Common issues:
- No suitable nodes (check node availability)
- Scheduling constraints not satisfied (check node labels/roles)
- Image pull failures (check registry authentication)

### Update Service Environment Variables

To update environment variables without redeploying:

```bash
docker service update \
  --env-add HOME_ASSISTANT_IP=192.168.1.24 \
  --env-add TELEGRAM_BOT_TOKEN=<token> \
  --env-add TELEGRAM_CHAT_ID=<chat_id> \
  ha-monitoring_monitoring
```

Or update `.env` file and redeploy:

```bash
./deploy.sh
```

## Useful Commands

### Stack Management

```bash
# Deploy/update stack
docker stack deploy -c docker-compose.yml ha-monitoring

# List stacks
docker stack ls

# List services in stack
docker stack services ha-monitoring

# Remove stack
docker stack rm ha-monitoring
```

### Service Management

```bash
# List all services
docker service ls

# Inspect service
docker service inspect ha-monitoring_monitoring

# View service logs
docker service logs ha-monitoring_monitoring -f

# Scale service
docker service scale ha-monitoring_monitoring=2

# Force update (redeploy)
docker service update --force ha-monitoring_monitoring
```

### Node Management

```bash
# List nodes
docker node ls

# Inspect node
docker node inspect psyduck

# Drain node (stop scheduling tasks)
docker node update --availability drain psyduck

# Make node active again
docker node update --availability active psyduck

# Remove node
docker node rm psyduck
```

### Registry Authentication

If using a private registry, create a registry auth config:

```bash
# Create docker config secret
docker swarm init  # if not already initialized
cat ~/.docker/config.json | docker config create registry-auth -
```

## Monitoring

### Check Service Health

```bash
# Quick status check
docker service ps ha-monitoring_monitoring

# Detailed status
docker service inspect ha-monitoring_monitoring --pretty

# Watch logs in real-time
docker service logs -f ha-monitoring_monitoring
```

### Verify Home Assistant Monitoring

The ha-monitoring service logs should show:

```
Starting HA monitoring script
Ping successful
Ping success: True
Curl successful
Curl success: True
Both ping and curl were successful.
```

If monitoring fails, you'll receive a Telegram notification.

## Development

### Building Images

Images are built and pushed to DigitalOcean Container Registry:

```bash
# Build ha-monitoring
cd ha-monitoring
docker build -t registry.digitalocean.com/pokedesk-cr/ha-monitoring:latest .
docker push registry.digitalocean.com/pokedesk-cr/ha-monitoring:latest
```

### Testing Locally

Test services locally before deploying to swarm:

```bash
docker-compose up -d
docker-compose logs -f
docker-compose down
```

## Security Notes

- `.env` file contains sensitive credentials - **never commit to git**
- Use `.env.example` as a template
- Swarm certificates expire periodically - rejoin nodes when needed
- Registry authentication is handled via Docker configs

## Contributing

When making changes:
1. Test locally with `docker-compose`
2. Build and push new image versions
3. Deploy to swarm with `./deploy.sh`
4. Monitor logs for issues

## Support

For issues related to:
- **Docker Swarm:** Check node status and swarm logs
- **ha-monitoring:** Check Home Assistant connectivity and Telegram bot
- **whoop-collector:** Check Whoop API credentials and database connectivity

---

Last updated: 2026-02-08
