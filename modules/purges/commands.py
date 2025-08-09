import asyncio
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from telegram.error import BadRequest

from utils.decorators import admin_only
from utils.context import resolve_target_chat_id
from modules.log_channels.service import log_action

# --- Core Purge Logic ---
async def _purge_messages(context: ContextTypes.DEFAULT_TYPE, chat_id: int, message_ids: list[int]) -> tuple[int, str]:
    """
    Helper to delete messages in batches of 100.
    Returns (deleted_count, status_message).
    """
    deleted_count = 0
    if not message_ids:
        return 0, "No messages to delete in the specified range."

    for i in range(0, len(message_ids), 100):
        batch = message_ids[i:i+100]
        try:
            await context.bot.delete_messages(chat_id=chat_id, message_ids=batch)
            deleted_count += len(batch)
        except BadRequest as e:
            if "message can't be deleted" in e.message.lower():
                # This often happens if messages are older than 48 hours
                return deleted_count, "Stopped early. Some messages may be older than 48 hours and cannot be deleted."
            else:
                print(f"Error during purge: {e.message}")
                return deleted_count, f"An error occurred: {e.message}"
        except Exception as e:
            print(f"An unexpected error occurred during purge: {e}")
            return deleted_count, f"An unexpected error occurred: {e}"
        
        await asyncio.sleep(1) # Be respectful of API limits
        
    return deleted_count, f"✅ Purged {deleted_count} messages."

# --- Admin Commands ---
@admin_only
async def delete_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Deletes the replied-to message."""
    if not update.message.reply_to_message:
        await update.message.reply_text("Reply to a message to delete it.")
        return
    
    try:
        await update.message.reply_to_message.delete()
        await update.message.delete()
    except BadRequest: pass

@admin_only
async def purge_command(update: Update, context: ContextTypes.DEFAULT_TYPE, silent: bool = False):
    """Handler for /purge and /spurge."""
    chat_id = await resolve_target_chat_id(update, context)
    if not update.message.reply_to_message:
        await update.message.reply_text("Reply to a message to start the purge from there.")
        return
        
    start_id = update.message.reply_to_message.message_id
    end_id = update.message.message_id
    
    message_ids_to_purge = list(range(start_id, end_id + 1))
        
    deleted_count, status_msg = await _purge_messages(context, chat_id, message_ids_to_purge)
    
    # Log the action
    admin = update.effective_user
    log_msg = (f"<b>#PURGE</b>\n"
               f"<b>Admin:</b> {admin.mention_html()} (<code>{admin.id}</code>)\n"
               f"<b>Messages Deleted:</b> {deleted_count}")
    await log_action(context, chat_id, "purges", log_msg)

    if not silent and deleted_count > 0:
        confirmation_msg = await context.bot.send_message(chat_id, status_msg)
        context.job_queue.run_once(
            lambda ctx: ctx.bot.delete_message(chat_id, confirmation_msg.message_id),
            5, name=f"del_purgeconf_{chat_id}_{confirmation_msg.message_id}"
        )

@admin_only
async def spurge_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Silent version of /purge."""
    await purge_command(update, context, silent=True)


@admin_only
async def purge_from(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Marks the starting point for a purge."""
    chat_id = await resolve_target_chat_id(update, context)
    if not update.message.reply_to_message:
        await update.message.reply_text("Reply to a message to mark it as the starting point.")
        return
        
    start_id = update.message.reply_to_message.message_id
    context.user_data.setdefault('purge_from', {})[chat_id] = start_id
    
    msg = await update.message.reply_text("✅ Marked this as the starting message. Now, reply to another message with `/purgeto`.")
    context.job_queue.run_once(lambda ctx: ctx.bot.delete_message(chat_id, msg.message_id), 10)
    await update.message.delete()

@admin_only
async def purge_to(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Marks the end point and executes the purge."""
    chat_id = await resolve_target_chat_id(update, context)
    if not update.message.reply_to_message:
        await update.message.reply_text("Reply to a message to mark it as the end point.")
        return

    start_id = context.user_data.get('purge_from', {}).get(chat_id)
    if not start_id:
        await update.message.reply_text("You need to use `/purgefrom` first to mark a starting message.")
        return
    
    end_id = update.message.reply_to_message.message_id
    if end_id <= start_id:
        await update.message.reply_text("The end message must be after the start message.")
        return

    # Clean up state
    del context.user_data['purge_from'][chat_id]
    
    message_ids = list(range(start_id, end_id + 1))
    await update.message.delete()
    deleted_count, status_msg = await _purge_messages(context, chat_id, message_ids)
    
    # Log the action (similar to purge_command)
    
    if deleted_count > 0:
        confirmation_msg = await context.bot.send_message(chat_id, status_msg)
        context.job_queue.run_once(
            lambda ctx: ctx.bot.delete_message(chat_id, confirmation_msg.message_id),
            5, name=f"del_purgeconf_{chat_id}_{confirmation_msg.message_id}"
        )
