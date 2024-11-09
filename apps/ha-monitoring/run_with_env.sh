   #!/bin/bash

   echo "Running run_with_env.sh script"
   # Source environment variables from the Docker environment
   export TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
   export TELEGRAM_CHAT_ID=${TELEGRAM_CHAT_ID}
   echo "TELEGRAM_BOT_TOKEN: $TELEGRAM_BOT_TOKEN"
   echo "TELEGRAM_CHAT_ID: $TELEGRAM_CHAT_ID"

   # Run the Python script
   /usr/local/bin/python /app/run.py