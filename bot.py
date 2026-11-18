import os
import asyncio
import tempfile
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)
import yt_dlp

TOKEN = os.environ.get("BOT_TOKEN")

def main_menu():
    keyboard = [
        [InlineKeyboardButton("🎵 Music Search", callback_data="music")],
        [InlineKeyboardButton("🎬 Video Downloader", callback_data="video")],
        [InlineKeyboardButton("🎧 Audio Downloader", callback_data="audio")],
        [InlineKeyboardButton("📸 Photo Downloader", callback_data="photo")],
        [InlineKeyboardButton("🔗 Link Downloader", callback_data="link")],
        [InlineKeyboardButton("ℹ️ Help", callback_data="help")]
    ]
    return InlineKeyboardMarkup(keyboard)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚀 WELCOME TO SWIFTSAVER!\n\n"
        "Your fast Telegram media assistant.\n\n"
        "Choose an option below:",
        reply_markup=main_menu()
    )


async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    messages = {
        "music": "🎵 Send a song title and artist.",
        "video": "🎬 Send a supported video URL.",
        "audio": "🎧 Send a video URL to extract audio.",
        "photo": "📸 Send a supported photo URL.",
        "link": "🔗 Paste your media URL.",
        "help": "ℹ️ Choose an option and follow the instructions."
    }

    context.user_data["mode"] = query.data
    await query.message.reply_text(messages[query.data])


def download_media(url, folder, audio=False):
    options = {
        "outtmpl": os.path.join(folder, "%(title).80s.%(ext)s"),
        "format": "bestaudio/best" if audio else "bestvideo*+bestaudio/best",
        "noplaylist": True,
        "quiet": True,
        "merge_output_format": "mp4"
    }

    if audio:
        options["postprocessors"] = [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3"
        }]

    with yt_dlp.YoutubeDL(options) as ydl:
        ydl.download([url])

    files = os.listdir(folder)
    return os.path.join(folder, files[0]) if files else None


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    mode = context.user_data.get("mode", "link")

    if mode == "music":
        await update.message.reply_text(
            "Music search needs a licensed music catalog API. "
            "This feature is not connected yet."
        )
        return

    if not text.startswith(("https://", "http://")):
        await update.message.reply_text("❌ Please send a valid URL.")
        return

    status = await update.message.reply_text("⏳ Processing your link...")

    try:
        with tempfile.TemporaryDirectory() as folder:
            path = await asyncio.to_thread(
                download_media, text, folder, mode == "audio"
            )

            if not path:
                raise Exception("No media found")

            await status.edit_text("📤 Sending your file...")

            with open(path, "rb") as file:
                if mode == "audio":
                    await update.message.reply_audio(audio=file)
                else:
                    await update.message.reply_document(document=file)

            await status.delete()

    except Exception:
        await status.edit_text(
            "❌ Download failed. The link may be unsupported, "
            "private or unavailable."
        )


def main():
    if not TOKEN:
        raise ValueError("BOT_TOKEN environment variable is missing")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

    print("SwiftSaver is running!")
    app.run_polling()


if __name__ == "__main__":
    main()
