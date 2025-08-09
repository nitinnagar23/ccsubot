import re
from datetime import timedelta, datetime, timezone
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

# --- Local Imports ---
from database.db import db
from utils.decorators import admin_only, check_disabled
from utils.permissions import is_user_admin
from utils.context import resolve_target_chat_id
from utils.formatters import select_random, apply_fillings, parse_buttons, extract_send_options
from utils.time import parse_duration, humanize_delta
from .jobs import send_repeated_note_job

# --- Service Integrations ---
from modules.log_channels.service import log_action
from modules.cleaning_bot_messages.service import schedule_bot_message_deletion

notes_collection = db["notes"]
chat_settings_collection = db["chat_settings"]

# --- Core Helper to Send a Note ---
async def _send_note(note_doc: dict, update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Central logic for checking permissions, formatting, and sending a note."""
    chat = update.effective_chat
    user = update.effective_user
    
    if note_doc.get("permission") == "admin" and not await is_user_admin(context, chat.id, user.id):
        sent_message = await update.message.reply_text("This is an admin-only note.")
        schedule_bot_message_deletion(context, sent_message, "note")
        return

    settings = chat_settings_collection.find_one({"_id": chat.id}) or {}
    note_privacy = note_doc.get("privacy", "default")
    global_privacy = settings.get("privatenotes_enabled", False)
    is_private_delivery = (note_privacy == 'private') or (note_privacy == 'noprivate' is False and global_privacy)
    
    if is_private_delivery and chat.type != 'private':
        pm_keyboard = [[InlineKeyboardButton(f"Click to get note '#{note_doc['note_name']}'", url=f"https://t.me/{context.bot.username}?start=note_{chat.id}_{note_doc['note_name']}")]]
        await update.message.reply_text("This note will be sent to you in a private message.", reply_markup=InlineKeyboardMarkup(pm_keyboard))
        return

    raw_text = note_doc.get("content", "")
    chosen_text = select_random(raw_text)
    send_options = extract_send_options(chosen_text)
    filled_text = apply_fillings(chosen_text, update)
    final_text, keyboard = parse_buttons(filled_text)
    if note_doc.get("protect_content"): send_options['protect_content'] = True
    
    sent_message = None
    try:
        target_chat_id = user.id if is_private_delivery else chat.id
        reply_func = context.bot.send_message if is_private_delivery else update.message.reply_text

        if note_doc.get("file_id"):
            file_id, file_type = note_doc["file_id"], note_doc["file_type"]
            sender_func = getattr(context.bot, f"send_{file_type}")
            sent_message = await sender_func(target_chat_id, file_id, caption=final_text, reply_markup=keyboard, parse_mode=ParseMode.HTML, **send_options)
        else:
            sent_message = await reply_func(final_text, reply_markup=keyboard, parse_mode=ParseMode.HTML, **send_options)
        
        if sent_message:
            schedule_bot_message_deletion(context, sent_message, "note")
    except Exception as e:
        await update.message.reply_text(f"Error sending note: {e}")

# --- User Handlers ---
@check_disabled
async def get_note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /get <notename>."""
    chat_id = await resolve_target_chat_id(update, context)
    args = context.args
    if not args:
        await update.message.reply_text("You need to specify which note you want to get.")
        return
        
    note_name = args[0].lower()
    if note_name == "rules":
        from modules.rules.commands import rules_command
        await rules_command(update, context)
        return
        
    note_doc = notes_collection.find_one({"chat_id": chat_id, "note_name": note_name})
    if not note_doc:
        await update.message.reply_text("This note does not exist.")
        return

    if len(args) > 1 and args[1].lower() == 'noformat':
        await update.message.reply_text(f"```\n{note_doc.get('content', '')}\n```", parse_mode=ParseMode.MARKDOWN_V2)
        return

    await _send_note(note_doc, update, context)

async def hashtag_note_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for #notename triggers."""
    chat_id = await resolve_target_chat_id(update, context)
    note_names = re.findall(r"#(\w+)", update.message.text)
    if not note_names: return
    
    for note_name in note_names:
        note_name_lower = note_name.lower()
        if note_name_lower == "rules":
            from modules.rules.commands import rules_command
            await rules_command(update, context)
            return
        
        note_doc = notes_collection.find_one({"chat_id": chat_id, "note_name": note_name_lower})
        if note_doc:
            await _send_note(note_doc, update, context)
            return

async def note_button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles clicks on notebuttons from the formatter."""
    query = update.callback_query
    await query.answer()
    note_name = query.data.split(":", 2)[2]
    
    # Fake the update and context args for get_note
    query.message.text = f"/get {note_name}"
    context.args = [note_name]
    await get_note(query, context)

# --- Admin Commands ---
@admin_only
async def save_note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Saves a note and schedules it for repetition if specified."""
    chat_id = await resolve_target_chat_id(update, context)
    args = context.args
    if not args:
        await update.message.reply_text("Usage: /save <notename> <content> or reply to media.")
        return

    note_name = args[0].lower()
    content, file_id, file_type = " ".join(args[1:]), None, None
    
    if update.message.reply_to_message:
        replied = update.message.reply_to_message
        content = " ".join(args[1:]) or replied.caption or ""
        if replied.photo: file_id, file_type = replied.photo[-1].file_id, 'photo'
        elif replied.document: file_id, file_type = replied.document.file_id, 'document'
        elif replied.video: file_id, file_type = replied.video.file_id, 'video'
        elif replied.sticker: file_id, file_type = replied.sticker.file_id, 'sticker'
        elif replied.animation: file_id, file_type = replied.animation.file_id, 'animation'
        elif replied.audio: file_id, file_type = replied.audio.file_id, 'audio'
        elif replied.voice: file_id, file_type = replied.voice.file_id, 'voice'

    if not content and not file_id:
        await update.message.reply_text("There's nothing to save!")
        return

    repeat_interval_seconds = 0
    repeat_match = re.search(r"\{repeat\s+([\w\d]+)\}", content)
    job_name = f"repeatnote_{chat_id}_{note_name}"
    for job in context.job_queue.get_jobs_by_name(job_name): job.schedule_removal()

    if repeat_match:
        duration = parse_duration(repeat_match.group(1))
        if duration:
            repeat_interval_seconds = duration.total_seconds()
            context.job_queue.run_repeating(
                callback=send_repeated_note_job, interval=repeat_interval_seconds,
                first=repeat_interval_seconds, data={'chat_id': chat_id, 'note_name': note_name},
                name=job_name)
    
    permission = "admin" if "{admin}" in content else "all"
    privacy = "private" if "{private}" in content else "noprivate" if "{noprivate}" in content else "default"
    protect = "{protect}" in content
    clean_content = re.sub(r"\{[^}]+\}", "", content).strip()
    
    notes_collection.update_one(
        {"chat_id": chat_id, "note_name": note_name},
        {"$set": {
            "content": clean_content, "file_id": file_id, "file_type": file_type,
            "permission": permission, "privacy": privacy, "protect_content": protect,
            "repeat_interval_seconds": repeat_interval_seconds
        }}, upsert=True)
    
    msg = f"✅ Note `#{note_name}` saved."
    if repeat_interval_seconds > 0: msg += f"\nIt will repeat every **{humanize_delta(timedelta(seconds=repeat_interval_seconds))}**."
    await update.message.reply_text(msg, parse_mode=ParseMode.HTML)

@admin_only
async def clear_note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Deletes a note."""
    chat_id = await resolve_target_chat_id(update, context)
    note_name = " ".join(context.args).lower()
    if not note_name: return

    result = notes_collection.find_one_and_delete({"chat_id": chat_id, "note_name": note_name})
    if result:
        job_name = f"repeatnote_{chat_id}_{note_name}"
        for job in context.job_queue.get_jobs_by_name(job_name): job.schedule_removal()
        await update.message.reply_text(f"Note `#{note_name}` has been cleared.", parse_mode=ParseMode.MARKDOWN_V2)
    else: await update.message.reply_text("This note does not exist.")

@admin_only
async def list_notes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lists all notes in the chat."""
    chat_id = await resolve_target_chat_id(update, context)
    all_notes = list(notes_collection.find({"chat_id": chat_id}))
    if not all_notes:
        await update.message.reply_text("There are no saved notes in this chat.")
        return
    msg = "<b>Saved Notes:</b> " + " ".join([f"<code>#{note['note_name']}</code>" for note in all_notes])
    await update.message.reply_text(msg, parse_mode=ParseMode.HTML)

@admin_only
async def clearall_notes_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Asks for confirmation to delete all notes."""
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("⚠️ Yes, delete all notes", callback_data="note:clearall_confirm"),
        InlineKeyboardButton("Cancel", callback_data="note:clearall_cancel")]])
    await update.message.reply_text("Are you sure you want to delete ALL notes in this chat?", reply_markup=keyboard)

async def clearall_notes_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    chat_id = query.message.chat.id
    if not await is_user_admin(context, chat_id, query.from_user.id):
        await query.answer("Only admins can do this.", show_alert=True)
        return
    if query.data.endswith("confirm"):
        notes_collection.delete_many({"chat_id": chat_id})
        # Also remove all repeating note jobs for this chat
        for job in context.job_queue.jobs():
            if job.name.startswith(f"repeatnote_{chat_id}_"):
                job.schedule_removal()
        await query.edit_message_text("✅ All notes for this chat have been deleted.")
    else:
        await query.edit_message_text("Action cancelled.")

@admin_only
async def toggle_private_notes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggle whether notes are sent in PM by default."""
    chat_id = await resolve_target_chat_id(update, context)
    if not context.args or context.args[0].lower() not in ["on", "off", "yes", "no"]:
        await update.message.reply_text("Usage: `/privatenotes <on/off>`")
        return
    enabled = context.args[0].lower() in ["on", "yes"]
    chat_settings_collection.update_one({"_id": chat_id}, {"$set": {"privatenotes_enabled": enabled}}, upsert=True)
    status = "will now be sent in private" if enabled else "will now be sent in the group"
    await update.message.reply_text(f"✅ Notes {status} by default.")

@admin_only
async def stop_repeat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Stops a note from repeating."""
    chat_id = await resolve_target_chat_id(update, context)
    note_name = " ".join(context.args).lower()
    if not note_name:
        await update.message.reply_text("Usage: `/stoprepeat <notename>`")
        return
    
    job_name = f"repeatnote_{chat_id}_{note_name}"
    jobs = context.job_queue.get_jobs_by_name(job_name)
    if not jobs:
        await update.message.reply_text(f"Note `#{note_name}` is not a repeating note.", parse_mode=ParseMode.MARKDOWN_V2)
        return
        
    for job in jobs: job.schedule_removal()
    notes_collection.update_one({"chat_id": chat_id, "note_name": note_name}, {"$set": {"repeat_interval_seconds": 0}})
    await update.message.reply_text(f"✅ Note `#{note_name}` will no longer repeat.", parse_mode=ParseMode.MARKDOWN_V2)

@admin_only
async def list_repeated_notes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lists all notes that are scheduled to repeat."""
    chat_id = await resolve_target_chat_id(update, context)
    repeating_notes = list(notes_collection.find({"chat_id": chat_id, "repeat_interval_seconds": {"$gt": 0}}))
    if not repeating_notes:
        await update.message.reply_text("There are no repeating notes in this chat.")
        return
    msg = "<b>Repeating Notes:</b>\n\n"
    for note in repeating_notes:
        interval = humanize_delta(timedelta(seconds=note['repeat_interval_seconds']))
        msg += f"- <code>#{note['note_name']}</code> (every {interval})\n"
    await update.message.reply_text(msg, parse_mode=ParseMode.HTML)
