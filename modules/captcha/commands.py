import random
from datetime import datetime, timedelta, timezone
from telegram import Update, ChatPermissions, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode, ChatMemberStatus

from database.db import db
from utils.decorators import admin_only
from utils.context import resolve_target_chat_id
# Import the full formatting pipeline for welcome messages
from utils.formatters import select_random, apply_fillings, parse_buttons, extract_send_options

chat_settings_collection = db["chat_settings"]
pending_captchas_collection = db["pending_captchas"]

# --- Job Queue Callbacks for Timeouts ---
async def _kick_user_job(context: ContextTypes.DEFAULT_TYPE):
    """Job to automatically kick a user if they fail to solve the CAPTCHA."""
    job_data = context.job.data
    chat_id, user_id = job_data['chat_id'], job_data['user_id']
    
    # Find and delete the pending record. If it exists, the user hasn't solved it.
    pending_user = pending_captchas_collection.find_one_and_delete({"chat_id": chat_id, "user_id": user_id})
    if pending_user:
        try:
            # Kick is a temporary ban
            await context.bot.ban_chat_member(chat_id, user_id, until_date=datetime.now() + timedelta(seconds=45))
            # Delete the original CAPTCHA message
            await context.bot.delete_message(chat_id, pending_user['captcha_message_id'])
        except Exception as e:
            print(f"Error in kick job: {e}")

# --- CAPTCHA Generation Logic ---
def generate_captcha(mode: str, button_text: str):
    """Generates the text, keyboard, and correct answer for a given CAPTCHA mode."""
    if mode == "math":
        a, b = random.randint(1, 10), random.randint(1, 10)
        correct_answer = a + b
        answers = {correct_answer}
        while len(answers) < 4: answers.add(random.randint(2, 20))
        
        shuffled_answers = random.sample(list(answers), len(answers))
        buttons = [InlineKeyboardButton(str(ans), callback_data=f"captcha:answer:{ans}") for ans in shuffled_answers]
        keyboard = InlineKeyboardMarkup([buttons])
        text = f"To prove you're human, please solve: **{a} + {b} = ?**"
        return text, keyboard, str(correct_answer)
        
    # Default to button mode
    text = "Please prove you're human by clicking the button below."
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton(button_text, callback_data="captcha:answer:solve")]])
    return text, keyboard, "solve"

# --- Core Handlers ---
async def handle_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """The entry point that triggers when a new user joins."""
    new_member_update = update.chat_member
    if not new_member_update: return

    chat = new_member_update.chat
    new_user = new_member_update.new_chat_member.user
    
    is_join = (new_member_update.new_chat_member.status == ChatMemberStatus.MEMBER 
               and new_member_update.old_chat_member.status == ChatMemberStatus.LEFT)
    if not is_join or new_user.is_bot: return
        
    settings = chat_settings_collection.find_one({"_id": chat.id}) or {}
    if not settings.get("captcha_enabled", False):
        return

    # Mute user immediately
    try:
        await context.bot.restrict_chat_member(chat.id, new_user.id, ChatPermissions(can_send_messages=False))
    except Exception as e:
        print(f"Failed to mute new user for CAPTCHA: {e}")
        return

    # --- Integration with Greetings: Combine welcome message and CAPTCHA ---
    welcome_text = settings.get("welcome_message", "Welcome {first} to {chatname}!")
    # We only run the randomizer and fillings part of the pipeline here.
    # The CAPTCHA logic will provide its own buttons.
    chosen_welcome = select_random(welcome_text)
    filled_welcome = apply_fillings(chosen_welcome, update)

    # --- Send CAPTCHA and schedule jobs ---
    captcha_text, keyboard, correct_answer = generate_captcha(
        settings.get("captcha_mode", "button"), 
        settings.get("captcha_button_text", "I am not a bot")
    )
    
    full_message_text = f"{filled_welcome}\n\n{captcha_text}"
    
    sent_message = await context.bot.send_message(
        chat.id, text=full_message_text, reply_markup=keyboard, parse_mode=ParseMode.HTML
    )
    
    pending_captchas_collection.insert_one({
        "chat_id": chat.id, "user_id": new_user.id,
        "captcha_message_id": sent_message.message_id,
        "correct_answer": correct_answer,
        "created_at": datetime.now(timezone.utc)
    })

    kick_time = settings.get("captcha_kicktime_seconds", 300) # Default 5 mins
    if settings.get("captcha_kick", True) and kick_time > 0:
        context.job_queue.run_once(
            _kick_user_job, kick_time, 
            data={"chat_id": chat.id, "user_id": new_user.id}, 
            name=f"captchakick_{chat.id}_{new_user.id}"
        )

async def handle_captcha_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the user's interaction with the CAPTCHA buttons."""
    query = update.callback_query
    user_id_to_check = int(query.from_user.id)
    chat_id = query.message.chat.id
    
    pending_user = pending_captchas_collection.find_one({"chat_id": chat_id, "user_id": user_id_to_check})
    if not pending_user:
        await query.answer("This CAPTCHA is not for you or has expired.", show_alert=True)
        return
        
    _, action, submitted_answer = query.data.split(":")
    
    if submitted_answer == pending_user["correct_answer"]:
        await query.answer("Correct! Welcome.", show_alert=False)
        try:
            # Unmute the user with full permissions
            await context.bot.restrict_chat_member(chat_id, user_id_to_check, ChatPermissions(
                can_send_messages=True, can_send_media_messages=True, 
                can_send_other_messages=True, can_add_web_page_previews=True))
            await query.message.delete()
            
            # Clean up scheduled jobs and DB record
            job_name = f"captchakick_{chat_id}_{user_id_to_check}"
            for job in context.job_queue.get_jobs_by_name(job_name): job.schedule_removal()
            pending_captchas_collection.delete_one({"_id": pending_user["_id"]})
        except Exception as e:
            print(f"Error during CAPTCHA success cleanup: {e}")
    else:
        await query.answer("That's not correct. Please try again.", show_alert=True)

# --- Admin Commands ---
@admin_only
async def toggle_captcha(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Enables or disables CAPTCHA for the chat."""
    chat_id = await resolve_target_chat_id(update, context)
    args = context.args
    if not args or args[0].lower() not in ["on", "off", "yes", "no"]:
        await update.message.reply_text("Usage: `/captcha <on/off>`")
        return
        
    enabled = args[0].lower() in ["on", "yes"]
    chat_settings_collection.update_one(
        {"_id": chat_id}, {"$set": {"captcha_enabled": enabled}}, upsert=True
    )
    status = "enabled" if enabled else "disabled"
    await update.message.reply_text(f"✅ CAPTCHA has been **{status}**.", parse_mode=ParseMode.HTML)
