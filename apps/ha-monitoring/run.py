import subprocess
from telegram import Bot
import asyncio
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

home_assistant_ip = os.getenv('HOME_ASSISTANT_IP')


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


if __name__ == "__main__":
    logger.info("Starting HA monitoring script")

    ping_success = pingHA()
    logger.info(f"Ping success: {ping_success}")
    curl_success = curlHA()
    logger.info(f"Curl success: {curl_success}")

    if not ping_success and not curl_success:
        message = "Both ping and curl failed."
        asyncio.run(sendNotification(message))
    elif not ping_success:
        message = "Ping failed, but curl was successful."
        asyncio.run(sendNotification(message))
    elif not curl_success:
        message = "Curl failed, but ping was successful."
        asyncio.run(sendNotification(message))
    else:
        logger.info("Both ping and curl were successful.")
