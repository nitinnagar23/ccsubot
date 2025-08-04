# modules/notes.py

from pyrogram import Client, filters
from pyrogram.types import Message
from utils.database import notesdb
from utils.helpers import is_admin

@Client.on_message(filters.command(["savenote", "!savenote"]) & filters.group)
async def save_note(client: Client, message: Message):
    if not await is_admin(client, message):
        return

    if len(message.command) < 3:
        return await message.reply("Usage: /savenote note_name note_content")

    note_name = message.command[1].lower()
    note_content = " ".join(message.command[2:])
    chat_id = str(message.chat.id)

    await notes_collection.update_one(
        {"chat_id": chat_id, "name": note_name},
        {"$set": {"content": note_content}},
        upsert=True
    )

    await message.reply(f"✅ Note '{note_name}' saved.")

@Client.on_message(filters.command(["getnote", "!getnote"]) & filters.group)
async def get_note(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply("Usage: /getnote note_name")

    note_name = message.command[1].lower()
    chat_id = str(message.chat.id)

    note = await notes_collection.find_one({"chat_id": chat_id, "name": note_name})
    if note:
        await message.reply(note["content"])
    else:
        await message.reply("❌ Note not found.")

@Client.on_message(filters.command(["delnote", "!delnote"]) & filters.group)
async def delete_note(client: Client, message: Message):
    if not await is_admin(client, message):
        return

    if len(message.command) < 2:
        return await message.reply("Usage: /delnote note_name")

    note_name = message.command[1].lower()
    chat_id = str(message.chat.id)

    result = await notes_collection.delete_one({"chat_id": chat_id, "name": note_name})
    if result.deleted_count:
        await message.reply(f"🗑️ Note '{note_name}' deleted.")
    else:
        await message.reply("❌ Note not found.")

@Client.on_message(filters.text & filters.group)
async def trigger_note(client: Client, message: Message):
    text = message.text.strip().lower()
    chat_id = str(message.chat.id)

    note = await notes_collection.find_one({"chat_id": chat_id, "name": text})
    if note:
        await message.reply(note["content"])
