#bot/modules/misban.py

""" Misban

This module helps you to keep your chats safe from corrupted admins who intend to destroy your legacy by removing members from the chat.

Commands:

/misban <on/off>: Turn on/off the Anti-Betrayal mode.

/misbannotify <on/off>: Whether to notify about the betrayal in the chat (disabled for channels by default).

/misbanmode <ban/kick>: Action to be taken against the corrupted admin.

/misbanconfig: Use this command to change default configurations for the misban module.


Note: You must promote admins using the bot's promote command for misban to function properly. """

from pyrogram import Client, filters from pyrogram.types import Message from bot.utils.database import misban_db from bot.utils.helpers import is_admin, is_user_admin

@Client.on_message(filters.command(["misban", "!misban"])) async def toggle_misban(client: Client, message: Message): if not await is_admin(message): return await message.reply("You need to be an admin to use this command.")

if len(message.command) < 2:
    return await message.reply("Usage: /misban <on/off>")

status = message.command[1].lower()
if status not in ["on", "off"]:
    return await message.reply("Invalid option. Use 'on' or 'off'.")

await misban_db.set_misban_status(message.chat.id, status == "on")
await message.reply(f"✅ Misban mode {'enabled' if status == 'on' else 'disabled'}.")

@Client.on_message(filters.command(["misbannotify", "!misbannotify"])) async def toggle_notify(client: Client, message: Message): if not await is_admin(message): return await message.reply("You need to be an admin to use this command.")

if len(message.command) < 2:
    return await message.reply("Usage: /misbannotify <on/off>")

status = message.command[1].lower()
if status not in ["on", "off"]:
    return await message.reply("Invalid option. Use 'on' or 'off'.")

await misban_db.set_notify_status(message.chat.id, status == "on")
await message.reply(f"🔔 Misban notifications {'enabled' if status == 'on' else 'disabled'}.")

@Client.on_message(filters.command(["misbanmode", "!misbanmode"])) async def set_action_mode(client: Client, message: Message): if not await is_admin(message): return await message.reply("You need to be an admin to use this command.")

if len(message.command) < 2:
    return await message.reply("Usage: /misbanmode <ban/kick>")

mode = message.command[1].lower()
if mode not in ["ban", "kick"]:
    return await message.reply("Invalid mode. Choose 'ban' or 'kick'.")

await misban_db.set_action_mode(message.chat.id, mode)
await message.reply(f"🚨 Misban will now {mode} corrupted admins.")

@Client.on_message(filters.command(["misbanconfig", "!misbanconfig"])) async def misban_config(client: Client, message: Message): if not await is_admin(message): return await message.reply("You need to be an admin to use this command.")

config = await misban_db.get_config(message.chat.id)
text = (
    f"🔐 Misban Configuration:\n"
    f"• Status: {'Enabled' if config.get('status') else 'Disabled'}\n"
    f"• Notify: {'Enabled' if config.get('notify') else 'Disabled'}\n"
    f"• Mode: {config.get('action', 'kick').capitalize()}\n\n"
    f"Use /misban, /misbannotify, /misbanmode to modify settings."
)
await message.reply(text)
