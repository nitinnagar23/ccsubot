# modules/repeats.py

from pyrogram import Client, filters
from pyrogram.types import Message
from utils.database import db
from utils.helpers import is_admin


@Client.on_message(filters.command(["cleanrepeat", "!cleanrepeat"]))
async def toggle_clean_repeat(client: Client, message: Message):
    if not message.chat or not message.from_user:
        return

    if not await is_admin(client, message):
        return await message.reply("You need to be an admin to toggle this setting.")

    chat_id = str(message.chat.id)
    args = message.command

    if len(args) < 2:
        current = await db.get_cleanrepeat(chat_id)
        return await message.reply(f"Current Clean Repeat setting is: `{current}`")

    value = args[1].lower()
    if value in ["yes", "on"]:
        await db.set_cleanrepeat(chat_id, True)
        await message.reply("Clean Repeat is now enabled.")
    elif value in ["no", "off"]:
        await db.set_cleanrepeat(chat_id, False)
        await message.reply("Clean Repeat is now disabled.")
    else:
        await message.reply("Invalid option. Use `yes`, `no`, `on`, or `off`.")


last_messages = {}  # In-memory store to avoid repeated texts (can move to DB for persistence)


@Client.on_message(filters.group & ~filters.service)
async def check_repeats(client: Client, message: Message):
    chat_id = str(message.chat.id)
    user_id = message.from_user.id if message.from_user else None
    clean_repeat = await db.get_cleanrepeat(chat_id)

    if not clean_repeat:
        return

    key = f"{chat_id}:{user_id}"
    last_text = last_messages.get(key)

    if message.text and last_text == message.text:
        try:
            await message.delete()
        except Exception:
            pass  # Handle if bot doesn't have permission
    else:
        last_messages[key] = message.text
