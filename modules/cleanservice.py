# bot/modules/cleanservice.py

from pyrogram import Client, filters
from pyrogram.types import Message, ChatPrivileges
from bot.utils.database import db


@Client.on_message(filters.service)
async def clean_service_messages(client: Client, message: Message):
    chat_id = str(message.chat.id)
    settings = await db.get_clean_service(chat_id)
    
    if settings and settings.get("enabled"):
        try:
            await message.delete()
        except Exception:
            pass


@Client.on_message(filters.command(["cleanservice", "!cleanservice"]))
async def toggle_cleanservice(client: Client, message: Message):
    if not message.from_user or not message.chat:
        return

    if not await client.get_chat_member(message.chat.id, message.from_user.id).can_manage_chat:
        return await message.reply("You must be an admin with manage chat permission to toggle this.")

    chat_id = str(message.chat.id)
    settings = await db.get_clean_service(chat_id)
    enabled = settings.get("enabled", False)

    await db.set_clean_service(chat_id, not enabled)

    status = "enabled" if not enabled else "disabled"
    await message.reply(f"Service message cleaner has been **{status}**.")
