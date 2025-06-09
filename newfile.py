
import asyncio
import logging
import re
import aiohttp
from telethon import TelegramClient, events
from telethon.errors import RPCError, SessionPasswordNeededError

# Configuration
SESSIONS = [
    {
        'name': 'Ankush',
        'session_file': 'ankush.session',
        'api_id': 7536366,
        'api_hash': '1ef0b51ab5b66fed13641d981ccb8389',
        'phone': '+919991207538',
        'is_main': True
    },
    {
        'name': 'Levi',
        'session_file': 'levi.session',
        'api_id': 24440214,
        'api_hash': 'b0a59a887f0f6fde4e3c3990f627a7b1',
        'phone': '+919050247534',
        'is_main': False
    },
    {
        'name': 'CoderNinja',
        'session_file': 'coderninja.session',
        'api_id': 22815674,
        'api_hash': '3aa83fb0fe83164b9fee00a1d0b31e5f',
        'phone': '+919350050226',
        'is_main': False
    },
    {
        'name': 'AsianGamer',
        'session_file': 'asiangamer.session',
        'api_id': 22001404,
        'api_hash': 'b1657c62edd096e74bfd1de603909b02',
        'phone': '+919354950340',
        'is_main': False
    },
    {
        'name': 'Ninja',
        'session_file': 'ninja.session',
        'api_id': 14039017,
        'api_hash': '68996f618f44f1a841f831419868b77a',
        'phone': '+918053622115',
        'is_main': False
    },
]

# Source and target channels
SOURCE_CHANNELS = ['@bottest991', '@haryanaschemes', '@speedjobs']
TARGET_CHANNEL = '@GovtJobAIert'
FORWARD_DELAY = 2  # seconds between forwards

# TinyURL tokens
TINYAPI_TOKEN1 = '19XBdAqwgXa1HdR2lV8XHOYxccCvZ0Yvd9u49F9vHSfRmrgjsqTuFxqyehOH'
TINYAPI_TOKEN2 = 'q1Z1dJrKI9kriIr391DbdcV1z56w9IYxOsN1RNLmCDah9Xl7STkNkM1CGfwv'
TINYAPI_TOKEN3 = 'ujI6352RQVrBRhFj63iwPLVvvpmARzezodG6NxCas4PSasij2TxsMLai6K11'

# Patterns
LINK_PATTERN = re.compile(r"https?://[A-Za-z0-9./?=-]+")
TME_PATTERN = re.compile(r"(?:https?://)?(?:t.me|telegram.me)/[A-Za-z0-9]+")
JOIN_PROMPT = re.compile(r"Join Our Telegram Group.*", re.IGNORECASE)

# Deduplication cache
processed_notices = set()

# Logging config
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Instantiate clients
dispatchers = []
for cfg in SESSIONS:
    client = TelegramClient(cfg['session_file'], cfg['api_id'], cfg['api_hash'])
    dispatchers.append((client, cfg))

# Helpers
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

    # all three failed → return original
    return url


def normalize_text(text: str) -> str:
    """Remove URLs and join prompts, collapse whitespace for dedupe."""
    text = LINK_PATTERN.sub('', text)
    text = JOIN_PROMPT.sub('', text)
    return ' '.join(text.split()).strip().lower()

async def authorize_clients():
    for client, cfg in dispatchers:
        await client.connect()
        if not await client.is_user_authorized():
            logging.info(f"Sending OTP to {cfg['name']} ({cfg['phone']})")
            await client.send_code_request(cfg['phone'])
            code = input(f"Enter code for {cfg['name']} ({cfg['phone']}): ")
            try:
                await client.sign_in(cfg['phone'], code)
            except SessionPasswordNeededError:
                pw = input(f"2FA password for {cfg['name']}: ")
                await client.sign_in(password=pw)
            me = await client.get_me()
            logging.info(f"{cfg['name']} logged in as {me.username or me.first_name}")

async def setup_handlers():
    # Main handler
    main_client, _ = next((c, cfg) for c, cfg in dispatchers if cfg['is_main'])

    @main_client.on(events.NewMessage(chats=SOURCE_CHANNELS, incoming=True))
    async def main_handler(event):
        msg = event.message
        # skip docs/videos
        if msg.document or msg.video:
            return
        text = msg.text or msg.raw_text or ''
        key = normalize_text(text)
        if not key or key in processed_notices:
            return
        processed_notices.add(key)

        # Process each URL
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

        # Repost
        if msg.photo:
            file = await event.client.download_media(msg)
            await event.client.send_file(TARGET_CHANNEL, file, caption=text, link_preview=False)
            logging.info(f"Main reposted photo to {TARGET_CHANNEL}")
        else:
            await event.client.send_message(TARGET_CHANNEL, text, link_preview=False)
            logging.info(f"Main reposted text to {TARGET_CHANNEL}")

    # Booster handlers
    for client, cfg in dispatchers:
        if cfg['is_main']:
            continue
        name = cfg['name']

        @client.on(events.NewMessage(chats=TARGET_CHANNEL, incoming=True))
        async def forward_handler(event, client=client, name=name):
            msg = event.message
            async for dlg in client.iter_dialogs():
                if not dlg.is_group:
                    continue
                try:
                    await event.forward_to(dlg.entity)
                    logging.info(f"{name} forwarded msg {msg.id} to group '{dlg.title}'")
                except RPCError as e:
                    logging.warning(f"{name} failed to forward to '{dlg.title}': {e}")
                await asyncio.sleep(FORWARD_DELAY)

async def main():
    await authorize_clients()
    await setup_handlers()
    await asyncio.gather(*(client.run_until_disconnected() for client, _ in dispatchers))

if __name__ == '__main__':
    asyncio.run(main())
    
