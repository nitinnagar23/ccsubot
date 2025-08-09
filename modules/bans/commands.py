from telegram import Update, ChatPermissions
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from telegram.error import BadRequest

# --- Local Imports ---
from utils.decorators import admin_only, check_disabled
from utils.parsers import extract_user
from utils.permissions import is_user_admin, is_user_approved
from utils.context import resolve_target_chat_id
from utils.time import parse_duration, humanize_delta
from utils.moderation import execute_punishment

# --- Service Integrations ---
from modules.log_channels.service import log_action
from modules.cleaning_bot_messages.service import schedule_bot_message_deletion


# --- Internal Helper to parse arguments ---
async def _parse_user_duration_and_reason(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Internal helper to parse arguments for all moderation commands."""
    user_id, user_name, reason, duration = None, None, "", None
    
    if update.message.reply_to_message:
        replied_user = update.message.reply_to_message.from_user
        user_id, user_name = replied_user.id, replied_user.first_name
        
        if context.args:
            parsed_dur = parse_duration(context.args[0])
            if parsed_dur:
                duration = parsed_dur
                reason = " ".join(context.args[1:])
            else:
                reason = " ".join(context.args)
    elif context.args:
        user_id, user_name = await extract_user(update, context)
        if user_id:
            # Check for duration in the argument following the user identifier
            arg_offset = 2 if context.args[0].isdigit() or context.args[0].startswith('@') else 1
            if len(context.args) >= arg_offset:
                parsed_dur = parse_duration(context.args[arg_offset-1])
                if parsed_dur:
                    duration = parsed_dur
                    reason = " ".join(context.args[arg_offset:])
                else:
                    reason = " ".join(context.args[arg_offset-1:])

    return user_id, user_name, duration, reason.strip()

# --- Central Moderation Executor ---
async def _execute_moderation(update: Update, context: ContextTypes.DEFAULT_TYPE, 
                            action: str, silent: bool = False, delete_reply: bool = False):
    """The core function that handles all ban/mute/kick actions."""
    target_chat_id = await resolve_target_chat_id(update, context)
    target_chat = await context.bot.get_chat(target_chat_id)
    admin = update.effective_user

    if delete_reply and not update.message.reply_to_message:
        await update.message.reply_text("You need to reply to a message to use this variant.")
        return

    target_id, target_name, duration, reason = await _parse_user_duration_and_reason(update, context)
    
    if not target_id:
        await update.message.reply_text("I can't find that user. Please reply or provide their ID.")
        return

    # Safety checks
    if target_id == context.bot.id: return
    if await is_user_admin(context, target_chat_id, target_id):
        await update.message.reply_text("I can't perform moderation actions on an admin.")
        return
    if is_user_approved(target_chat_id, target_id):
        await update.message.reply_text("This user is approved. To moderate them, `/unapprove` them first.")
        return

    # Determine action type (ban vs tban, mute vs tmute)
    final_action = f"t{action}" if duration else action
    
    # Call the centralized punishment utility
    success, action_string = await execute_punishment(context, target_chat_id, target_id, final_action, duration.total_seconds() if duration else 0)

    if not success:
        await update.message.reply_text(f"Could not perform action. {action_string}")
        return

    # Handle variants
    if silent: await update.message.delete()
    if delete_reply: await update.message.reply_to_message.delete()

    # Log the action
    log_msg = (
        f"<b>#{action.upper()}</b>\n"
        f"<b>Admin:</b> {admin.mention_html()} (<code>{admin.id}</code>)\n"
        f"<b>User:</b> {target_name} (<code>{target_id}</code>)\n"
        f"<b>Chat:</b> {target_chat.title}"
    )
    if reason: log_msg += f"\n<b>Reason:</b> {reason}"
    if duration: log_msg += f"\n<b>Duration:</b> {humanize_delta(duration)}"
    await log_action(context, target_chat_id, "bans", log_msg)

    # Send public feedback if not silent
    if not silent:
        feedback = f"User {target_name} has been **{action_string}**."
        if reason: feedback += f"\nReason: {reason}"
        sent_message = await update.message.reply_text(feedback, parse_mode=ParseMode.HTML)
        # --- INTEGRATION: Schedule this confirmation message for deletion ---
        schedule_bot_message_deletion(context, sent_message, "action")

# --- Wrapper Command Handlers ---
@admin_only
async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE): await _execute_moderation(update, context, 'ban')
@admin_only
async def dban(update: Update, context: ContextTypes.DEFAULT_TYPE): await _execute_moderation(update, context, 'ban', delete_reply=True)
@admin_only
async def sban(update: Update, context: ContextTypes.DEFAULT_TYPE): await _execute_moderation(update, context, 'ban', silent=True)
@admin_only
async def tban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    _, _, duration, _ = await _parse_user_duration_and_reason(update, context)
    if not duration:
        await update.message.reply_text("Usage: `/tban <user> <duration>` (e.g., /tban @user 1d)")
        return
    await _execute_moderation(update, context, 'ban')

@admin_only
async def mute(update: Update, context: ContextTypes.DEFAULT_TYPE): await _execute_moderation(update, context, 'mute')
@admin_only
async def dmute(update: Update, context: ContextTypes.DEFAULT_TYPE): await _execute_moderation(update, context, 'mute', delete_reply=True)
@admin_only
async def smute(update: Update, context: ContextTypes.DEFAULT_TYPE): await _execute_moderation(update, context, 'mute', silent=True)
@admin_only
async def tmute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    _, _, duration, _ = await _parse_user_duration_and_reason(update, context)
    if not duration:
        await update.message.reply_text("Usage: `/tmute <user> <duration>` (e.g., /tmute @user 2h)")
        return
    await _execute_moderation(update, context, 'mute')

@admin_only
async def kick(update: Update, context: ContextTypes.DEFAULT_TYPE): await _execute_moderation(update, context, 'kick')
@admin_only
async def dkick(update: Update, context: ContextTypes.DEFAULT_TYPE): await _execute_moderation(update, context, 'kick', delete_reply=True)
@admin_only
async def skick(update: Update, context: ContextTypes.DEFAULT_TYPE): await _execute_moderation(update, context, 'kick', silent=True)

# --- Un-Commands ---
@admin_only
async def unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target_chat_id = await resolve_target_chat_id(update, context)
    target_id, target_name, _, _ = await _parse_user_duration_and_reason(update, context)
    if not target_id: return
    try:
        await context.bot.unban_chat_member(target_chat_id, target_id)
        sent_message = await update.message.reply_text(f"User {target_name} (`{target_id}`) has been unbanned.")
        # --- INTEGRATION: Schedule this confirmation message for deletion ---
        schedule_bot_message_deletion(context, sent_message, "action")
    except BadRequest as e: await update.message.reply_text(f"Error: {e.message}")

@admin_only
async def unmute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target_chat_id = await resolve_target_chat_id(update, context)
    target_id, target_name, _, _ = await _parse_user_duration_and_reason(update, context)
    if not target_id: return
    try:
        await context.bot.restrict_chat_member(target_chat_id, target_id, ChatPermissions(can_send_messages=True, can_send_media_messages=True, can_send_other_messages=True, can_add_web_page_previews=True))
        sent_message = await update.message.reply_text(f"User {target_name} (`{target_id}`) has been unmuted.")
        # --- INTEGRATION: Schedule this confirmation message for deletion ---
        schedule_bot_message_deletion(context, sent_message, "action")
    except BadRequest as e: await update.message.reply_text(f"Error: {e.message}")
        
# --- User Command ---
@check_disabled
async def kickme(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_id = update.effective_chat.id
    if await is_user_admin(context, chat_id, user.id):
        await update.message.reply_text("Admins can't kick themselves.")
        return
    success, _ = await execute_punishment(context, chat_id, user.id, 'kick')
    if success: await update.message.reply_text("Bye bye!")
