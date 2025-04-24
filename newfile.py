import os
import nest_asyncio
import asyncio
import re
import logging
from telethon import TelegramClient, events

# Allow multiple async frameworks in one loop
nest_asyncio.apply()

# Configuration
api_id = int(os.getenv('TELEGRAM_API_ID', '22001404'))
api_hash = os.getenv('TELEGRAM_API_HASH', 'b1657c62edd096e74bfd1de603909b02')
session_file = os.getenv('SESSION_FILE', 'user_session.session')
source_channels = os.getenv(
    'SOURCE_CHANNELS',
    '@speedjobs,@haryana_jobs_in,@pubg_accounts_buy_sell,@haryanaschemes'
).split(',')
target_channel = os.getenv('TARGET_CHANNEL', '@Govt_JobNotification')

# Initialize Telethon client
client = TelegramClient(session_file, api_id, api_hash)

# Define the Telegram link pattern
telegram_link_pattern = r'(?:https?://)?(?:telegram\.me|t\.me)/[A-Za-z0-9_]+'

# Define the pattern to detect "Join Our Telegram Group for Fast Update" with any Telegram link
join_message_pattern = r'Join Our Telegram Group for Fast Update\s*' + telegram_link_pattern

# Helper function to rewrite Telegram links to the target channel
def rewrite_links(text: str, target_channel: str) -> str:
    """
    Rewrites any Telegram links in the text to point to the target channel.
    """
    tc = target_channel.lstrip('@')
    replacement = f'https://t.me/{tc}'
    return re.sub(telegram_link_pattern, replacement, text)

# Event handler for new messages in source channels
@client.on(events.NewMessage(chats=source_channels))
async def forward_message(event):
    """
    Forwards messages from source channels to the target channel, processing text as needed.
    """
    text = event.raw_text or ''
    media = event.message.media
    channel = event.chat.username or str(event.chat.id)
    logging.info(f"Received from {channel}: Text='{text}', Has Media={bool(media)}")

    # Check if the text contains "Join Our Telegram Group for Fast Update" with any Telegram link
    has_join_message = re.search(join_message_pattern, text) is not None

    # Rewrite any Telegram links to the target channel
    processed_text = rewrite_links(text, target_channel)

    # Append the message only if the pattern is not present and there is text
    if not has_join_message and text.strip():
        processed_text += "\n\nJoin Our Telegram Group for Fast Update https://t.me/Govt_JobNotification"

    try:
        if media and re.search(telegram_link_pattern, text):
            # If media and a Telegram link are present, send only text and discard media
            await client.send_message(target_channel, processed_text, parse_mode=None)
            logging.info(f"Sent text-only (link detected) to {target_channel}: {processed_text}")
        elif media and not text.strip():
            # If only a photo is sent (no text), skip forwarding
            logging.info(f"Skipped photo-only message from {channel}")
        else:
            # Forward text-only messages or text with media (no links)
            await client.send_message(target_channel, processed_text, parse_mode=None)
            logging.info(f"Sent text to {target_channel}: {processed_text}")
    except Exception as e:
        logging.error(f"Error processing message from {channel}: {e}")

# Main entry point
async def main():
    """Starts the Telegram client and keeps it running."""
    await client.start()
    logging.info(f"Bot started. Listening to: {source_channels}")
    await client.run_until_disconnected()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Run the bot
if __name__ == '__main__':
    asyncio.run(main())
