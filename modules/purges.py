# modules/purges.py

from pyrogram import Client, filters
from pyrogram.types import Message
from utils.helpers import is_admin

@Client.on_message(filters.command(["purge", "!purge"]) & filters.group)
async def purge_messages(client: Client, message: Message):
    if not await is_admin(client, message):
        return

    if not message.reply_to_message:
        return await message.reply("Reply to a message to start purging from.")

    chat_id = message.chat.id
    from_message_id = message.reply_to_message.message_id
    to_message_id = message.message_id

    message_ids = list(range(from_message_id, to_message_id + 1))
    try:
        for i in range(0, len(message_ids), 100):
            await client.delete_messages(chat_id, message_ids[i:i + 100])
        await message.reply("🧹 Messages purged.")
    except Exception as e:
        await message.reply(f"Error: {e}")

@Client.on_message(filters.command(["del", "!del"]) & filters.group)
async def del_single(client: Client, message: Message):
    if not await is_admin(client, message):
        return

    if not message.reply_to_message:
        return await message.reply("Reply to a message to delete it.")
    try:
        await message.reply_to_message.delete()
        await message.delete()
    except Exception as e:
        await message.reply(f"Error: {e}")

@Client.on_message(filters.command(["purgefrom", "!purgefrom"]) & filters.group)
async def purge_from(client: Client, message: Message):
    if not await is_admin(client, message):
        return

    if not message.reply_to_message:
        return await message.reply("Reply to a message to start purging from.")

    chat_id = message.chat.id
    from_message_id = message.reply_to_message.message_id

    # Allow up to 100 messages for safety
    try:
        to_message_id = message.message_id
        message_ids = list(range(from_message_id, to_message_id + 1))
        for i in range(0, len(message_ids), 100):
            await client.delete_messages(chat_id, message_ids[i:i + 100])
        await message.reply("🔻 Messages purged from the reply message.")
    except Exception as e:
        await message.reply(f"Error: {e}")
