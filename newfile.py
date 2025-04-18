import nest_asyncio
import asyncio
from telethon import TelegramClient, events
from telegram.ext import Application, CommandHandler
from telegram import Bot

# === Apply nest_asyncio to allow multiple frameworks in the same event loop ===
nest_asyncio.apply()

# === Telethon Auth ===
api_id = 22001404
api_hash = 'b1657c62edd096e74bfd1de603909b02'
source_channels = ['@speedjobs', '@haryana_jobs_in', '@pubg_accounts_buy_sell']  # Added new channel
target_channel = '@Govt_JobNotification'  # Target channel

# === Create Telethon client ===
client = TelegramClient('user_session', api_id, api_hash)

# === Setup python-telegram-bot ===
BOT_TOKEN = '7919514003:AAGMyAgcNc3dDkLo794OCSXkhfIiqQ2Ai9Y'

# === Initialize Bot instance for sending messages ===
bot = Bot(token=BOT_TOKEN)

@client.on(events.NewMessage(chats=source_channels))
async def forward_message(event):
    try:
        # Extract message content
        message = event.message
        text = message.text or ""  # Get text, default to empty string if None
        media = message.media  # Get media if present

        # Get target channel ID (resolve username to ID)
        target = await bot.get_chat(target_channel)

        # Format the message with the alert header
        formatted_text = "<b>📨 Alert! New Notification</b>\n\n" + text if text else "<b>📨 Alert! New Notification</b>\n\n"

        # Send text message if present
        if text or not media:  # Send text or empty alert if no media
            await bot.send_message(chat_id=target.id, text=formatted_text, parse_mode='HTML')

        # Send media if present
        if media:
            # Handle different types of media (photo, video, document, etc.)
            if hasattr(media, 'photo'):
                # Download the photo to send it
                file = await client.download_media(message.media, file=bytes)
                await bot.send_photo(chat_id=target.id, photo=file, caption=formatted_text, parse_mode='HTML')
            elif hasattr(media, 'document'):
                # Download the document
                file = await client.download_media(message.media, file=bytes)
                await bot.send_document(chat_id=target.id, document=file, caption=formatted_text, parse_mode='HTML')
            elif hasattr(media, 'video'):
                # Download the video
                file = await client.download_media(message.media, file=bytes)
                await bot.send_video(chat_id=target.id, video=file, caption=formatted_text, parse_mode='HTML')
            else:
                print(f"Unsupported media type: {type(media)}")

        print(f"Message sent to {target_channel} with alert formatting.")
    except Exception as e:
        print(f"Error sending message: {e}")

async def start(update, context):
    await update.message.reply_text("Hello, I'm your bot!")

# === Build the application ===
application = Application.builder().token(BOT_TOKEN).build()
application.add_handler(CommandHandler("start", start))

# === Unified run loop ===
async def main():
    try:
        # Start Telethon client
        await client.start()
        print("Telethon client started.")

        # Initialize and start PTB application
        await application.initialize()
        await application.start()
        await application.updater.start_polling()
        print("Python-telegram-bot started.")

        # Run Telethon until disconnected
        await client.run_until_disconnected()

    except Exception as e:
        print(f"Error in main loop: {e}")
    finally:
        # Ensure proper shutdown
        await application.stop()
        await application.updater.stop()
        print("Application stopped.")

# === Run the unified loop ===
if __name__ == '__main__':
    try:
        # Use the existing event loop
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        print("Program terminated by user.")
    except Exception as e:
        print(f"Unexpected error: {e}")
