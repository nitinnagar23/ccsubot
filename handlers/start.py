# handlers/start.py

from pyrogram import Client, filters
from pyrogram.types import Message
from config import OWNER_ID

@Client.on_message(filters.command("start") & filters.private)
async def start_private(client: Client, message: Message):
    await message.reply_text(
        f"👋 Hello {message.from_user.mention},\n"
        "I'm a modular Telegram bot.\n\n"
        "Use /help to explore my features."
    )

@Client.on_message(filters.command("start") & filters.group)
async def start_group(client: Client, message: Message):
    if message.from_user.id in OWNER_ID:
        await message.reply_text("👋 Bot is running correctly in this group.")
