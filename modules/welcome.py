# modules/welcome.py

from pyrogram import Client, filters
from pyrogram.types import Message
from utils.database import db
from utils.helpers import is_admin

@Client.on_message(filters.new_chat_members)
async def welcome_user(client: Client, message: Message):
    chat_id = message.chat.id
    for user in message.new_chat_members:
        welcome_text = await db.get(f"welcome:{chat_id}") or "Welcome to the group, {mention}!"
        formatted = welcome_text.replace("{mention}", user.mention)
        await message.reply(formatted)

@Client.on_message(filters.command(["setwelcome", "!setwelcome"]) & filters.group)
async def set_welcome(client: Client, message: Message):
    if not await is_admin(client, message):
        return

    if len(message.command) < 2:
        return await message.reply("Please provide a welcome message.")

    text = message.text.split(None, 1)[1]
    await db.set(f"welcome:{message.chat.id}", text)
    await message.reply("✅ Welcome message has been updated.")

@Client.on_message(filters.command(["getwelcome", "!getwelcome"]) & filters.group)
async def get_welcome(client: Client, message: Message):
    welcome_text = await db.get(f"welcome:{message.chat.id}")

    if not welcome_text:
        return await message.reply("No welcome message set.")

    await message.reply(f"📩 Current welcome message:\n\n{welcome_text}")

@Client.on_message(filters.command(["resetwelcome", "!resetwelcome"]) & filters.group)
async def reset_welcome(client: Client, message: Message):
    if not await is_admin(client, message):
        return

    await db.delete(f"welcome:{message.chat.id}")
    await message.reply("❌ Welcome message has been reset.")
