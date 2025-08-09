import re
from telegram.ext import CommandHandler, MessageHandler, filters, CallbackQueryHandler

from .commands import get_note, hashtag_note_handler, save_note #, ... other handlers
from bot_core.registry import COMMAND_REGISTRY, HELP_REGISTRY

def load_module(application):
    """Loads the Notes and Repeated Notes module."""
    user_cmds = {"get": "Get a note by its name. Or, just use #notename."}
    for cmd, help in user_cmds.items():
        COMMAND_REGISTRY[cmd] = {"module": "Notes", "category": "user", "help": help}
        
    admin_cmds = {
        "save": "Save a new note. Supports media and advanced formatting.",
        "clear": "Delete a note.",
        "notes": "List all notes in the chat.",
        "stoprepeat": "Stops a note from repeating.",
        "repeatednotes": "Lists all notes that are scheduled to repeat.",
        # ... other admin note commands
    }
    for cmd, help in admin_cmds.items():
        COMMAND_REGISTRY[cmd] = {"module": "Notes", "category": "admin", "help": help}
        
    HELP_REGISTRY["Notes"] = {**user_cmds, **admin_cmds}
    
    # Add command handlers
    application.add_handler(CommandHandler("get", get_note))
    application.add_handler(CommandHandler("save", save_note))
    # ... other command handlers
    
    # Add message handlers
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.Regex(r'#\w+'), hashtag_note_handler))
    
    # Add callback handler for notebuttons
    # application.add_handler(CallbackQueryHandler(note_button_callback, pattern="^note:open:"))
