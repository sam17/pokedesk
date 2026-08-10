FROM ghcr.io/openclaw/openclaw:latest

USER root

# System packages for calendar skills
RUN apt-get update -qq && \
    apt-get install -y -qq --no-install-recommends \
    python3-pip \
    vdirsyncer \
    khal \
    cargo \
    docker.io \
    chromium && \
    rm -rf /var/lib/apt/lists/*

# Python packages
RUN pip3 install --break-system-packages gcalcli google-api-python-client google-auth google-auth-oauthlib google-auth-httplib2

# Node global packages
RUN npm i -g clawdhub undici mcp-remote @tobilu/qmd

USER node
