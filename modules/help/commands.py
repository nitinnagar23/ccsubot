import math
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from bot_core.registry import COMMAND_REGISTRY
from utils.decorators import check_disabled

# --- Constants ---
ITEMS_PER_PAGE = 8 # Number of buttons per page

# --- Helper to build the dynamic keyboard ---
def build_help_keyboard(page: int = 0, module: str = None) -> InlineKeyboardMarkup:
    """Builds the multi-level, paginated help keyboard."""
    buttons = []
    
    if module:
        # --- COMMANDS VIEW ---
        all_cmds = sorted([cmd for cmd, info in COMMAND_REGISTRY.items() if info.get("module") == module])
        header_text = f"📖 {module}"
        
        start = page * ITEMS_PER_PAGE
        end = start + ITEMS_PER_PAGE
        cmds_on_page = all_cmds[start:end]

        for cmd in cmds_on_page:
            # We create a button for each command that shows its help text when clicked
            help_text = COMMAND_REGISTRY[cmd]['help']
            buttons.append([InlineKeyboardButton(f"/{cmd}", callback_data=f"help:cmd_info:{cmd}:{help_text}")])

        nav_row = []
        if page > 0:
            nav_row.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"help:module:{module}:{page-1}"))
        
        nav_row.append(InlineKeyboardButton("⬅️ Back", callback_data=f"help:main:main:0"))
        
        if end < len(all_cmds):
            nav_row.append(InlineKeyboardButton("Next ➡️", callback_data=f"help:module:{module}:{page+1}"))
        
        footer = nav_row

    else:
        # --- MAIN MODULES VIEW ---
        all_modules = sorted(list(set(info['module'] for info in COMMAND_REGISTRY.values())))
        header_text = "📚 Command Modules"
        
        start = page * ITEMS_PER_PAGE
        end = start + ITEMS_PER_PAGE
        modules_on_page = all_modules[start:end]
        
        for mod_name in modules_on_page:
            buttons.append([InlineKeyboardButton(mod_name, callback_data=f"help:module:{mod_name}:0")])
            
        nav_row = []
        if page > 0:
            nav_row.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"help:main:main:{page-1}"))

        # We don't add a close button, user can just delete the message
        
        if end < len(all_modules):
            nav_row.append(InlineKeyboardButton("Next ➡️", callback_data=f"help:main:main:{page+1}"))
        
        footer = nav_row
        
    keyboard_layout = [[InlineKeyboardButton(header_text, callback_data="help:dummy:x:0")]] + buttons
    if footer:
        keyboard_layout.append(footer)
        
    return InlineKeyboardMarkup(keyboard_layout)

# --- Command and Callback Handlers ---
@check_disabled
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends the main, top-level help menu."""
    keyboard = build_help_keyboard()
    await update.message.reply_text("Here are my available command modules. Click a module to see its commands.", reply_markup=keyboard)

async def help_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles all interactions with the help menu."""
    query = update.callback_query
    await query.answer()

    _ , level, data, page_str = query.data.split(":", 3)
    page = int(page_str)

    if level == "main":
        keyboard = build_help_keyboard(page=page)
        await query.edit_message_text("Here are my available command modules.", reply_markup=keyboard)
    
    elif level == "module":
        module_name = data
        keyboard = build_help_keyboard(page=page, module=module_name)
        await query.edit_message_text(f"Commands for module: *{module_name}*", parse_mode=ParseMode.MARKDOWN_V2, reply_markup=keyboard)
        
    elif level == "cmd_info":
        cmd_name = data
        help_text = page_str # We cleverly passed the help text in the page_str part of the data
        await query.answer(f"/{cmd_name}: {help_text}", show_alert=True)
