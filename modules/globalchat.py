# modules/globalchat.py

from pyrogram import Client, filters
from pyrogram.types import Message
from utils.database import db
from utils.helpers import is_admin
import asyncio

# Global chat collection name
GC_COLLECTION = "global_chats"


@Client.on_message(filters.command(["addglobal", "!addglobal"]))
async def add_global_chat(client: Client, message: Message):
    if not await is_admin(client, message):
        return await message.reply("Only admins can manage global chat.")

    chat_id = str(message.chat.id)
    added = await db.add_to_list(GC_COLLECTION, chat_id)

    if added:
        await message.reply("This chat has been added to the global chat network.")
    else:
        await message.reply("This chat is already part of the global chat network.")


@Client.on_message(filters.command(["removeglobal", "!removeglobal"]))
async def remove_global_chat(client: Client, message: Message):
    if not await is_admin(client, message):
        return await message.reply("Only admins can manage global chat.")

    chat_id = str(message.chat.id)
    removed = await db.remove_from_list(GC_COLLECTION, chat_id)

    if removed:
        await message.reply("This chat has been removed from the global chat network.")
    else:
        await message.reply("This chat was not part of the global chat network.")


@Client.on_message(filters.group & ~filters.command)
async def global_chat_handler(client: Client, message: Message):
    if not message.text or message.service:
        return

    chat_id = str(message.chat.id)
    chats = await db.get_list(GC_COLLECTION)

    if chat_id not in chats:
        return

    for target_chat in chats:
        if target_chat != chat_id:
            try:
                await client.send_message(
                    int(target_chat),
                    f"<b>{message.from_user.first_name}</b> from <code>{chat_id}</code>:\n\n{message.text}"
                )
                await asyncio.sleep(0.2)  # Small delay to avoid flood
            except Exception:
                pass
