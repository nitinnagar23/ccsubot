from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from bot_core.registry import COMMAND_REGISTRY
from database.db import db
from utils.decorators import admin_only
from utils.context import resolve_target_chat_id

chat_settings_collection = db["chat_settings"]

# --- Helper Function ---
def get_disableable_commands():
    """Returns a list of all commands that can be disabled (category: 'user')."""
    return [cmd for cmd, info in COMMAND_REGISTRY.items() if info.get("category") == "user"]

# --- Admin Commands ---
@admin_only
async def disable_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Disables one or more commands in the chat."""
    target_chat_id = await resolve_target_chat_id(update, context)
    args = [arg.lower() for arg in context.args]
    if not args:
        await update.message.reply_text("You need to specify which command(s) to disable.")
        return

    disableable_list = get_disableable_commands()
    cmds_to_disable = []
    
    if "all" in args:
        cmds_to_disable = disableable_list
    else:
        for cmd in args:
            if cmd in disableable_list:
                cmds_to_disable.append(cmd)
            else:
                await update.message.reply_text(f"`{cmd}` is not a disableable command. Use `/disableable` to see the list.", parse_mode=ParseMode.MARKDOWN_V2)
                return

    if not cmds_to_disable:
        await update.message.reply_text("No valid commands to disable were provided.")
        return
        
    chat_settings_collection.update_one(
        {"_id": target_chat_id},
        {"$addToSet": {"disabled_commands": {"$each": cmds_to_disable}}},
        upsert=True
    )
    await update.message.reply_text(f"✅ Disabled commands: `{'`, `'.join(cmds_to_disable)}`.", parse_mode=ParseMode.MARKDOWN_V2)

@admin_only
async def enable_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Enables one or more commands in the chat."""
    target_chat_id = await resolve_target_chat_id(update, context)
    args = [arg.lower() for arg in context.args]
    if not args:
        await update.message.reply_text("You need to specify which command(s) to enable.")
        return
        
    chat_settings_collection.update_one(
        {"_id": target_chat_id},
        {"$pullAll": {"disabled_commands": args}},
    )
    # Also remove 'all' if it exists, to allow re-enabling individual commands
    if "all" in args:
        chat_settings_collection.update_one(
            {"_id": target_chat_id},
            {"$set": {"disabled_commands": []}}
        )

    await update.message.reply_text(f"✅ Enabled commands: `{'`, `'.join(args)}`.", parse_mode=ParseMode.MARKDOWN_V2)

@admin_only
async def list_disableable(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lists all commands that can be disabled."""
    disableable_list = get_disableable_commands()
    msg = "The following user-facing commands can be disabled:\n\n"
    msg += " ".join(f"`{cmd}`" for cmd in sorted(disableable_list))
    await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN_V2)

@admin_only
async def list_disabled(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lists all currently disabled commands in the chat."""
    target_chat_id = await resolve_target_chat_id(update, context)
    settings = chat_settings_collection.find_one({"_id": target_chat_id}) or {}
    disabled_cmds = settings.get("disabled_commands", [])

    if not disabled_cmds:
        await update.message.reply_text("No commands are currently disabled in this chat.")
        return
        
    msg = "The following commands are currently disabled for non-admins:\n\n"
    msg += " ".join(f"`{cmd}`" for cmd in sorted(disabled_cmds))
    await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN_V2)

@admin_only
async def set_disabled_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set whether to delete disabled commands when used."""
    target_chat_id = await resolve_target_chat_id(update, context)
    args = context.args
    if not args or args[0].lower() not in ["yes", "no", "on", "off"]:
        await update.message.reply_text("Usage: `/disabledel <on/off>`")
        return

    setting = args[0].lower() in ["yes", "on"]
    chat_settings_collection.update_one(
        {"_id": target_chat_id}, {"$set": {"disable_delete": setting}}, upsert=True
    )
    status = "will now be deleted" if setting else "will be ignored"
    await update.message.reply_text(f"Used disabled commands {status}.")

@admin_only
async def set_disable_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set whether admins are also affected by disabled commands."""
    target_chat_id = await resolve_target_chat_id(update, context)
    args = context.args
    if not args or args[0].lower() not in ["yes", "no", "on", "off"]:
        await update.message.reply_text("Usage: `/disableadmin <on/off>`")
        return

    setting = args[0].lower() in ["yes", "on"]
    chat_settings_collection.update_one(
        {"_id": target_chat_id}, {"$set": {"disable_admin": setting}}, upsert=True
    )
    status = "now affects admins" if setting else "no longer affects admins"
    await update.message.reply_text(f"Disabled commands list {status}.")
