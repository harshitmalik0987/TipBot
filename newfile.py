import os import asyncio import re import logging import random import aiohttp from telethon import TelegramClient, events, errors

Configuration

API_ID = int(os.getenv('TELEGRAM_API_ID', '22001404')) API_HASH = os.getenv('TELEGRAM_API_HASH', 'b1657c62edd096e74bfd1de603909b02') SESSION_FILE = os.getenv('SESSION_FILE', 'user_session.session') SOURCE_CHANNELS = os.getenv( 'SOURCE_CHANNELS', '@speedjobs,@haryana_jobs_in,@pubg_accounts_buy_sell,@haryanaschemes' ).split(',') TARGET_CHANNEL = os.getenv('TARGET_CHANNEL', '@Govt_JobNotification')

N1Panel API configuration

API_KEY = os.getenv('N1PANEL_API_KEY', '93600468f93f081f51123815b5b9f409') SERVICE1 = int(os.getenv('SERVICE1_ID', 3183)) SERVICE2 = int(os.getenv('SERVICE2_ID', 3232))

Patterns

TELEGRAM_LINK_RE = re.compile(r"(?:https?://)?(?:telegram.me|t.me)/[A-Za-z0-9_]+") JOIN_MSG_RE = re.compile( r"Join Our Telegram Group for Fast Update\s*" + TELEGRAM_LINK_RE.pattern ) URL_RE = re.compile(r"https?://\S+")

Initialize client

client = TelegramClient(SESSION_FILE, API_ID, API_HASH) http_session: aiohttp.ClientSession

def rewrite_links(text: str) -> str: """Replace any Telegram links in text with the target channel link.""" tc = TARGET_CHANNEL.lstrip('@') return TELEGRAM_LINK_RE.sub(f'https://t.me/{tc}', text)

def strip_markdown(text: str) -> str: """Convert basic Markdown formatting to plain text.""" patterns = [ (r"**(.?)**", r"\1"), (r"__(.?)__", r"\1"), (r"*(.*?)*", r"\1"), (r"(.*?)", r"\1"), (r"]+)([^)]+)", r"\1"), ] for pat, repl in patterns: text = re.sub(pat, repl, text) return text

@client.on(events.NewMessage(chats=SOURCE_CHANNELS)) async def handler(event: events.NewMessage.Event) -> None: text = event.raw_text or '' media = event.message.media src = event.chat.username or str(event.chat.id) logging.info(f"Got message from {src}: has_media={bool(media)}, text_len={len(text)}")

# Sanitize and rewrite links
rewritten = rewrite_links(text)
plain = strip_markdown(rewritten).strip()
has_join = bool(JOIN_MSG_RE.search(text))

if plain and not has_join:
    plain += f"\n\nJoin Our Telegram Group for Fast Update https://t.me/{TARGET_CHANNEL.lstrip('@')}"

if not plain and not media:
    logging.debug("Empty message, skipping.")
    return

# Bold non-URLs
parts = URL_RE.split(plain)
urls = URL_RE.findall(plain)
formatted = ''
for i, part in enumerate(parts):
    formatted += f"**{part}**"
    if i < len(urls):
        formatted += urls[i]

try:
    # Send message
    msg = await client.send_message(TARGET_CHANNEL, formatted, parse_mode='md')
    logging.info(f"Forwarded to {TARGET_CHANNEL}: msg_id={msg.id}")

    # Prepare post link
    post_link = f"https://t.me/{TARGET_CHANNEL.lstrip('@')}/{msg.id}"
    # Randomize quantities
    q1, q2 = random.randint(200, 250), random.randint(10, 15)
    urls = [
        f"https://n1panel.com/api/v2?action=add&service={SERVICE1}&link={post_link}&quantity={q1}&key={API_KEY}",
        f"https://n1panel.com/api/v2?action=add&service={SERVICE2}&link={post_link}&quantity={q2}&key={API_KEY}",
    ]
    for api_url in urls:
        async with http_session.get(api_url) as resp:
            if resp.status == 200:
                logging.info(f"API call success: {api_url}")
            else:
                logging.error(f"API call failed ({resp.status}): {api_url}")
except errors.TelegramError as te:
    logging.error(f"Telegram error: {te}")
except Exception as e:
    logging.exception(f"Unexpected error: {e}")

async def main() -> None: global http_session logging.info("Starting bot...") http_session = aiohttp.ClientSession() try: await client.start() logging.info(f"Listening on {SOURCE_CHANNELS}") await client.run_until_disconnected() finally: await http_session.close() logging.info("HTTP session closed.")

if name == 'main': logging.basicConfig( level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s' ) asyncio.run(main())

