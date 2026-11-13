import subprocess
from telegram import Bot
import asyncio
import os
import json
import time
import logging
from datetime import datetime

# Use IST for log + message timestamps (container clock is otherwise ~UTC).
os.environ['TZ'] = os.getenv('TZ', 'Asia/Kolkata')
try:
    time.tzset()
except Exception:
    pass

# Configure logging (timestamps now carry the timezone)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S %Z'
)
logger = logging.getLogger(__name__)

home_assistant_ip = os.getenv('HOME_ASSISTANT_IP')
# Persisted up/down state so we alert once per transition instead of every run.
# Mount a volume at this path to keep state across container restarts.
STATE_FILE = os.getenv('HA_STATE_FILE', '/tmp/ha_monitoring_state.json')


def pingHA():
    # Ping homeassistant.local and check for at least 3 successful responses
    try:
        response = subprocess.run(
            ['ping', '-c', '3', f'{home_assistant_ip}'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        if response.returncode == 0:
            logger.info("Ping successful")
            return True
        else:
            logger.warning("Ping failed")
            return False
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return False


def curlHA():
    # Curl homeassistant.local and check for a 200 response
    try:
        response = subprocess.run(
            ['curl', '-I', f'http://{home_assistant_ip}:8123'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        if response.returncode == 0:
            logger.info("Curl successful")
            return True
        else:
            logger.warning("Curl failed")
            return False
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return False


async def sendNotification(message):
    # Send a notification to the user via Telegram
    try:
        bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        chat_id = os.getenv('TELEGRAM_CHAT_ID')
        bot = Bot(token=bot_token)
        await bot.send_message(chat_id=chat_id, text=message)
        logger.info("Notification sent successfully")
    except Exception as e:
        logger.error(f"An error occurred while sending notification: {e}")


def read_state():
    # Default to healthy on first run / unreadable state so we don't fire a
    # spurious "recovered" message and only alert if HA is actually down.
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except Exception:
        return {"healthy": True}


def write_state(healthy):
    try:
        with open(STATE_FILE, 'w') as f:
            json.dump({"healthy": healthy}, f)
    except Exception as e:
        logger.error(f"Could not write state file {STATE_FILE}: {e}")


if __name__ == "__main__":
    logger.info("Starting HA monitoring script")

    ping_success = pingHA()
    curl_success = curlHA()
    logger.info(f"Ping success: {ping_success}, Curl success: {curl_success}")

    healthy = ping_success and curl_success
    was_healthy = read_state().get("healthy", True)
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S %Z')

    if healthy and not was_healthy:
        # Recovery: HA came back up.
        asyncio.run(sendNotification(
            f"✅ Home Assistant recovered at {now} (ping + HTTP both OK)."))
    elif not healthy and was_healthy:
        # First transition to unhealthy -> alert once, with detail.
        if not ping_success and not curl_success:
            detail = "both ping and HTTP failed"
        elif not ping_success:
            detail = "ping failed (HTTP OK)"
        else:
            detail = "HTTP check failed (ping OK)"
        asyncio.run(sendNotification(
            f"⚠️ Home Assistant DOWN at {now}: {detail}."))
    elif not healthy:
        # Still down; already alerted on the transition, don't re-spam.
        logger.info("Still unhealthy; down alert already sent, not re-notifying.")
    else:
        logger.info("Both ping and curl were successful; no state change.")

    write_state(healthy)
