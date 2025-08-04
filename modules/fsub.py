# modules/fsub.py

from pyrogram import Client, filters
from pyrogram.types import Message
from bot.utils.database import db

FSUB_COLLECTION = "force_subscribe_channels"


@Client.on_message(filters.command(["fsub", "!fsub"]))
async def set_fsub_channel(client: Client, message: Message):
    if not message.chat or not message.from_user:
        return

    if not message.from_user.id in (await db.get_admins(message.chat.id)):
        return await message.reply("Only admins can manage force subscription.")

    if len(message.command) < 2:
        return await message.reply("Usage: /fsub <channel_username or OFF>")

    arg = message.command[1]
    if arg.lower() == "off":
        await db.delete_item(FSUB_COLLECTION, str(message.chat.id))
        return await message.reply("Force subscribe disabled in this chat.")

    if not arg.startswith("@"):
        return await message.reply("Please provide a valid channel username (with @).")

    await db.set_item(FSUB_COLLECTION, str(message.chat.id), {"channel": arg})
    await message.reply(f"Users must join {arg} before chatting here.")


@Client.on_message(filters.group, group=1)
async def enforce_fsub(client: Client, message: Message):
    if message.from_user is None or message.sender_chat:
        return

    data = await db.get_item(FSUB_COLLECTION, str(message.chat.id))
    if not data:
        return

    channel = data.get("channel")
    if not channel:
        return

    try:
        member = await client.get_chat_member(channel, message.from_user.id)
        if member.status in ("left", "kicked"):
            raise ValueError
    except Exception:
        try:
            await message.delete()
        except Exception:
            pass

        try:
            await message.reply(
                f"You must join {channel} to chat here.",
                reply_to_message_id=message.id
            )
        except Exception:
            pass
