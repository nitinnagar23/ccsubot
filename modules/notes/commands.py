import re
from datetime import timedelta
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from telegram.constants import ParseMode

from database.db import db
from utils.decorators import admin_only, check_disabled
from utils.permissions import is_user_admin
from utils.context import resolve_target_chat_id
from utils.formatters import select_random, apply_fillings, parse_buttons, extract_send_options
from utils.time import parse_duration, humanize_delta
from .jobs import send_repeated_note_job

notes_collection = db["notes"]
chat_settings_collection = db["chat_settings"]

# --- Core Helper to Send a Note ---
async def _send_note(note_doc: dict, update: Update, context: ContextTypes.DEFAULT_TYPE, target_chat):
    """Central logic for checking permissions, formatting, and sending a note."""
    user = update.effective_user
    if note_doc.get("permission") == "admin" and not await is_user_admin(context, target_chat.id, user.id):
        await update.message.reply_text("This is an admin-only note.")
        return

    settings = chat_settings_collection.find_one({"_id": target_chat.id}) or {}
    note_privacy = note_doc.get("privacy", "default")
    global_privacy = settings.get("privatenotes_enabled", False)
    
    is_private_delivery = (note_privacy == 'private') or (note_privacy == 'default' and global_privacy)
    
    if is_private_delivery and target_chat.type != 'private':
        # ... logic to send a button with a deep link to PM ...
        return

    # Format and send the message
    raw_text = note_doc.get("content", "")
    # ... (full formatting pipeline as in previous examples) ...
    # ... (logic to send text or media) ...
    await update.message.reply_text("Note sending logic would be here.") # Placeholder for brevity

# --- User Handlers ---
@check_disabled
async def get_note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /get <notename>."""
    # ... (implementation from previous thought process) ...

async def hashtag_note_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for #notename triggers."""
    # ... (implementation from previous thought process) ...

# --- Admin Commands ---
@admin_only
async def save_note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Saves a note and schedules it for repetition if specified."""
    chat_id = await resolve_target_chat_id(update, context)
    args = context.args
    if not args: return # Add usage message

    note_name = args[0].lower()
    content = " ".join(args[1:]) # Simplified
    
    # Parse for {repeat <time>} tag
    repeat_interval_seconds = 0
    repeat_match = re.search(r"\{repeat\s+([\w\d]+)\}", content)
    job_name = f"repeatnote_{chat_id}_{note_name}"
    
    # Remove any existing job for this note
    for job in context.job_queue.get_jobs_by_name(job_name):
        job.schedule_removal()

    if repeat_match:
        duration = parse_duration(repeat_match.group(1))
        if duration:
            repeat_interval_seconds = duration.total_seconds()
            context.job_queue.run_repeating(
                callback=send_repeated_note_job, interval=repeat_interval_seconds,
                first=repeat_interval_seconds, data={'chat_id': chat_id, 'note_name': note_name},
                name=job_name
            )
    
    # ... (parse other modifiers and save to DB) ...
    notes_collection.update_one(
        {"chat_id": chat_id, "note_name": note_name},
        {"$set": {"content": re.sub(r"\{[^}]+\}", "", content).strip(), "repeat_interval_seconds": repeat_interval_seconds}},
        upsert=True)
    
    msg = f"✅ Note `#{note_name}` saved."
    if repeat_interval_seconds > 0:
        msg += f"\nIt will repeat every **{humanize_delta(timedelta(seconds=repeat_interval_seconds))}**."
    await update.message.reply_text(msg, parse_mode=ParseMode.HTML)

# ... (Implement /clear, /notes, /stoprepeat, etc.)
