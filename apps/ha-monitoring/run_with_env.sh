#!/bin/bash
echo "Running run_with_env.sh script"

# Source the environment file
. /etc/environment

echo "TELEGRAM_BOT_TOKEN: $TELEGRAM_BOT_TOKEN"
echo "TELEGRAM_CHAT_ID: $TELEGRAM_CHAT_ID"
echo "HA_API_URL: $HOME_ASSISTANT_IP"

# Run the Python script and redirect output
exec /usr/local/bin/python /app/run.py