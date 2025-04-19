import os
import re
import logging
from telethon import TelegramClient, events
from telethon.sessions import StringSession

# ————— Configuration —————
# Required environment variables
api_id = int(os.getenv('TELEGRAM_API_ID', '22001404'))  # Default value provided but should be set in env
api_hash = os.getenv('TELEGRAM_API_HASH', 'b1657c62edd096e74bfd1de603909b02')  # Default value provided
session_str = os.getenv('STRING_SESSION')  # Must be generated and set in environment

# Channel configuration with defaults
raw_sources = os.getenv('SOURCE_CHANNELS', '@speedjobs,@haryana_jobs_in,@pubg_accounts_buy_sell,@haryanaschemes')
source_channels = [ch.strip().lstrip('@') for ch in raw_sources.split(',')]

raw_target = os.getenv('TARGET_CHANNEL', '@Govt_JobNotification').strip()
target_channel = raw_target if raw_target.startswith('@') else f'@{raw_target}'

# Pattern for cleaning messages
telegram_link_pattern = r'(?:https?://)?(?:telegram\.me|t\.me)/[A-Za-z0-9_]+'

# ————— Helpers —————
def strip_all_links(text: str) -> str:
    """Remove all Telegram links from text"""
    return re.sub(telegram_link_pattern, '', text).strip()

def strip_markdown(text: str) -> str:
    """Remove markdown formatting from text"""
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'__(.*?)__', r'\1', text)
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    text = re.sub(r'`(.*?)`', r'\1', text)
    text = re.sub(r'([^]+)([^)]+)', r'\1', text)
    return text

# Initialize client with StringSession
client = TelegramClient(StringSession(session_str), api_id, api_hash)

@client.on(events.NewMessage(chats=source_channels))
async def forward_message(event):
    """Handle incoming messages and forward them to target channel"""
    raw_text = event.raw_text or ''
    media = event.message.media
    chat_id = event.chat.username or event.chat.id
    logging.info(f"[{chat_id}] got message: {raw_text[:40]!r}")

    # Process message content
    no_link_text = strip_all_links(raw_text)
    caption = strip_markdown(no_link_text)

    try:
        if media:
            # Handle media with in-memory download
            media_bytes = await client.download_media(media, file=bytes)
            file_name = getattr(media, 'file_name', 'file')
            await client.send_file(
                target_channel,
                (media_bytes, file_name),
                caption=caption or None,
                link_preview=False
            )
            logging.info(f"    → Media sent ({file_name}).")
        else:
            # No media → just send text
            await client.send_message(
                target_channel,
                caption or " ",  # Using space as empty messages aren't allowed
                link_preview=False
            )
            logging.info("    → Text sent.")

    except Exception as e:
        logging.error(f"    ❌ Forwarding failed: {e}", exc_info=True)

def main():
    """Start the bot"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s'
    )
    logging.info(f"Starting bot: listening on {source_channels} → {target_channel}")
    client.start()
    client.run_until_disconnected()

if __name__ == '__main__':
    main()
