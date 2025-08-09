import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from utils.decorators import check_disabled
from utils.permissions import is_user_admin, is_user_approved, is_user_owner
from utils.parsers import extract_user
from utils.context import resolve_target_chat_id
from utils.config import DONATION_URL, DONATION_TEXT

# --- Constants ---
RUNS_STRINGS = [
    "runs to the hills", "runs to the kitchen", "runs to a different country", 
    "runs to the moon", "runs away", "runs into a wall",
]

# --- Commands ---

@check_disabled
async def runs_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends a random 'runs' string."""
    await update.message.reply_text(random.choice(RUNS_STRINGS))

@check_disabled
async def id_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gets the ID of the user, chat, or replied-to user/forwarded message."""
    user = update.effective_user
    chat = update.effective_chat
    
    text = f"Your User ID is: `<code>{user.id}</code>`\n"
    if chat.type != "private":
        text += f"This chat's ID is: `<code>{chat.id}</code>`\n"
    
    # Check for replied-to message
    if update.message.reply_to_message:
        replied_msg = update.message.reply_to_message
        text += f"\nReplied to message ID: `<code>{replied_msg.message_id}</code>`\n"
        replied_user = replied_msg.from_user
        if replied_user:
            text += f"Replied to user's ID: `<code>{replied_user.id}</code>`"

    # Check for forwarded message
    elif update.message.forward_from or update.message.forward_from_chat:
        if update.message.forward_from: # Forwarded from a user
            text += f"\nForwarded from user's ID: `<code>{update.message.forward_from.id}</code>`"
        elif update.message.forward_from_chat: # Forwarded from a channel
            text += f"\nForwarded from channel's ID: `<code>{update.message.forward_from_chat.id}</code>`"

    await update.message.reply_text(text, parse_mode=ParseMode.HTML)

@check_disabled
async def info_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gets information about a user."""
    target_chat_id = await resolve_target_chat_id(update, context)
    
    user_to_check_id, user_to_check_name = await extract_user(update, context)
    if not user_to_check_id:
        user_to_check_id = update.effective_user.id
        user_to_check_name = update.effective_user.first_name

    try:
        user_chat = await context.bot.get_chat(user_to_check_id)
    except:
        await update.message.reply_text("I can't seem to find that user.")
        return

    is_admin_check = await is_user_admin(context, target_chat_id, user_to_check_id)
    is_apprv_check = is_user_approved(target_chat_id, user_to_check_id)
    is_owner_check = is_user_owner(user_to_check_id)

    text = f"<b>User Info for {user_chat.mention_html()}</b>\n"
    text += f"<b>ID</b>: <code>{user_chat.id}</code>\n"
    if user_chat.username: text += f"<b>Username</b>: @{user_chat.username}\n"
        
    text += "\n<b>Permissions in this context:</b>\n"
    text += f"Bot Owner: {'✅' if is_owner_check else '❌'}\n"
    text += f"Chat Admin: {'✅' if is_admin_check else '❌'}\n"
    text += f"Approved User: {'✅' if is_apprv_check else '❌'}\n"
    
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)

@check_disabled
async def donate_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends the bot's donation link."""
    keyboard = None
    if DONATION_URL:
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("❤️ Donate Here", url=DONATION_URL)
        ]])
    
    await update.message.reply_text(DONATION_TEXT, reply_markup=keyboard, disable_web_page_preview=True)

@check_disabled
async def limits_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Shows some of the bot's configured limits."""
    text = (
        "<b>Bot Limits</b>\n\n"
        "These are some of the limits imposed by Telegram or the bot's configuration.\n\n"
        "• Max message length: <code>4096 characters</code>\n"
        "• Max caption length: <code>1024 characters</code>\n"
        "• File upload limit: <code>50 MB</code> (via local upload)\n"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)
