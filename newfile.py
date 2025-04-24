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
    Forwards messages from source channels to the target channel with all text in bold.

    Args:
        event: The Telethon event object containing the message details
    """
    text = event.raw_text or ''
    media = event.message.media
    channel = event.chat.username or str(event.chat.id)
    logging.info(f"Received from {channel}: Text='{text}', Has Media={bool(media)}")

    # Check if the text contains "Join Our Telegram Group for Fast Update" with any Telegram link
    has_join_message = re.search(join_message_pattern, text) is not None

    # Process the text: rewrite links and convert to plain text
    processed_text = rewrite_links(text, target_channel)
    plain_text = convert_markdown_to_plain_text(processed_text)

    # Append the join message if the pattern is not present and there is text
    if not has_join_message and text.strip():
        plain_text += "\n\nJoin Our Telegram Group for Fast Update https://t.me/Govt_JobNotification"

    try:
        # Only send if there's text to avoid empty messages
        if plain_text.strip():
            # Apply bold formatting
            bold_text = '**' + plain_text + '**'
            # Log based on message type
            if media and re.search(telegram_link_pattern, text):
                logging.info(f"Sent text-only (link detected) to {target_channel}: {plain_text}")
            else:
                logging.info(f"Sent text to {target_channel}: {plain_text}")
            # Send with Markdown parsing for bold
            await client.send_message(target_channel, bold_text, parse_mode='md')
        elif media:
            logging.info(f"Skipped photo-only message from {channel}")
        else:
            logging.info(f"Skipped empty text message from {channel}")
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
