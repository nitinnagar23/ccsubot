import re
from telegram.ext import CommandHandler, MessageHandler, filters, CallbackQueryHandler

from .commands import (
    grant_xp_on_message, rank_command, toggle_xp, set_xp, reset_xp, reset_xp_callback
    # leaderboard_command would be imported here too
)
from bot_core.registry import COMMAND_REGISTRY, HELP_REGISTRY

def load_module(application):
    """Loads the Gamification module."""
    user_cmds = {
        "rank": "Show your XP and level.",
        "leaderboard": "View the top users in the chat."
    }
    for cmd, help_text in user_cmds.items():
        COMMAND_REGISTRY[cmd] = {"module": "Gamification", "category": "user", "help": help_text}
        
    admin_cmds = {
        "xp": "Toggle the XP system on or off.",
        "setxp": "Set XP for a user.",
        "resetxp": "Reset all XP data for the group.",
        "setxpgain": "Set the amount of XP per message.",
        "setxpcooldown": "Set the cooldown between XP-granting messages."
    }
    for cmd, help_text in admin_cmds.items():
        COMMAND_REGISTRY[cmd] = {"module": "Gamification", "category": "admin", "help": help_text}

    HELP_REGISTRY["Gamification"] = {**user_cmds, **admin_cmds}
    
    handlers = {
        "rank": rank_command, "xp": toggle_xp, "setxp": set_xp, "resetxp": reset_xp,
        # "leaderboard": leaderboard_command
    }
    for cmd_name, handler_func in handlers.items():
        application.add_handler(CommandHandler(cmd_name, handler_func))
        application.add_handler(MessageHandler(filters.Regex(rf'^{re.escape("!")}{cmd_name}(\s|$)'), handler_func))
    
    # Add other handlers
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, grant_xp_on_message), group=15)
    application.add_handler(CallbackQueryHandler(reset_xp_callback, pattern="^xp:reset_"))
