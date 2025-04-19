import os import nest_asyncio import asyncio import re from telethon import TelegramClient, events from telegram.ext import Application, CommandHandler from telegram import Bot

=== Apply nest_asyncio to allow multiple frameworks in the same event loop ===

nest_asyncio.apply()

=== Telethon Auth (using environment variables with defaults for testing) ===

api_id = int(os.getenv('TELEGRAM_API_ID', '22001404')) api_hash = os.getenv('TELEGRAM_API_HASH', 'b1657c62edd096e74bfd1de603909b02') source_channels = ['@speedjobs', '@haryana_jobs_in', '@pubg_accounts_buy_sell', '@haryanaschemes'] target_channel = '@Govt_JobNotification'

=== Create Telethon client ===

client = TelegramClient('user_session', api_id, api_hash)

=== Setup python-telegram-bot (using environment variables with defaults) ===

BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '7919514003:AAGMyAgcNc3dDkLo794OCSXkhfIiqQ2Ai9Y') bot = Bot(token=BOT_TOKEN)

=== Link Rewriting ===

def rewrite_links(text): """ Replace any telegram.me or t.me links in the text with the target channel link. """ pattern = r'https?://(?:telegram.me|t.me)/[A-Za-z0-9_]+' replacement = f'https://t.me/{target_channel.lstrip("@")}'' return re.sub(pattern, replacement, text)

=== Markdown to HTML conversion ===

def convert_markdown_to_html(text): # Bold text = re.sub(r'**(.?)**', r'<b>\1</b>', text) # Underline text = re.sub(r'__(.?)__', r'<u>\1</u>', text) # Italic text = re.sub(r'(.*?)', r'<i>\1</i>', text) # Inline code text = re.sub(r'(.*?)', r'<code>\1</code>', text) # Links text = re.sub(r'', r'<a href="\2">\1</a>', text) return text

=== Message Forwarding Handler ===

@client.on(events.NewMessage(chats=source_channels)) async def forward_message(event): try: message = event.message text = message.text or "" media = message.media

# Rewrite any source links
    text = rewrite_links(text)

    # Resolve target channel ID
    target = await bot.get_chat(target_channel)

    # Convert Markdown to HTML
    formatted_body = convert_markdown_to_html(text)
    formatted_text = formatted_body if text else ""

    # Send text or empty alert if no media
    if text or not media:
        await bot.send_message(
            chat_id=target.id,
            text=formatted_text,
            parse_mode='HTML'
        )

    # Handle media if present
    if media:
        file = await client.download_media(media, file=bytes)
        if hasattr(media, 'photo'):
            await bot.send_photo(
                chat_id=target.id,
                photo=file,
                caption=formatted_text,
                parse_mode='HTML'
            )
        elif hasattr(media, 'document'):
            await bot.send_document(
                chat_id=target.id,
                document=file,
                caption=formatted_text,
                parse_mode='HTML'
            )
        elif hasattr(media, 'video'):
            await bot.send_video(
                chat_id=target.id,
                video=file,
                caption=formatted_text,
                parse_mode='HTML'
            )
        else:
            print(f"Unsupported media type: {type(media)}")

    print(f"Message sent to {target_channel}.")
except Exception as e:
    print(f"Error sending message: {e}")

=== Command Handler ===

async def start(update, context): await update.message.reply_text("Hello, I'm your bot!")

=== Build and Configure the Application ===

application = Application.builder().token(BOT_TOKEN).build() application.add_handler(CommandHandler("start", start))

=== Unified Async Main Loop ===

async def main(): try: # Start Telethon client await client.start() print("Telethon client started.")

# Initialize and start the Application
    await application.initialize()
    await application.start()
    print("Python-telegram-bot application started.")

    # Keep the script running with Telethon
    await client.run_until_disconnected()
except Exception as e:
    print(f"Error in main loop: {e}")
finally:
    # Ensure clean shutdown
    await application.stop()
    print("Application stopped.")

=== Run the Application ===

if name == 'main': try: loop = asyncio.get_event_loop() loop.run_until_complete(main()) except KeyboardInterrupt: print("Program terminated by user.") except Exception as e: print(f"Unexpected error: {e}")

