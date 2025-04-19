import os
import nest_asyncio
import asyncio
from telethon import TelegramClient, events
from telegram.ext import Application, CommandHandler
from telegram import Bot

# === Apply nest_asyncio to allow multiple frameworks in the same event loop ===
nest_asyncio.apply()

# === Telethon Auth (using environment variables with defaults for testing) ===
api_id = int(os.getenv('TELEGRAM_API_ID', '22001404'))
api_hash = os.getenv('TELEGRAM_API_HASH', 'b1657c62edd096e74bfd1de603909b02')
source_channels = ['@speedjobs', '@haryana_jobs_in', '@pubg_accounts_buy_sell']
target_channel = '@Govt_JobNotification'

# === Create Telethon client ===
client = TelegramClient('user_session', api_id, api_hash)

# === Setup python-telegram-bot (using environment variables with defaults) ===
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '7919514003:AAGMyAgcNc3dDkLo794OCSXkhfIiqQ2Ai9Y')
bot = Bot(token=BOT_TOKEN)

# === Message Forwarding Handler ===
@client.on(events.NewMessage(chats=source_channels))
async def forward_message(event):
    try:
        message = event.message
        text = message.text or ""  # Default to empty string if no text
        media = message.media

        # Resolve target channel ID
        target = await bot.get_chat(target_channel)
        formatted_text = "<b>📨 Alert! New Notification</b>\n\n" + text if text else "<b>📨 Alert! New Notification</b>\n\n"

        # Send text or empty alert if no media
        if text or not media:
            await bot.send_message(chat_id=target.id, text=formatted_text, parse_mode='HTML')

        # Handle media if present
        if media:
            file = await client.download_media(message.media, file=bytes)
            if hasattr(media, 'photo'):
                await bot.send_photo(chat_id=target.id, photo=file, caption=formatted_text, parse_mode='HTML')
            elif hasattr(media, 'document'):
                await bot.send_document(chat_id=target.id, document=file, caption=formatted_text, parse_mode='HTML')
            elif hasattr(media, 'video'):
                await bot.send_video(chat_id=target.id, video=file, caption=formatted_text, parse_mode='HTML')
            else:
                print(f"Unsupported media type: {type(media)}")

        print(f"Message sent to {target_channel} with alert formatting.")
    except Exception as e:
        print(f"Error sending message: {e}")

# === Command Handler ===
async def start(update, context):
    await update.message.reply_text("Hello, I'm your bot!")

# === Build and Configure the Application ===
application = Application.builder().token(BOT_TOKEN).build()
application.add_handler(CommandHandler("start", start))

# === Unified Async Main Loop ===
async def main():
    try:
        # Start Telethon client
        await client.start()
        print("Telethon client started.")

        # Initialize and start the Application (handles polling internally)
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

# === Run the Application ===
if __name__ == '__main__':
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        print("Program terminated by user.")
    except Exception as e:
        print(f"Unexpected error: {e}")
