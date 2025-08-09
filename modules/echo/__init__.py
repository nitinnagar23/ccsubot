import re
from telegram.ext import CommandHandler, MessageHandler, filters

from .commands import echo, broadcast
from bot_core.registry import COMMAND_REGISTRY, HELP_REGISTRY

def load_module(application):
    """Loads the Echo module."""
    # Register commands
    COMMAND_REGISTRY["echo"] = {"module": "Echo", "category": "admin", "help": "Repeats your message, preserving formatting."}
    COMMAND_REGISTRY["say"] = {"module": "Echo", "category": "admin", "help": "Alias for /echo."}
    COMMAND_REGISTRY["broadcast"] = {"module": "Echo", "category": "admin", "help": "Bot owner only. Sends a message to all chats."}
    
    HELP_REGISTRY["Echo"] = {cmd: info["help"] for cmd, info in COMMAND_REGISTRY.items() if info["module"] == "Echo"}

    handlers = {
        "echo": echo,
        "say": echo, # Alias
        "broadcast": broadcast
    }

    for cmd_name, handler_func in handlers.items():
        application.add_handler(CommandHandler(cmd_name, handler_func))
        application.add_handler(MessageHandler(
            filters.Regex(rf'^{re.escape("!")}{cmd_name}(\s|$)'),
            handler_func
        ))
