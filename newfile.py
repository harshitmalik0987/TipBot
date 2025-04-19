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

# Define the Telegram link pattern globally
telegram_link_pattern = r'(?:https?://)?(?:telegram\.me|t\.me)/[A-Za-z0-9_]+'

# Helper function to rewrite Telegram links to the target channel
def rewrite_links(text: str, target_channel: str) -> str:
    """
    Rewrites any Telegram links in the text to point to the target channel.

    Args:
        text (str): The input text with possible Telegram links
        target_channel (str): The target channel handle (e.g., '@channelname')

    Returns:
        str: Text with rewritten links
    """
    tc = target_channel.lstrip('@')
    replacement = f'https://t.me/{tc}'
    return re.sub(telegram_link_pattern, replacement, text)

# Helper function to convert Markdown to plain text
def convert_markdown_to_plain_text(text: str) -> str:
    """
    Converts Markdown formatting in the text to plain text.

    Args:
        text (str): The input text with Markdown formatting

    Returns:
        str: Plain text with formatting removed
    """
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # Remove bold
    text = re.sub(r'__(.*?)__', r'\1', text)      # Remove underline
    text = re.sub(r'\*(.*?)\*', r'\1', text)      # Remove italic
    text = re.sub(r'`(.*?)`', r'\1', text)        # Remove code
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'\1', text)  # Remove link markup, keep text
    return text

# Event handler for new messages in source channels
@client.on(events.NewMessage(chats=source_channels))
async def forward_message(event):
    """
    Forwards messages from source channels to the target channel, processing text only if links are present.

    Args:
        event: The Telethon event object containing the message details
    """
    text = event.raw_text or ''
    media = event.message.media
    channel = event.chat.username or event.chat.id
    logging.info(f"Received message from {channel}: {text}")

    # Process the text: rewrite links and convert to plain text
    processed_text = rewrite_links(text, target_channel)
    plain_text = convert_markdown_to_plain_text(processed_text)

    try:
        if not media or (media and re.search(telegram_link_pattern, text)):
            # Send only text if there's no media or if there's a Telegram link
            await client.send_message(target_channel, plain_text, parse_mode=None)
            logging.info(f"Sent text-only message to {target_channel}")
        else:
            # Send media with caption if there's media and no Telegram links
            data = await client.download_media(media, file=bytes)
            await client.send_file(target_channel, data, caption=plain_text, parse_mode=None)
            logging.info(f"Sent media with caption to {target_channel}")
    except Exception as e:
        logging.error(f"Error processing message from {channel}: {e}")

# Main entry point
async def main():
    """Starts the Telegram client and keeps it running."""
    await client.start()
    logging.info(f"Bot started. Listening to: {source_channels}")
    await client.run_until_disconnected()

# Configure logging
logging.basicConfig(level=logging.INFO)

# Run the bot
if __name__ == '__main__':
    asyncio.run(main())
