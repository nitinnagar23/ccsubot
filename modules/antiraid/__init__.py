import re
from telegram.ext import CommandHandler, MessageHandler, ChatMemberHandler, filters

from .commands import antiraid_command, handle_new_member # Import handlers
from bot_core.registry import COMMAND_REGISTRY, HELP_REGISTRY

def load_module(application):
    """Loads the AntiRaid module."""
    # Define admin commands
    admin_cmds = {
        "antiraid": "Toggle antiraid mode. All new joins will be temporarily banned.",
        "raidtime": "View or set the default antiraid duration (default 6h).",
        "raidactiontime": "View or set the temp-ban duration for new joins (default 1h).",
        "autoantiraid": "Enable automatic antiraid if X users join per minute.",
    }
    
    # A map of commands to their actual handler functions
    handlers = { "antiraid": antiraid_command }

    # Register all commands and add their handlers
    for cmd_name, help_text in admin_cmds.items():
        COMMAND_REGISTRY[cmd_name] = {"module": "AntiRaid", "category": "admin", "help": help_text}
        if cmd_name in handlers:
            handler_func = handlers[cmd_name]
            application.add_handler(CommandHandler(cmd_name, handler_func))
            application.add_handler(MessageHandler(
                filters.Regex(rf'^{re.escape("!")}{cmd_name}(\s|$)'),
                handler_func
            ))
            
    HELP_REGISTRY["AntiRaid"] = admin_cmds
    
    # Add the main chat member handler to check all new joins
    application.add_handler(ChatMemberHandler(handle_new_member, ChatMemberHandler.CHAT_MEMBER))
