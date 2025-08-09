from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from database.db import db
from utils.decorators import admin_only, check_disabled
from utils.parsers import extract_user
from utils.permissions import is_user_admin, is_user_approved
from utils.context import resolve_target_chat_id

chat_settings_collection = db["chat_settings"]

# --- User Command ---
@check_disabled
async def approval_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Checks the approval status of a user."""
    target_chat_id = await resolve_target_chat_id(update, context)
    
    user_to_check_id, user_to_check_name = await extract_user(update, context)
    
    # If no user was specified, check the user who sent the command
    if not user_to_check_id:
        user_to_check = update.effective_user
        user_to_check_id = user_to_check.id
        user_to_check_name = user_to_check.first_name
    
    user_mention = f"<a href='tg://user?id={user_to_check_id}'>{user_to_check_name}</a>"

    if await is_user_admin(context, target_chat_id, user_to_check_id):
        status = "an **Admin**."
    elif is_user_approved(target_chat_id, user_to_check_id):
        status = "**Approved**."
    else:
        status = "a regular user (not approved)."

    await update.message.reply_text(f"User {user_mention} is {status}", parse_mode=ParseMode.HTML)

# --- Admin Commands ---
@admin_only
async def approve_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Approves a user, exempting them from certain rules."""
    target_chat_id = await resolve_target_chat_id(update, context)
    user_to_approve_id, user_to_approve_name = await extract_user(update, context)

    if not user_to_approve_id:
        return # extract_user sends its own error message

    if await is_user_admin(context, target_chat_id, user_to_approve_id):
        await update.message.reply_text("Admins are automatically approved and do not need to be manually approved.")
        return

    chat_settings_collection.update_one(
        {"_id": target_chat_id},
        {"$addToSet": {"approved_users": user_to_approve_id}},
        upsert=True
    )
    user_mention = f"<a href='tg://user?id={user_to_approve_id}'>{user_to_approve_name}</a>"
    await update.message.reply_text(f"✅ {user_mention} has been approved!", parse_mode=ParseMode.HTML)

@admin_only
async def unapprove_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Removes a user's approved status."""
    target_chat_id = await resolve_target_chat_id(update, context)
    user_to_unapprove_id, user_to_unapprove_name = await extract_user(update, context)

    if not user_to_unapprove_id:
        return
        
    chat_settings_collection.update_one(
        {"_id": target_chat_id},
        {"$pull": {"approved_users": user_to_unapprove_id}}
    )
    user_mention = f"<a href='tg://user?id={user_to_unapprove_id}'>{user_to_unapprove_name}</a>"
    await update.message.reply_text(f"❌ {user_mention} is no longer approved.", parse_mode=ParseMode.HTML)

@admin_only
async def list_approved(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lists all approved users in the chat."""
    target_chat_id = await resolve_target_chat_id(update, context)
    target_chat = await context.bot.get_chat(target_chat_id)
    
    settings = chat_settings_collection.find_one({"_id": target_chat_id})
    approved_ids = settings.get("approved_users", []) if settings else []

    if not approved_ids:
        await update.message.reply_text(f"There are no approved users in **{target_chat.title}**.", parse_mode=ParseMode.HTML)
        return

    msg = f"<b>Approved Users in {target_chat.title}:</b>\n\n"
    for user_id in approved_ids:
        try:
            user = await context.bot.get_chat(user_id)
            msg += f"- {user.mention_html()} (`{user.id}`)\n"
        except Exception:
            msg += f"- <i>User not found (`{user_id}`)</i>\n"
    
    await update.message.reply_text(msg, parse_mode=ParseMode.HTML)

@admin_only
async def unapprove_all_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Asks for confirmation to unapprove all users."""
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("⚠️ Yes, unapprove ALL users", callback_data="approval:unapprove_all_confirm")],
        [InlineKeyboardButton("Cancel", callback_data="approval:unapprove_all_cancel")]
    ])
    await update.message.reply_text(
        "Are you sure you want to unapprove EVERYONE in this chat? This action cannot be undone.",
        reply_markup=keyboard
    )

async def unapprove_all_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the confirmation callback for unapproving all."""
    query = update.callback_query
    user = query.from_user
    chat_id = await resolve_target_chat_id(update, context)
    
    if not await is_user_admin(context, chat_id, user.id):
        await query.answer("Only admins can perform this action.", show_alert=True)
        return

    action = query.data.split(":")[-1]
    if action == "confirm":
        chat_settings_collection.update_one(
            {"_id": chat_id}, {"$set": {"approved_users": []}}
        )
        await query.edit_message_text("✅ All users have been unapproved.")
    else: # Cancel
        await query.edit_message_text("Action cancelled.")
