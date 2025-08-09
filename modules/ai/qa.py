import os
import google.generativeai as genai
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ChatAction, ParseMode

from utils.decorators import check_disabled
from utils.config import GEMINI_API_KEY

# Configure the Gemini API client only if the key exists
if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
    except Exception as e:
        print(f"Failed to configure Gemini API: {e}")
        GEMINI_API_KEY = None # Disable feature if config fails
else:
    print("⚠️ GEMINI_API_KEY not found. AI Q&A feature will be disabled.")


# Command handler for /ask
@check_disabled
async def ask_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Answers a user's question using the Gemini AI model."""
    if not GEMINI_API_KEY:
        await update.message.reply_text("The AI Q&A feature is not configured by the bot owner.")
        return

    question = " ".join(context.args)
    if not question:
        await update.message.reply_text("Please ask me a question! Usage: `/ask What is the capital of Uttar Pradesh?`")
        return

    # Acknowledge the request and show a "typing" status for good UX
    processing_message = await update.message.reply_text("🧠 Thinking...")
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)

    try:
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
        # Use generate_content_async for non-blocking API calls
        response = await model.generate_content_async(question)
        
        # Edit the "Thinking..." message with the final answer.
        # Use Markdown for formatting, as Gemini often uses it.
        await processing_message.edit_text(response.text, parse_mode=ParseMode.MARKDOWN)
        
    except Exception as e:
        # Handle potential errors from the API (e.g., rate limits, safety blocks)
        error_message = f"Sorry, I encountered an error while processing your request.\n\n`{str(e)}`"
        await processing_message.edit_text(error_message, parse_mode=ParseMode.MARKDOWN_V2)
