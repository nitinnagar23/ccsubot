from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from utils.decorators import check_disabled
from utils.config import SUPPORT_GROUP_URL
# We will need to call handlers from other modules for deep linking
from modules.rules.commands import rules_command
from modules.formatting.commands import markdown_help_command
from modules.notes.commands import get_note

@check_disabled
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /start command and deep link payloads."""
    args = context.args
    
    # --- Deep Link Handling ---
    if args:
        payload = args[0]
        if payload == "help":
            # This is a placeholder for a deep link to the main help menu
            # In a full implementation, this would call the help command.
            await update.message.reply_text("Here is the main help menu:")
            return
        elif payload == "markdownhelp":
            await markdown_help_command(update, context)
            return
        elif payload.startswith("rules_"):
            try:
                # Payload is "rules_{chat_id}". Temporarily set context for the rules command.
                _, chat_id_str = payload.split("_", 1)
                context.user_data['deep_link_chat_id'] = int(chat_id_str)
                await rules_command(update, context)
                del context.user_data['deep_link_chat_id'] # Clean up
            except:
                await update.message.reply_text("Could not retrieve rules. The link may be invalid.")
            return
        elif payload.startswith("note_"):
            try:
                # Payload is "note_{chat_id}_{note_name}".
                _, chat_id_str, note_name = payload.split("_", 2)
                context.user_data['deep_link_chat_id'] = int(chat_id_str)
                context.args = [note_name] # Fake the /get command arguments
                await get_note(update, context)
                del context.user_data['deep_link_chat_id'] # Clean up
            except:
                 await update.message.reply_text("Could not retrieve the note. The link may be invalid.")
            return

    # --- Standard /start command logic ---
    if update.effective_chat.type == "private":
        bot_name = context.bot.first_name
        user_name = update.effective_user.first_name
        
        text = (
            f"Hello, {user_name}! I'm {bot_name}, a powerful and modular group management bot.\n\n"
            "To get started, add me to one of your groups and make me an admin!"
        )
        
        keyboard_buttons = [
            [InlineKeyboardButton("➕ Add Me to a Group", url=f"https://t.me/{context.bot.username}?startgroup=true")],
            # This button will open the help menu we designed
            [InlineKeyboardButton("📚 Commands Help", callback_data="help:main:main:0")]
        ]
        if SUPPORT_GROUP_URL:
            keyboard_buttons.append([InlineKeyboardButton("💬 Support Group", url=SUPPORT_GROUP_URL)])
            
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard_buttons))
    else:
        # In a group, /start can just be a simple "I'm alive" message
        await update.message.reply_text("I'm alive and running!")
