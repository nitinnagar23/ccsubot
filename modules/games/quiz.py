import asyncio
import random
from telegram import Update, Poll
from telegram.ext import ContextTypes
from telegram.constants import ParseMode, ChatMemberStatus
from telegram.error import BadRequest

from database.db import db
from utils.decorators import admin_only, check_disabled
from utils.context import resolve_target_chat_id

# --- Database Collections ---
quiz_questions_collection = db["quiz_questions"]
quiz_scores_collection = db["quiz_scores"]

# --- Helper Functions ---
async def _send_next_question(context: ContextTypes.DEFAULT_TYPE, chat_id: int):
    """Fetches a new question and sends it as a quiz poll."""
    # Fetch a random approved question using an aggregation pipeline
    pipeline = [{"$match": {"status": "approved"}}, {"$sample": {"size": 1}}]
    question_doc = next(iter(quiz_questions_collection.aggregate(pipeline)), None)

    if not question_doc:
        await context.bot.send_message(chat_id, "There are no quiz questions in my database! An admin needs to add some first.")
        await _stop_quiz_logic(context, chat_id) # Stop the quiz
        return

    context.chat_data['current_question_doc'] = question_doc
    
    question_text = f"Category: {question_doc.get('category', 'General')}\n\n{question_doc['question']}"
    
    try:
        quiz_message = await context.bot.send_poll(
            chat_id=chat_id, question=question_text, options=question_doc['options'],
            type=Poll.QUIZ, correct_option_id=question_doc['correct_option_index'],
            open_period=30, is_anonymous=False
        )
        # We need to save the poll ID to check the answer later
        context.chat_data['current_poll_id'] = quiz_message.poll.id
    except BadRequest as e:
        print(f"Error sending quiz poll: {e}")
        await _stop_quiz_logic(context, chat_id)

async def _stop_quiz_logic(context: ContextTypes.DEFAULT_TYPE, chat_id: int):
    """The core logic to stop a quiz, tally scores, and clean up."""
    if not context.chat_data.get('quiz_active', False): return

    current_scores = context.chat_data.get('quiz_scores', {})
    if current_scores:
        leaderboard = sorted(current_scores.items(), key=lambda item: item[1], reverse=True)
        msg = "🏁 <b>Quiz Over!</b> Final Scores:\n\n"
        for user_id, score in leaderboard[:5]:
            try:
                user = await context.bot.get_chat(user_id)
                msg += f"• {user.mention_html()}: {score} points\n"
            except: pass
        await context.bot.send_message(chat_id, msg, parse_mode=ParseMode.HTML)

    for key in ['quiz_active', 'quiz_scores', 'current_question_doc', 'current_poll_id']:
        context.chat_data.pop(key, None)

# --- Command Handlers ---
@check_disabled
async def start_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Starts a new quiz in the chat."""
    chat_id = await resolve_target_chat_id(update, context)
    
    if context.chat_data.get('quiz_active', False):
        await update.message.reply_text("A quiz is already in progress!")
        return

    await update.message.reply_text("Alright, let's start a quiz! The first question is coming right up. Good luck!")
    context.chat_data['quiz_active'] = True
    context.chat_data['quiz_scores'] = {}
    
    await _send_next_question(context, chat_id)

@admin_only
async def stop_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Stops the currently running quiz."""
    chat_id = await resolve_target_chat_id(update, context)
    if not context.chat_data.get('quiz_active', False):
        await update.message.reply_text("There is no quiz running to stop.")
        return
        
    await _stop_quiz_logic(context, chat_id)

# --- Poll Answer Handler ---
async def handle_quiz_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles when a user answers a quiz poll and awards points."""
    poll_answer = update.poll_answer
    user = poll_answer.user
    
    # Check if a quiz is active and if the answered poll is the current one
    if not context.chat_data.get('quiz_active', False) or poll_answer.poll_id != context.chat_data.get('current_poll_id'):
        return

    question_doc = context.chat_data.get('current_question_doc')
    if not question_doc: return

    # Check if the selected option is correct
    # The `option_ids` list contains the index of the user's choice.
    if poll_answer.option_ids and poll_answer.option_ids[0] == question_doc['correct_option_index']:
        # Award points
        current_scores = context.chat_data.setdefault('quiz_scores', {})
        current_scores[user.id] = current_scores.get(user.id, 0) + 1
        
        # Update persistent all-time score
        quiz_scores_collection.update_one(
            {"chat_id": context.chat_data.get('chat_id', update.effective_chat.id), "user_id": user.id},
            {"$inc": {"score": 1}},
            upsert=True
        )
        
        # Send next question after a short delay
        chat_id = next(iter(quiz_scores_collection.find({"user_id": user.id}).limit(1)))['chat_id'] # A bit of a hack to get chat_id
        context.job_queue.run_once(
            lambda ctx: _send_next_question(ctx, chat_id), 
            3, # 3 second delay
            name=f"next_quiz_q_{chat_id}"
        )
