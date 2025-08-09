import re
from telegram.ext import CommandHandler, MessageHandler, filters

from .commands import nightmode_command, nightmode_status, set_timezone, check_night_mode
from bot_core.registry import COMMAND_REGISTRY, HELP_REGISTRY

def load_module(application):
    """Loads the Night Mode module."""
    admin_cmds = {
        "nightmode": "Set, enable, or disable night mode.",
        "nightmodestatus": "Check the current night mode status and schedule.",
        "settimezone": "Set the chat's timezone for schedules (e.g., `Asia/Kolkata`).",
        "nightmodeallow": "Add a user to the night mode whitelist.",
        "nightmoderemove": "Remove a user from the whitelist.",
        "nightmodeconfig": "Configure blocked content types for night mode.",
    }
    for cmd, help_text in admin_cmds.items():
        COMMAND_REGISTRY[cmd] = {"module": "NightMode", "category": "admin", "help": help_text}

    HELP_REGISTRY["NightMode"] = admin_cmds
    
    handlers = {
        "nightmode": nightmode_command,
        "nightmodestatus": nightmode_status,
        "settimezone": set_timezone,
    }

    for cmd_name, handler_func in handlers.items():
        application.add_handler(CommandHandler(cmd_name, handler_func))
        application.add_handler(MessageHandler(filters.Regex(rf'^{re.escape("!")}{cmd_name}(\s|$)'), handler_func))

    # Add the main listener.
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, check_night_mode), group=7)
