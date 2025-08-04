# bot/modules/topics.py

from pyrogram import Client, filters
from pyrogram.types import Message
from bot.utils.database import db
from bot.utils.helpers import is_admin


@Client.on_message(filters.command(["topic", "!topic"]))
async def set_topic(client: Client, message: Message):
    if not message.chat or not message.from_user:
        return

    if not await is_admin(client, message):
        return await message.reply("You need to be an admin to use this command.")

    if not message.reply_to_message:
        return await message.reply("Reply to a message to set its thread as the default topic.")

    chat_id = str(message.chat.id)
    topic_id = message.reply_to_message.message_thread_id

    await db.set_topic(chat_id, topic_id)
    await message.reply(f"Default topic set to `{topic_id}`.")


@Client.on_message(filters.command(["cleartopic", "!cleartopic"]))
async def clear_topic(client: Client, message: Message):
    if not message.chat or not message.from_user:
        return

    if not await is_admin(client, message):
        return await message.reply("You need to be an admin to use this command.")

    chat_id = str(message.chat.id)
    await db.clear_topic(chat_id)
    await message.reply("Default topic has been cleared.")


async def get_default_topic(chat_id: int) -> int | None:
    topic = await db.get_topic(str(chat_id))
    return topic.get("topic_id") if topic else None
