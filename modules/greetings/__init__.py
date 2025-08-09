import re
from telegram.ext import CommandHandler, MessageHandler, filters, ChatMemberHandler

from .commands import toggle_welcome, set_welcome, handle_member_update # Import handlers
from bot_core.registry import COMMAND_REGISTRY, HELP_REGISTRY

def load_module(application):
    """Loads the Greetings module."""
    admin_cmds = {
        "welcome": "Enable/disable welcome messages.",
        "goodbye": "Enable/disable goodbye messages.",
        "setwelcome": "Set a new welcome message. Supports markdown, buttons, and fillings.",
        "resetwelcome": "Reset the welcome message to default.",
        "setgoodbye": "Set a new goodbye message.",
        "resetgoodbye": "Reset the goodbye message to default.",
        "cleanwelcome": "Delete old welcome messages automatically.",
    }
    for cmd, help_text in admin_cmds.items():
        COMMAND_REGISTRY[cmd] = {"module": "Greetings", "category": "admin", "help": help_text}

    HELP_REGISTRY["Greetings"] = admin_cmds
    
    handlers = {
        "welcome": toggle_welcome,
        "setwelcome": set_welcome,
        # ... add other handlers here ...
    }
    
    for cmd_name, handler_func in handlers.items():
        application.add_handler(CommandHandler(cmd_name, handler_func))
        application.add_handler(MessageHandler(
            filters.Regex(rf'^{re.escape("!")}{cmd_name}(\s|$)'),
            handler_func
        ))

    # Add the main chat member handler to watch for joins and leaves
    application.add_handler(ChatMemberHandler(handle_member_update, ChatMemberHandler.CHAT_MEMBER))
