# bot/modules/admin.py

from pyrogram import Client, filters
from pyrogram.types import Message
from bot.utils.helpers import is_admin

@Client.on_message(filters.command(["promote", "!promote"]) & filters.group)
async def promote_user(client: Client, message: Message):
    if not await is_admin(client, message):
        return

    if not message.reply_to_message:
        return await message.reply_text("Reply to a user to promote.")
    
    try:
        await client.promote_chat_member(
            chat_id=message.chat.id,
            user_id=message.reply_to_message.from_user.id,
            can_change_info=True,
            can_post_messages=True,
            can_edit_messages=True,
            can_delete_messages=True,
            can_invite_users=True,
            can_restrict_members=True,
            can_pin_messages=True,
            can_promote_members=False
        )
        await message.reply_text("✅ User promoted.")
    except Exception as e:
        await message.reply_text(f"Failed to promote: {e}")

@Client.on_message(filters.command(["demote", "!demote"]) & filters.group)
async def demote_user(client: Client, message: Message):
    if not await is_admin(client, message):
        return

    if not message.reply_to_message:
        return await message.reply_text("Reply to a user to demote.")

    try:
        await client.promote_chat_member(
            chat_id=message.chat.id,
            user_id=message.reply_to_message.from_user.id,
            can_change_info=False,
            can_post_messages=False,
            can_edit_messages=False,
            can_delete_messages=False,
            can_invite_users=False,
            can_restrict_members=False,
            can_pin_messages=False,
            can_promote_members=False
        )
        await message.reply_text("✅ User demoted.")
    except Exception as e:
        await message.reply_text(f"Failed to demote: {e}")
