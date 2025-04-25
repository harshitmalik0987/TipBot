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

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
client = TelegramClient(session_file, api_id, api_hash)

# In-memory dedupe
processed = set()

def rewrite_links(text: str, target_channel: str) -> str:
    tc = target_channel.lstrip('@')
    return re.sub(telegram_link_pattern, f'https://t.me/{tc}', text)

async def n1panel_add(service_id: int, link: str, quantity: int):
    url = (
        f"https://n1panel.com/api/v2?action=add&service={service_id}"
        f"&link={link}&quantity={quantity}&key={api_key}"
    )
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as resp:
                text = await resp.text()
                logging.info(f"n1panel service {service_id} → {text}")
        except Exception as e:
            logging.error(f"n1panel error: {e}")

@client.on(events.NewMessage)
async def forward_message(event):
    try:
        # DEBUG: did we even get here?
        logging.debug(f"[DEBUG] Event: chat_id={event.chat_id}, msg_id={event.message.id}, from={event.chat.username}")

        # Only process if this chat is one of our source entities
        if event.chat_id not in source_ids:
            return

        key = (event.chat_id, event.message.id)
        if key in processed:
            logging.debug("→ already processed, skipping")
            return
        processed.add(key)

        text = event.raw_text or ''
        photo = event.photo
        media = event.media

        # rewrite + join-prompt logic
        processed_text = rewrite_links(text, target_channel)
        if text.strip() and not re.search(join_message_pattern, text):
            processed_text += f"\n\nJoin Our Telegram Group for Fast Update https://t.me/{target_channel.lstrip('@')}"

        # forward to target
        if photo:
            sent = await client.send_file(target_entity, photo, caption=processed_text, link_preview=False)
        elif media:
            logging.info("→ skipping non-photo media")
            return
        else:
            sent = await client.send_message(target_entity, processed_text, link_preview=False)

        if sent:
            link = f"https://t.me/{target_channel.lstrip('@')}/{sent.id}"
            await n1panel_add(3183, link, random.randint(200, 250))
            await n1panel_add(3232, link, random.randint(10, 15))
        else:
            logging.warning("→ send returned no message")

    except Exception:
        logging.error("forward_message error:\n" + traceback.format_exc())

async def main():
    global target_entity, source_ids

    await client.start()
    me = await client.get_me()
    logging.info(f"Logged in as {me.username or me.first_name}")

    # Resolve target
    target_entity = await client.get_entity(target_channel)
    logging.info(f"Target → {target_entity.title or target_entity.username} ({target_entity.id})")

    # Resolve sources
    source_ids = []
    for ch in source_channels:
        try:
            ent = await client.get_entity(ch)
            source_ids.append(ent.id)
            logging.info(f"Source → {ch} resolved to {ent.id}")
        except Exception as e:
            logging.error(f"Could not resolve source {ch}: {e}")

    logging.info("Listening for new messages…")
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
