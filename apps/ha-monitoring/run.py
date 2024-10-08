import subprocess
from telegram import Bot
import asyncio
import os


def pingHA():
    # Ping homeassistant.local and check for at least 3 successful responses
    try:
        response = subprocess.run(
            ['ping', '-c', '3', 'homeassistant.local'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        if response.returncode == 0:
            print("Ping successful")
            return True
        else:
            print("Ping failed")
            return False
    except Exception as e:
        print(f"An error occurred: {e}")
        return False


def curlHA():
    # Curl homeassistant.local and check for a 200 response
    try:
        response = subprocess.run(
            ['curl', '-I', 'http://homeassistant.local:8123'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        if response.returncode == 0:
            print("Curl successful")
            return True
        else:
            print("Curl failed")
            return False
    except Exception as e:
        print(f"An error occurred: {e}")
        return False


async def sendNotification(message):
    # Send a notification to the user via Telegram
    try:
        bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        chat_id = os.getenv('TELEGRAM_CHAT_ID')
        bot = Bot(token=bot_token)
        await bot.send_message(chat_id=chat_id, text=message)
        print("Notification sent successfully")
    except Exception as e:
        print(f"An error occurred while sending notification: {e}")


if __name__ == "__main__":
    ping_success = pingHA()
    curl_success = curlHA()

    if ping_success and curl_success:
        message = "Both ping and curl were successful."
    elif not ping_success and not curl_success:
        message = "Both ping and curl failed."
    elif not ping_success:
        message = "Ping failed, but curl was successful."
    else:
        message = "Curl failed, but ping was successful."

    asyncio.run(sendNotification(message))

