import time
import math
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from telegram.error import BadRequest

from database.db import db
from utils.decorators import admin_only, check_disabled
from utils.permissions import is_user_admin
from utils.parsers import extract_user
from utils.context import resolve_target_chat_id

xp_collection = db["xp_data"]
chat_settings_collection = db["chat_settings"]

# --- XP & Leveling Constants and Helpers ---
LEVEL_CONSTANT = 150 # Adjust this to make leveling faster (lower) or slower (higher)

def xp_to_level(xp: int) -> tuple[int, int, int]:
    """Calculates level, xp in current level, and xp for next level."""
    if xp < 0: xp = 0
    level = int(math.sqrt(xp / LEVEL_CONSTANT))
    xp_for_current_level = LEVEL_CONSTANT * (level ** 2)
    xp_for_next_level = LEVEL_CONSTANT * ((level + 1) ** 2)
    xp_in_level = xp - xp_for_current_level
    xp_needed_for_next = xp_for_next_level - xp_for_current_level
    return level, xp_in_level, xp_needed_for_next

# --- Core Message Handler for Granting XP ---
async def grant_xp_on_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Listens to messages and grants XP."""
    user = update.effective_user
    chat = update.effective_chat
    if not user or not chat or user.is_bot: return

    settings = chat_settings_collection.find_one({"_id": chat.id}) or {}
    if not settings.get("xp_enabled", False): return

    cooldown = settings.get("xp_cooldown_seconds", 60)
    cooldown_dict = context.chat_data.setdefault("xp_cooldowns", {})
    last_xp_time = cooldown_dict.get(user.id, 0)
    
    if time.time() - last_xp_time < cooldown: return

    xp_gain = settings.get("xp_per_message", 10)
    user_xp_doc = xp_collection.find_one({"chat_id": chat.id, "user_id": user.id})
    old_xp = user_xp_doc.get("xp", 0) if user_xp_doc else 0
    new_xp = old_xp + xp_gain
    
    old_level, _, _ = xp_to_level(old_xp)
    new_level, _, _ = xp_to_level(new_xp)
    
    xp_collection.update_one({"chat_id": chat.id, "user_id": user.id}, {"$set": {"xp": new_xp}}, upsert=True)
    cooldown_dict[user.id] = time.time()
    
    if new_level > old_level:
        await update.message.reply_text(
            f"🎉 Congratulations, {user.mention_html()}! You've reached **Level {new_level}**!",
            parse_mode=ParseMode.HTML
        )

# --- User Commands ---
@check_disabled
async def rank_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Shows the user's rank, XP, and level."""
    chat_id = await resolve_target_chat_id(update, context)
    user_to_check_id, user_to_check_name = await extract_user(update, context)
    if not user_to_check_id:
        user_to_check_id = update.effective_user.id
        user_to_check_name = update.effective_user.first_name
        
    user_xp_doc = xp_collection.find_one({"chat_id": chat_id, "user_id": user_to_check_id}) or {}
    xp = user_xp_doc.get("xp", 0)
    level, xp_in_level, xp_needed = xp_to_level(xp)
    
    progress = xp_in_level / xp_needed if xp_needed > 0 else 0
    progress_bar = "█" * int(progress * 10) + "░" * (10 - int(progress * 10))
    
    msg = (f"<b>🏅 Rank for {user_to_check_name}</b>\n\n"
           f"<b>Level:</b> <code>{level}</code>\n"
           f"<b>XP:</b> <code>{xp}</code>\n"
           f"<b>Progress:</b> <code>{xp_in_level} / {xp_needed}</code>\n"
           f"<code>[{progress_bar}] ({progress:.0%})</code>")
    await update.message.reply_text(msg, parse_mode=ParseMode.HTML)

# --- Admin Commands ---
@admin_only
async def toggle_xp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggles the XP system on or off."""
    chat_id = await resolve_target_chat_id(update, context)
    settings = chat_settings_collection.find_one({"_id": chat_id}) or {}
    new_status = not settings.get("xp_enabled", False)
    
    chat_settings_collection.update_one({"_id": chat_id}, {"$set": {"xp_enabled": new_status}}, upsert=True)
    status = "enabled" if new_status else "disabled"
    await update.message.reply_text(f"✅ XP system has been <b>{status}</b>.", parse_mode=ParseMode.HTML)

@admin_only
async def set_xp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manually sets XP for a user."""
    chat_id = await resolve_target_chat_id(update, context)
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("Usage: `/setxp <user> <amount>`")
        return
        
    target_id, target_name = await extract_user(update, context)
    if not target_id: return
    
    try: amount = int(args[1])
    except ValueError:
        await update.message.reply_text("The amount must be a number.")
        return
        
    xp_collection.update_one({"chat_id": chat_id, "user_id": target_id}, {"$set": {"xp": amount}}, upsert=True)
    await update.message.reply_text(f"✅ Set XP for <b>{target_name}</b> to <b>{amount}</b>.", parse_mode=ParseMode.HTML)

@admin_only
async def reset_xp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Asks for confirmation to reset all chat XP."""
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("⚠️ Yes, reset all XP", callback_data="xp:reset_confirm"),
        InlineKeyboardButton("Cancel", callback_data="xp:reset_cancel")]])
    await update.message.reply_text("Are you sure you want to delete all XP data for this chat? This cannot be undone.", reply_markup=keyboard)

async def reset_xp_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /resetxp confirmation."""
    query = update.callback_query
    chat_id = query.message.chat.id
    if not await is_user_admin(context, chat_id, query.from_user.id):
        await query.answer("Only admins can do this.", show_alert=True)
        return

    if query.data.endswith("confirm"):
        xp_collection.delete_many({"chat_id": chat_id})
        await query.edit_message_text("✅ All XP data for this chat has been reset.")
    else:
        await query.edit_message_text("Action cancelled.")
