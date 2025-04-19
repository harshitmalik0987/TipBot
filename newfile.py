import os import nest_asyncio import asyncio import re from telethon import TelegramClient, events

=== Allow multiple async frameworks in one loop ===

nest_asyncio.apply()

=== Configuration ===

api_id = int(os.getenv('TELEGRAM_API_ID', '22001404')) api_hash = os.getenv('TELEGRAM_API_HASH', 'b1657c62edd096e74bfd1de603909b02') session_file = os.getenv('SESSION_FILE', 'user_session.session') source_channels = os.getenv( 'SOURCE_CHANNELS', '@speedjobs,@haryana_jobs_in,@pubg_accounts_buy_sell,@haryanaschemes' ).split(',') target_channel = os.getenv('TARGET_CHANNEL', '@Govt_JobNotification')

=== Initialize Telethon client ===

client = TelegramClient(session_file, api_id, api_hash)

=== Helper: Rewrite any telegram links to target channel ===

def rewrite_links(text: str) -> str: pattern = r'https?://(?:telegram.me|t.me)/[A-Za-z0-9_]+' tc = target_channel.lstrip('@') replacement = f'https://t.me/{tc}' return re.sub(pattern, replacement, text)

=== Helper: Convert Markdown to HTML ===

def convert_markdown_to_html(text: str) -> str: text = re.sub(r'**(.?)**', r'<b>\1</b>', text) text = re.sub(r'__(.?)__', r'<u>\1</u>', text) text = re.sub(r'(.*?)', r'<i>\1</i>', text) text = re.sub(r'(.*?)', r'<code>\1</code>', text) text = re.sub(r'', r'<a href="\2">\1</a>', text) return text

=== Handler: on new message in any source channel ===

@client.on(events.NewMessage(chats=source_channels)) async def forward_message(event): text = event.raw_text or '' media = event.message.media

# Rewrite links and convert formatting
text = rewrite_links(text)
html = convert_markdown_to_html(text)

if not media:
    await client.send_message(target_channel, html, parse_mode='HTML')
else:
    data = await client.download_media(media, file=bytes)
    await client.send_file(target_channel, data, caption=html, parse_mode='HTML')

=== Entry point ===

async def main(): await client.start() print(f"Bot running. Listening on {source_channels}") await client.run_until_disconnected()

if name == 'main': asyncio.run(main())
