# modules/filters.py

from pyrogram import Client, filters
from pyrogram.types import Message
from utils.database import filters_collection
from utils.helpers import is_admin

@Client.on_message(filters.command(["addfilter", "!addfilter"]) & filters.group)
async def add_filter(client: Client, message: Message):
    if not await is_admin(client, message):
        return

    if len(message.command) < 3:
        return await message.reply("Usage: /addfilter keyword reply_text")

    keyword = message.command[1].lower()
    reply_text = " ".join(message.command[2:])
    chat_id = str(message.chat.id)

    await filters_collection.update_one(
        {"chat_id": chat_id, "keyword": keyword},
        {"$set": {"reply": reply_text}},
        upsert=True,
    )

    await message.reply(f"✅ Filter for '{keyword}' added.")

@Client.on_message(filters.command(["delfilter", "!delfilter"]) & filters.group)
async def delete_filter(client: Client, message: Message):
    if not await is_admin(client, message):
        return

    if len(message.command) < 2:
        return await message.reply("Usage: /delfilter keyword")

    keyword = message.command[1].lower()
    chat_id = str(message.chat.id)

    result = await filters_collection.delete_one({"chat_id": chat_id, "keyword": keyword})
    if result.deleted_count:
        await message.reply(f"🗑️ Filter '{keyword}' deleted.")
    else:
        await message.reply("❌ No such filter.")

@Client.on_message(filters.text & filters.group)
async def reply_filter(client: Client, message: Message):
    keyword = message.text.lower().strip()
    chat_id = str(message.chat.id)

    result = await filters_collection.find_one({"chat_id": chat_id, "keyword": keyword})
    if result:
        await message.reply(result["reply"])
