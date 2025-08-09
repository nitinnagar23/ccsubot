from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from bot_core.registry import COMMAND_REGISTRY
from utils.decorators import check_disabled
# Import our new content files
from .content import HELP_BIO, MODULE_HELP_TEXTS

def build_main_keyboard() -> InlineKeyboardMarkup:
    """Builds the main grid of module buttons."""
    # Get a unique, sorted list of all module names from our registry
    all_modules = sorted(list(set(info['module'] for info in COMMAND_REGISTRY.values())))
    
    buttons = []
    row = []
    # Arrange buttons in a grid of 3 columns
    for module_name in all_modules:
        row.append(InlineKeyboardButton(module_name, callback_data=f"help:module:{module_name}"))
        if len(row) == 3:
            buttons.append(row)
            row = []
    if row: # Add the last row if it's not full
        buttons.append(row)
        
    return InlineKeyboardMarkup(buttons)

@check_disabled
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends the main, top-level help menu."""
    keyboard = build_main_keyboard()
    await update.message.reply_text(HELP_BIO, reply_markup=keyboard, parse_mode=ParseMode.HTML)

async def help_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles all interactions with the help menu."""
    query = update.callback_query
    await query.answer()

    _ , level, data = query.data.split(":", 2)

    if level == "main":
        # User clicked "Back"
        keyboard = build_main_keyboard()
        await query.edit_message_text(HELP_BIO, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    
    elif level == "module":
        # User clicked a module button
        module_name = data
        help_text = MODULE_HELP_TEXTS.get(module_name, "No detailed help available for this module yet.")
        
        # Create a new keyboard with just a "Back" button
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("⬅️ Back to Modules", callback_data="help:main:main")
        ]])
        
        await query.edit_message_text(help_text, reply_markup=keyboard, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
