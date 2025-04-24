import os
import asyncio
import logging
import re
import traceback
import random
import aiohttp
from telethon import TelegramClient, events

# Configuration
api_id = int(os.getenv('TELEGRAM_API_ID', '22001404'))
api_hash = os.getenv('TELEGRAM_API_HASH', 'b1657c62edd096e74bfd1de603909b02')
session_file = os.getenv('SESSION_FILE', 'user_session.session')

source_channels = os.getenv(
    'SOURCE_CHANNELS',
    '@speedjobs,@haryana_jobs_in,@bottest991,@haryanaschemes'
).split(',')

target_channel = os.getenv('TARGET_CHANNEL', '@Govt_JobNotification')
api_key = '93600468f93f081f51123815b5b9f409'

# Regex patterns
telegram_link_pattern = r'(?:https?://)?(?:telegram\.me|t\.me)/[A-Za-z0-9_]+'
join_message_pattern = r'Join Our Telegram Group for Fast Update\s*' + telegram_link_pattern

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Telethon client
client = TelegramClient(session_file, api_id, api_hash)
target_entity = None

# Replace Telegram links with your channel link
def rewrite_links(text: str, target_channel: str) -> str:
    tc = target_channel.lstrip('@')
    return re.sub(telegram_link_pattern, f'https://t.me/{tc}', text)

# Make n1panel API calls
async def n1panel_add(service_id: int, link: str, quantity: int):
    url = (
        f"https://n1panel.com/api/v2?action=add&service={service_id}"
        f"&link={link}&quantity={quantity}&key={api_key}"
    )
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as resp:
                text = await resp.text()
                logging.info(f"n1panel (service {service_id}) response: {text}")
        except Exception as e:
            logging.error(f"Error calling n1panel API: {e}")

# Event handler
@client.on(events.NewMessage(chats=source_channels))
async def forward_message(event):
    try:
        text = event.raw_text or ''
        media = event.message.media
        photo = event.photo
        channel_username = event.chat.username or ''

        logging.info(f"New message from {channel_username or event.chat.id}")

        has_join_message = re.search(join_message_pattern, text) is not None
        processed_text = rewrite_links(text, target_channel)

        if not has_join_message and text.strip():
            processed_text += f"\n\nJoin Our Telegram Group for Fast Update https://t.me/{target_channel.lstrip('@')}"

        sent_msg = None

        if photo:
            # Send photo with caption and no link preview
            sent_msg = await client.send_file(
                target_entity,
                file=photo,
                caption=processed_text,
                link_preview=False
            )
        elif media:
            logging.info("Skipped non-photo media.")
            return
        else:
            # Send text message with no link preview
            sent_msg = await client.send_message(
                target_entity,
                processed_text,
                link_preview=False
            )

        # Get link of the posted message in the target channel
        if sent_msg:
            post_link = f"https://t.me/{target_channel.lstrip('@')}/{sent_msg.id}"
            await n1panel_add(3183, post_link, random.randint(200, 250))
            await n1panel_add(3232, post_link, random.randint(10, 15))
        else:
            logging.warning("Message not sent, skipping API call.")

    except Exception:
        logging.error("Error in forward_message:\n" + traceback.format_exc())

# Main runner
async def main():
    global target_entity
    await client.start()
    me = await client.get_me()
    logging.info(f"Logged in as {me.username or me.first_name}")

    target_entity = await client.get_entity(target_channel)
    logging.info(f"Target channel resolved: {target_entity.title or target_entity.username}")

    logging.info(f"Listening to source channels: {source_channels}")
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
