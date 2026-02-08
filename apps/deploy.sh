#!/bin/bash

# Deployment script for ha-monitoring on Docker Swarm
# This script deploys services to the swarm cluster running on charmander (manager) and psyduck (worker)

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
SWARM_MANAGER="pi@charmander.local"
SWARM_WORKER="pi@psyduck.local"
STACK_NAME="ha-monitoring"

echo -e "${GREEN}=== Docker Swarm Deployment Script ===${NC}"
echo ""

# Function to check if we're on the swarm manager
check_location() {
    if [ "$(hostname)" == "charmander" ]; then
        echo -e "${GREEN}✓ Running on swarm manager (charmander)${NC}"
        ON_MANAGER=true
    else
        echo -e "${YELLOW}→ Running from remote machine, will SSH to swarm manager${NC}"
        ON_MANAGER=false
    fi
}

# Function to run command (local or remote)
run_cmd() {
    if [ "$ON_MANAGER" = true ]; then
        eval "$1"
    else
        ssh "$SWARM_MANAGER" "$1"
    fi
}

# Check Docker daemon on both nodes
check_docker_daemons() {
    echo ""
    echo "Checking Docker daemons..."

    # Check manager
    if run_cmd "docker info > /dev/null 2>&1"; then
        echo -e "${GREEN}✓ Docker running on charmander (manager)${NC}"
    else
        echo -e "${RED}✗ Docker not running on charmander${NC}"
        exit 1
    fi

    # Check worker
    if ssh "$SWARM_WORKER" "docker info > /dev/null 2>&1"; then
        echo -e "${GREEN}✓ Docker running on psyduck (worker)${NC}"
    else
        echo -e "${YELLOW}! Docker not running on psyduck, attempting to start...${NC}"
        if ssh "$SWARM_WORKER" "sudo systemctl start docker"; then
            echo -e "${GREEN}✓ Docker started on psyduck${NC}"
            sleep 2
        else
            echo -e "${RED}✗ Failed to start Docker on psyduck${NC}"
            exit 1
        fi
    fi
}

# Check swarm status
check_swarm_status() {
    echo ""
    echo "Checking swarm status..."

    SWARM_STATUS=$(run_cmd "docker info --format '{{.Swarm.LocalNodeState}}'")

    if [ "$SWARM_STATUS" != "active" ]; then
        echo -e "${RED}✗ Swarm is not active${NC}"
        exit 1
    fi

    echo -e "${GREEN}✓ Swarm is active${NC}"

    # Check nodes
    echo ""
    echo "Swarm nodes:"
    run_cmd "docker node ls"

    # Count ready nodes
    READY_NODES=$(run_cmd "docker node ls --format '{{.Status}}' | grep -c Ready")
    if [ "$READY_NODES" -lt 2 ]; then
        echo -e "${YELLOW}! Warning: Only $READY_NODES node(s) ready${NC}"
    else
        echo -e "${GREEN}✓ All $READY_NODES nodes are ready${NC}"
    fi
}

# Deploy the stack
deploy_stack() {
    echo ""
    echo "Deploying stack: $STACK_NAME..."

    # Check if .env file exists
    if [ ! -f ".env" ]; then
        echo -e "${RED}✗ .env file not found${NC}"
        exit 1
    fi

    # Copy files to manager if running remotely
    if [ "$ON_MANAGER" = false ]; then
        echo "Copying files to swarm manager..."
        scp docker-compose.yml .env "$SWARM_MANAGER:~/"
    fi

    # Deploy the stack
    run_cmd "docker stack deploy -c docker-compose.yml $STACK_NAME"

    echo -e "${GREEN}✓ Stack deployed${NC}"
}

# Wait for services to be ready
wait_for_services() {
    echo ""
    echo "Waiting for services to start..."
    sleep 5

    # Show service status
    echo ""
    echo "Service status:"
    run_cmd "docker stack services $STACK_NAME"

    echo ""
    echo "Service tasks:"
    run_cmd "docker service ps ${STACK_NAME}_monitoring --no-trunc | head -5"
}

# Main execution
main() {
    check_location
    check_docker_daemons
    check_swarm_status
    deploy_stack
    wait_for_services

    echo ""
    echo -e "${GREEN}=== Deployment Complete ===${NC}"
    echo ""
    echo "Useful commands:"
    echo "  - View services:     docker stack services $STACK_NAME"
    echo "  - View tasks:        docker service ps ${STACK_NAME}_monitoring"
    echo "  - View logs:         docker service logs ${STACK_NAME}_monitoring"
    echo "  - Remove stack:      docker stack rm $STACK_NAME"
    echo ""
}

# Run main function
main
