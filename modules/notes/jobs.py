from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from database.db import db
from utils.formatters import select_random, apply_fillings, parse_buttons, extract_send_options

notes_collection = db["notes"]

async def send_repeated_note_job(context: ContextTypes.DEFAULT_TYPE):
    """The job that gets executed by the JobQueue to send a repeated note."""
    job = context.job
    chat_id, note_name = job.data['chat_id'], job.data['note_name']
    
    note_doc = notes_collection.find_one({"chat_id": chat_id, "note_name": note_name})
    if not note_doc or note_doc.get("repeat_interval_seconds", 0) == 0:
        # Note was deleted or is no longer repeating, so we stop the job.
        job.schedule_removal()
        return

    # NOTE: Since this job runs without a user context (no one sent a command),
    # fillings like {first}, {mention}, etc., will NOT work.
    # Only {chatname} and other context-free fillings are suitable.
    
    # We create a "dummy" update object for the formatters to use.
    try:
        chat_obj = await context.bot.get_chat(chat_id)
        # Create a simple object that mimics the structure our formatters expect
        dummy_update = type('DummyUpdate', (), {'effective_chat': chat_obj, 'effective_user': None})()
    except Exception as e:
        print(f"Could not fetch chat {chat_id} for repeated note. Removing job. Error: {e}")
        job.schedule_removal()
        return

    # Run the note content through our formatting pipeline
    raw_text = note_doc.get("content", "")
    chosen_text = select_random(raw_text)
    send_options = extract_send_options(chosen_text)
    filled_text = apply_fillings(chosen_text, dummy_update)
    final_text, keyboard = parse_buttons(filled_text)
    
    # Send the note content
    file_id = note_doc.get("file_id")
    file_type = note_doc.get("file_type")
    
    try:
        if file_id:
            sender_func = getattr(context.bot, f"send_{file_type}", None)
            if sender_func:
                await sender_func(chat_id, file_id, caption=final_text, reply_markup=keyboard, parse_mode=ParseMode.HTML, **send_options)
        else:
            await context.bot.send_message(chat_id, text=final_text, reply_markup=keyboard, parse_mode=ParseMode.HTML, **send_options)
    except Exception as e:
        print(f"Failed to send repeated note '{note_name}' to chat {chat_id}. Error: {e}")
