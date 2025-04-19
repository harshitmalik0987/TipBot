import os
import nest_asyncio
import asyncio
import re
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

# Helper function to rewrite Telegram links to the target channel
def rewrite_links(text: str, target_channel: str) -> str:
    """
    Rewrites any Telegram links in the text to point to the target channel.
    
    Args:
        text (str): The input text containing possible Telegram links
        target_channel (str): The target channel handle (e.g., '@channelname')
    
    Returns:
        str: Text with rewritten links
    """
    pattern = r'(?:https?://)?(?:telegram\.me|t\.me)/[A-Za-z0-9_]+'
    tc = target_channel.lstrip('@')
    replacement = f'https://t.me/{tc}'
    return re.sub(pattern, replacement, text)

# Helper function to convert Markdown to HTML
def convert_markdown_to_html(text: str) -> str:
    """
    Converts Markdown formatting in the text to HTML tags.
    
    Args:
        text (str): The input text with Markdown formatting
    
    Returns:
        str: Text with HTML formatting
    """
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)  # Bold
    text = re.sub(r'__(.*?)__', r'<u>\1</u>', text)      # Underline
    text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)      # Italic
    text = re.sub(r'`(.*?)`', r'<code>\1</code>', text)  # Code
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)  # Links
    return text

# Event handler for new messages in source channels
@client.on(events.NewMessage(chats=source_channels))
async def forward_message(event):
    """
    Forwards messages from source channels to the target channel, processing text and media.
    
    Args:
        event: The Telethon event object containing the message details
    """
    text = event.raw_text or ''
    media = event.message.media

    # Process the text: rewrite links and convert to HTML
    text = rewrite_links(text, target_channel)
    html = convert_markdown_to_html(text)

    # Forward the message with or without media
    if not media:
        await client.send_message(target_channel, html, parse_mode='HTML')
    else:
        data = await client.download_media(media, file=bytes)
        await client.send_file(target_channel, data, caption=html, parse_mode='HTML')

# Main entry point
async def main():
    """Starts the Telegram client and keeps it running."""
    await client.start()
    print(f"Bot running. Listening on {source_channels}")
    await client.run_until_disconnected()

# Run the bot
if __name__ == '__main__':
    asyncio.run(main())
