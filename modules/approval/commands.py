from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

# --- Local Imports ---
from database.db import db
from utils.decorators import admin_only, check_disabled
from utils.parsers import extract_user
from utils.permissions import is_user_admin, is_user_approved
from utils.context import resolve_target_chat_id

# --- Service Integrations ---
from modules.log_channels.service import log_action

chat_settings_collection = db["chat_settings"]

# --- User Command ---
@check_disabled
async def approval_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Checks the approval status of a user."""
    target_chat_id = await resolve_target_chat_id(update, context)
    
    user_to_check_id, user_to_check_name = await extract_user(update, context)
    
    if not user_to_check_id:
        user_to_check = update.effective_user
        user_to_check_id, user_to_check_name = user_to_check.id, user_to_check.first_name
    
    user_mention = f"<a href='tg://user?id={user_to_check_id}'>{user_to_check_name}</a>"

    if await is_user_admin(context, target_chat_id, user_to_check_id):
        status = "an <b>Admin</b>."
    elif is_user_approved(target_chat_id, user_to_check_id):
        status = "<b>Approved</b>."
    else:
        status = "not approved."

    await update.message.reply_text(f"User {user_mention} is {status}", parse_mode=ParseMode.HTML)

# --- Admin Commands ---
@admin_only
async def approve_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Approves a user, exempting them from certain rules."""
    admin = update.effective_user
    target_chat_id = await resolve_target_chat_id(update, context)
    user_to_approve_id, user_to_approve_name = await extract_user(update, context)

    if not user_to_approve_id: return

    if await is_user_admin(context, target_chat_id, user_to_approve_id):
        await update.message.reply_text("Admins are automatically approved.")
        return

    chat_settings_collection.update_one(
        {"_id": target_chat_id},
        {"$addToSet": {"approved_users": user_to_approve_id}},
        upsert=True
    )
    user_mention = f"<a href='tg://user?id={user_to_approve_id}'>{user_to_approve_name}</a>"
    await update.message.reply_text(f"✅ {user_mention} has been approved!", parse_mode=ParseMode.HTML)
    
    # --- LOGGING INTEGRATION ---
    log_msg = (f"<b>#APPROVED</b>\n"
               f"<b>Admin:</b> {admin.mention_html()}\n"
               f"<b>User:</b> {user_mention}")
    await log_action(context, target_chat_id, "admins", log_msg)


@admin_only
async def unapprove_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Removes a user's approved status."""
    admin = update.effective_user
    target_chat_id = await resolve_target_chat_id(update, context)
    user_to_unapprove_id, user_to_unapprove_name = await extract_user(update, context)

    if not user_to_unapprove_id: return
        
    chat_settings_collection.update_one(
        {"_id": target_chat_id},
        {"$pull": {"approved_users": user_to_unapprove_id}}
    )
    user_mention = f"<a href='tg://user?id={user_to_unapprove_id}'>{user_to_unapprove_name}</a>"
    await update.message.reply_text(f"❌ {user_mention} is no longer approved.", parse_mode=ParseMode.HTML)

    # --- LOGGING INTEGRATION ---
    log_msg = (f"<b>#UNAPPROVED</b>\n"
               f"<b>Admin:</b> {admin.mention_html()}\n"
               f"<b>User:</b> {user_mention}")
    await log_action(context, target_chat_id, "admins", log_msg)

@admin_only
async def list_approved(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lists all approved users in the chat."""
    target_chat_id = await resolve_target_chat_id(update, context)
    target_chat = await context.bot.get_chat(target_chat_id)
    
    settings = chat_settings_collection.find_one({"_id": target_chat_id})
    approved_ids = settings.get("approved_users", []) if settings else []

    if not approved_ids:
        await update.message.reply_text(f"There are no approved users in <b>{target_chat.title}</b>.", parse_mode=ParseMode.HTML)
        return

    msg = f"<b>Approved Users in {target_chat.title}:</b>\n\n"
    for user_id in approved_ids:
        try:
            user = await context.bot.get_chat(user_id)
            msg += f"- {user.mention_html()} (<code>{user.id}</code>)\n"
        except Exception:
            msg += f"- <i>User not found (<code>{user_id}</code>)</i>\n"
    
    await update.message.reply_text(msg, parse_mode=ParseMode.HTML)

@admin_only
async def unapprove_all_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Asks for confirmation to unapprove all users."""
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("⚠️ Yes, unapprove ALL users", callback_data="approval:unapprove_all_confirm")],
        [InlineKeyboardButton("Cancel", callback_data="approval:unapprove_all_cancel")]
    ])
    await update.message.reply_text("Are you sure? This will remove all users from the approved list.", reply_markup=keyboard)

async def unapprove_all_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the confirmation callback for unapproving all."""
    query = update.callback_query
    admin = query.from_user
    chat_id = await resolve_target_chat_id(update, context)
    
    if not await is_user_admin(context, chat_id, admin.id):
        await query.answer("Only admins can perform this action.", show_alert=True)
        return

    action = query.data.split(":")[-1]
    if action == "confirm":
        chat_settings_collection.update_one({"_id": chat_id}, {"$set": {"approved_users": []}})
        await query.edit_message_text("✅ All users have been unapproved.")

        # --- LOGGING INTEGRATION ---
        log_msg = (f"<b>#UNAPPROVE_ALL</b>\n"
                   f"<b>Admin:</b> {admin.mention_html()}")
        await log_action(context, chat_id, "admins", log_msg)
    else: # Cancel
        await query.edit_message_text("Action cancelled.")
