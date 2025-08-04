# modules/warnings.py

from pyrogram import Client, filters
from pyrogram.types import Message
from utils.database import db
from utils.helpers import is_admin

WARN_LIMIT = 3

def get_warns_key(chat_id: int, user_id: int):
    return f"warns:{chat_id}:{user_id}"

@Client.on_message(filters.command(["warn", "!warn"]) & filters.group)
async def warn_user(client: Client, message: Message):
    if not await is_admin(client, message):
        return

    if not message.reply_to_message:
        return await message.reply("Reply to the user you want to warn.")

    warned_user = message.reply_to_message.from_user
    reason = " ".join(message.command[1:]) or "No reason provided"

    key = get_warns_key(message.chat.id, warned_user.id)
    warns = await db.incr(key)

    await message.reply(
        f"⚠️ {warned_user.mention} has been warned.\n"
        f"Reason: {reason}\n"
        f"Warnings: {warns}/{WARN_LIMIT}"
    )

    if warns >= WARN_LIMIT:
        try:
            await message.chat.ban_member(warned_user.id)
            await db.delete(key)
            await message.reply(f"🚫 {warned_user.mention} has been banned due to reaching warning limit.")
        except Exception as e:
            await message.reply(f"Error banning user: {e}")

@Client.on_message(filters.command(["resetwarns", "!resetwarns"]) & filters.group)
async def reset_warns(client: Client, message: Message):
    if not await is_admin(client, message):
        return

    if not message.reply_to_message:
        return await message.reply("Reply to the user whose warnings you want to reset.")

    warned_user = message.reply_to_message.from_user
    key = get_warns_key(message.chat.id, warned_user.id)
    await db.delete(key)

    await message.reply(f"✅ Warnings for {warned_user.mention} have been reset.")

@Client.on_message(filters.command(["warns", "!warns"]) & filters.group)
async def check_warns(client: Client, message: Message):
    if not message.reply_to_message:
        return await message.reply("Reply to a user to check warnings.")

    warned_user = message.reply_to_message.from_user
    key = get_warns_key(message.chat.id, warned_user.id)
    warns = await db.get(key) or 0

    await message.reply(f"ℹ️ {warned_user.mention} has {warns}/{WARN_LIMIT} warnings.")
