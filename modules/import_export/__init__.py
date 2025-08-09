import re
from telegram.ext import CommandHandler, MessageHandler, filters, CallbackQueryHandler

from .commands import export_settings, import_settings, reset_settings, reset_callback
from bot_core.registry import COMMAND_REGISTRY, HELP_REGISTRY

def load_module(application):
    """Loads the Import/Export module."""
    # The decorators on the functions handle the permission logic
    cmds = {
        "export": "Generate a file containing your chat's settings.",
        "import": "Chat creator only. Import settings from a file.",
        "reset": "Chat creator only. Reset all bot settings for the chat."
    }
    for cmd, help_text in cmds.items():
        COMMAND_REGISTRY[cmd] = {"module": "ImportExport", "category": "admin", "help": help_text}

    HELP_REGISTRY["ImportExport"] = cmds
    
    handlers = {
        "export": export_settings,
        "import": import_settings,
        "reset": reset_settings,
    }
    for cmd_name, handler_func in handlers.items():
        application.add_handler(CommandHandler(cmd_name, handler_func))
        application.add_handler(MessageHandler(
            filters.Regex(rf'^{re.escape("!")}{cmd_name}(\s|$)'),
            handler_func
        ))
        
    application.add_handler(CallbackQueryHandler(reset_callback, pattern="^reset:"))
