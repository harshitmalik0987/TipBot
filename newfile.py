import asyncio
import logging
import re
import aiohttp
from telethon import TelegramClient, events
from telethon.errors import RPCError, SessionPasswordNeededError

# Configuration for only Ankush Malik
SESSION = {
    'name': 'Ankush',
    'session_file': 'ankush.session',
    'api_id': 7536366,
    'api_hash': '1ef0b51ab5b66fed13641d981ccb8389',
    'phone': '+919991207538'
}

# Source and target channels
SOURCE_CHANNELS = ['@bottest991', '@haryanaschemes', '@speedjobs']
TARGET_CHANNEL = '@GovtJobAIert'

# TinyURL tokens
TINYAPI_TOKEN1 = '19XBdAqwgXa1HdR2lV8XH946ccCvZ0Yvd9u49F9vHSfRmrgjsqTuFxqyehOH'
TINYAPI_TOKEN2 = 'q1Z1dJrKI9kriIr391D764V1z56w9IYxOsN1RNLmCDah9Xl7STkNkM1CGfwv'
TINYAPI_TOKEN3 = 'ujI6352RQVrBRhFj64976PLVvvpmARzezodG6NxCas4PSasij2TxsMLai6K11'

# Patterns
LINK_PATTERN = re.compile(r"https?://[A-Za-z0-9./?=-]+")
TME_PATTERN = re.compile(r"(?:https?://)?(?:t.me|telegram.me)/[A-Za-z0-9]+")

# Logging config
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Instantiate single client
client = TelegramClient(SESSION['session_file'], SESSION['api_id'], SESSION['api_hash'])

# Helper function to shorten URLs
async def shorten_url(url: str) -> str:
    """
    Shorten via TinyURL using up to three different API tokens.
    If all three attempts fail, returns the original URL.
    """
    api_url = 'https://api.tinyurl.com/create'
    headers_template = {
        'Authorization': 'Bearer {}',
        'Content-Type': 'application/json'
    }
    tokens = [TINYAPI_TOKEN1, TINYAPI_TOKEN2, TINYAPI_TOKEN3]

    for token in tokens:
        try:
            headers = {
                'Authorization': headers_template['Authorization'].format(token),
                'Content-Type': headers_template['Content-Type']
            }
            async with aiohttp.ClientSession() as session:
                async with session.post(api_url, json={'url': url}, headers=headers, timeout=5) as resp:
                    data = await resp.json()
                    short = data.get('data', {}).get('tiny_url')
                    if short:
                        return short
                    else:
                        logging.warning(f"TinyURL ({token[:8]}…) returned no data: {data}")
        except Exception as e:
            logging.warning(f"TinyURL ({token[:8]}…) request failed: {e}")
    return url  # Return original if all attempts fail

# Authorize the single client
async def authorize_client():
    await client.connect()
    if not await client.is_user_authorized():
        logging.info(f"Sending OTP to {SESSION['name']} ({SESSION['phone']})")
        await client.send_code_request(SESSION['phone'])
        code = input(f"Enter code for {SESSION['name']} ({SESSION['phone']}): ")
        try:
            await client.sign_in(SESSION['phone'], code)
        except SessionPasswordNeededError:
            pw = input(f"2FA password for {SESSION['name']}: ")
            await client.sign_in(password=pw)
        me = await client.get_me()
        logging.info(f"{SESSION['name']} logged in as {me.username or me.first_name}")

# Set up message handler
async def setup_handlers():
    @client.on(events.NewMessage(chats=SOURCE_CHANNELS, incoming=True))
    async def main_handler(event):
        msg = event.message
        # Skip documents and videos
        if msg.document or msg.video:
            return
        
        text = msg.text or msg.raw_text or ''
        if not text:
            return

        # Process URLs in the message
        async def process_text(txt: str) -> str:
            parts = []
            last = 0
            for m in LINK_PATTERN.finditer(txt):
                url = m.group(0)
                short = await shorten_url(url) if not TME_PATTERN.match(url) else f'https://t.me/{TARGET_CHANNEL.lstrip("@")}'
                parts.append(txt[last:m.start()])
                parts.append(short)
                last = m.end()
            parts.append(txt[last:])
            return ''.join(parts)

        text = await process_text(text)

        # Repost to target channel
        if msg.photo:
            file = await client.download_media(msg)
            await client.send_file(TARGET_CHANNEL, file, caption=text, link_preview=False)
            logging.info(f"Reposted photo to {TARGET_CHANNEL}")
        else:
            await client.send_message(TARGET_CHANNEL, text, link_preview=False)
            logging.info(f"Reposted text to {TARGET_CHANNEL}")

# Main execution
async def main():
    await authorize_client()
    await setup_handlers()
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
