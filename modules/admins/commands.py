from telegram import Update, User, ChatMember
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from database.db import db
from utils.decorators import admin_only
from utils.parsers import extract_user
from utils.context import resolve_target_chat_id

chat_settings_collection = db["chat_settings"]

# --- Helper function to get chat settings ---
def get_chat_settings(chat_id: int):
    settings = chat_settings_collection.find_one({"_id": chat_id})
    if not settings:
        return {"allow_anon_admin": False, "send_admin_error": True, "promoted_users": []}
    return settings

# --- Command Handlers ---

@admin_only
async def promote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Promote a user to a 'bot admin'."""
    target_chat_id = await resolve_target_chat_id(update, context)
    target_chat = await context.bot.get_chat(target_chat_id)
    
    target_user_id, target_user_name = await extract_user(update, context)
    if not target_user_id:
        await update.message.reply_text("I can't find that user.")
        return

    # Check if user is already a Telegram admin
    chat_admins = await target_chat.get_administrators()
    if target_user_id in {admin.user.id for admin in chat_admins}:
        await update.message.reply_text("This user is already a full chat admin in the target chat.")
        return

    # Check if user is already a bot admin
    settings = get_chat_settings(target_chat_id)
    if target_user_id in settings.get("promoted_users", []):
        await update.message.reply_text(f"User {target_user_name} is already a bot admin.")
        return

    # Promote the user
    chat_settings_collection.update_one(
        {"_id": target_chat_id},
        {"$addToSet": {"promoted_users": target_user_id}},
        upsert=True
    )
    await update.message.reply_text(f"✅ Successfully promoted {target_user_name} (`{target_user_id}`) to bot admin in **{target_chat.title}**!", parse_mode=ParseMode.HTML)

@admin_only
async def demote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Demote a user from being a 'bot admin'."""
    target_chat_id = await resolve_target_chat_id(update, context)
    target_chat = await context.bot.get_chat(target_chat_id)
    
    target_user_id, target_user_name = await extract_user(update, context)
    if not target_user_id:
        await update.message.reply_text("I can't find that user.")
        return

    # Cannot demote full chat admins via the bot
    chat_admins = await target_chat.get_administrators()
    if target_user_id in {admin.user.id for admin in chat_admins}:
        await update.message.reply_text("This user is a full chat admin. You must demote them through Telegram's own settings.")
        return
        
    # Check if user is a bot admin
    settings = get_chat_settings(target_chat_id)
    if target_user_id not in settings.get("promoted_users", []):
        await update.message.reply_text(f"{target_user_name} is not a bot admin.")
        return

    # Demote the user
    chat_settings_collection.update_one(
        {"_id": target_chat_id},
        {"$pull": {"promoted_users": target_user_id}}
    )
    await update.message.reply_text(f"✅ Successfully demoted {target_user_name} (`{target_user_id}`) in **{target_chat.title}**.", parse_mode=ParseMode.HTML)

@admin_only
async def admin_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lists all admins in the chat."""
    target_chat_id = await resolve_target_chat_id(update, context)
    target_chat = await context.bot.get_chat(target_chat_id)
    
    try:
        chat_admins = await target_chat.get_administrators()
    except Exception as e:
        await update.message.reply_text(f"An error occurred: {e}\nI might not have permission to see admins in the target chat.")
        return

    creator = None
    admins = []
    for admin in chat_admins:
        if admin.status == ChatMember.CREATOR: creator = admin.user
        else: admins.append(admin.user)
            
    settings = get_chat_settings(target_chat_id)
    bot_admins_ids = settings.get("promoted_users", [])
    
    msg = f"<b>Admins in {target_chat.title}</b>\n\n"
    if creator:
        msg += f"👑 **Creator**\n- {creator.mention_html()} (`{creator.id}`)\n\n"
    
    if admins:
        msg += "👮‍♂️ **Admins**\n"
        msg += "".join([f"- {admin.mention_html()} (`{admin.id}`)\n" for admin in admins]) + "\n"

    if bot_admins_ids:
        bot_admin_users = []
        for user_id in bot_admins_ids:
            if user_id not in {u.id for u in admins} and (not creator or user_id != creator.id):
                try: bot_admin_users.append(await context.bot.get_chat(user_id))
                except Exception: pass
        if bot_admin_users:
             msg += "🤖 **Bot Admins**\n"
             msg += "".join([f"- {user.mention_html()} (`{user.id}`)\n" for user in bot_admin_users])
    
    await update.message.reply_text(msg, parse_mode=ParseMode.HTML)

@admin_only
async def admin_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles /anonadmin and /adminerror."""
    command = update.message.text.split()[0].lower().lstrip('/!')
    setting_key = "allow_anon_admin" if command == "anonadmin" else "send_admin_error"
    
    target_chat_id = await resolve_target_chat_id(update, context)
    args = context.args
    if not args or args[0].lower() not in ["on", "off", "yes", "no"]:
        await update.message.reply_text(f"Usage: `/{command} <on/off>`")
        return
        
    enabled = args[0].lower() in ["on", "yes"]
    chat_settings_collection.update_one(
        {"_id": target_chat_id},
        {"$set": {setting_key: enabled}},
        upsert=True
    )
    status_msg = "enabled" if enabled else "disabled"
    await update.message.reply_text(f"✅ Setting `{command}` has been **{status_msg}**.", parse_mode=ParseMode.MARKDOWN_V2)

