import os
import asyncio
import logging
import re
import traceback
import random
import aiohttp
from telethon import TelegramClient, events

# ——— Configuration ———
api_id       = int(os.getenv('TELEGRAM_API_ID', '22001404'))
api_hash     = os.getenv('TELEGRAM_API_HASH',   'b1657c62edd096e74bfd1de603909b02')
session_file = os.getenv('SESSION_FILE',        'user_session.session')

source_channels = os.getenv(
    'SOURCE_CHANNELS',
    '@speedjobs,@haryana_jobs_in,@bottest991,@haryanaschemes'
).split(',')

target_channel = os.getenv('TARGET_CHANNEL', '@Govt_JobNotification')
api_key        = '93600468f93f081f51123815b5b9f409'

telegram_link_pattern = r'(?:https?://)?(?:telegram\.me|t\.me)/[A-Za-z0-9_]+'
join_message_pattern  = r'Join Our Telegram Group for Fast Update\s*' + telegram_link_pattern

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

client = TelegramClient(session_file, api_id, api_hash)

# In‐memory dedupe set
processed = set()


def rewrite_links(text: str, target: str) -> str:
    tc = target.lstrip('@')
    return re.sub(telegram_link_pattern, f'https://t.me/{tc}', text)


async def n1panel_add(service_id: int, link: str, qty: int):
    url = (
        f"https://n1panel.com/api/v2?action=add&service={service_id}"
        f"&link={link}&quantity={qty}&key={api_key}"
    )
    async with aiohttp.ClientSession() as sess:
        try:
            async with sess.get(url) as resp:
                txt = await resp.text()
                logging.info(f"n1panel#{service_id} → {txt.strip()}")
        except Exception as e:
            logging.error(f"n1panel error: {e}")


async def forward_message(event):
    try:
        # Dedupe by (source_chat, source_msg)
        key = (event.chat_id, event.message.id)
        if key in processed:
            logging.debug("→ duplicate, skipping")
            return
        processed.add(key)

        text  = event.raw_text or ''
        photo = event.photo
        media = event.media

        # rewrite links & append join prompt if needed
        out = rewrite_links(text, target_channel)
        if text.strip() and not re.search(join_message_pattern, text):
            out += f"\n\nJoin Our Telegram Group for Fast Update https://t.me/{target_channel.lstrip('@')}"

        # send to target
        if photo:
            sent = await client.send_file(
                target_entity,
                photo,
                caption=out,
                link_preview=False
            )
        elif media:
            logging.info("→ non‐photo media skipped")
            return
        else:
            sent = await client.send_message(
                target_entity,
                out,
                link_preview=False
            )

        # trigger n1panel
        if sent:
            link = f"https://t.me/{target_channel.lstrip('@')}/{sent.id}"
            await n1panel_add(3183, link, random.randint(520, 600))
            await n1panel_add(3232, link, random.randint(12, 20))
        else:
            logging.warning("→ send failed, no message returned")

    except Exception:
        logging.error("forward_message error:\n" + traceback.format_exc())


async def main():
    global target_entity

    await client.start()
    me = await client.get_me()
    logging.info(f"Logged in as {me.username or me.first_name}")

    # resolve the target entity once
    target_entity = await client.get_entity(target_channel)
    logging.info(f"Will post into → {target_entity.title or target_entity.username} ({target_entity.id})")

    # resolve all source channels to numeric IDs
    src_ids = []
    for ch in source_channels:
        try:
            e = await client.get_entity(ch)
            src_ids.append(e.id)
            logging.info(f"Source channel {ch} → {e.id}")
        except Exception as e:
            logging.error(f"Failed to resolve {ch}: {e}")

    # now register the handler *only* on those IDs, only incoming
    client.add_event_handler(
        forward_message,
        events.NewMessage(chats=src_ids, incoming=True)
    )

    logging.info("Listening for new messages...")
    await client.run_until_disconnected()


if __name__ == '__main__':
    asyncio.run(main())
