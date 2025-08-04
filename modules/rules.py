# bot/modules/rules.py

from pyrogram import Client, filters
from pyrogram.types import Message
from bot.utils.database import rules_db
from bot.utils.helpers import is_admin

@Client.on_message(filters.command(["setrules", "!setrules"]) & filters.group)
async def set_rules(client: Client, message: Message):
    if not await is_admin(client, message):
        return
    if len(message.command) < 2 and not message.reply_to_message:
        return await message.reply("Reply to a message or provide the rules text.")

    rules = message.reply_to_message.text if message.reply_to_message else message.text.split(None, 1)[1]
    await rules_db.set_rules(message.chat.id, rules)
    await message.reply("✅ Rules updated!")

@Client.on_message(filters.command(["rules", "!rules"]) & filters.group)
async def get_rules(client: Client, message: Message):
    rules = await rules_db.get_rules(message.chat.id)
    if rules:
        await message.reply(f"📜 **Group Rules:**\n\n{rules}")
    else:
        await message.reply("No rules have been set yet.")

@Client.on_message(filters.command(["clearrules", "!clearrules"]) & filters.group)
async def clear_rules(client: Client, message: Message):
    if not await is_admin(client, message):
        return
    await rules_db.delete_rules(message.chat.id)
    await message.reply("🗑️ Rules cleared.")
