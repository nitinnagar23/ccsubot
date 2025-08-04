# bot/modules/reports.py

from pyrogram import Client, filters
from pyrogram.types import Message
from bot.utils.helpers import get_admins

REPORT_TRIGGERS = ["@admin", "#report", "!report", "/report"]

@Client.on_message(filters.group & filters.text)
async def handle_report(client: Client, message: Message):
    if not any(trigger in message.text.lower() for trigger in REPORT_TRIGGERS):
        return

    admins = await get_admins(client, message.chat.id)
    if not admins:
        return

    mentions = " ".join([f"[{admin.first_name}](tg://user?id={admin.id})" for admin in admins if not admin.bot])
    await message.reply(
        f"🚨 User [{message.from_user.first_name}](tg://user?id={message.from_user.id}) has reported a message!\n\n{mentions}",
        quote=True,
        disable_web_page_preview=True,
    )

@Client.on_message(filters.command(["report", "!report"]) & filters.reply & filters.group)
async def report_reply(client: Client, message: Message):
    reply = message.reply_to_message
    admins = await get_admins(client, message.chat.id)

    if not admins:
        return

    mentions = " ".join([f"[{admin.first_name}](tg://user?id={admin.id})" for admin in admins if not admin.bot])
    await message.reply(
        f"🚨 Reported message from [{reply.from_user.first_name}](tg://user?id={reply.from_user.id}).\n\n{mentions}",
        quote=True,
        disable_web_page_preview=True,
    )
