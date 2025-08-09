import re
from telegram.ext import MessageHandler, ChatMemberHandler, CommandHandler, filters
from .filter import check_for_spam, track_new_member
from .commands import toggle_spam_guard, set_quarantine_time

from bot_core.registry import COMMAND_REGISTRY, HELP_REGISTRY

def load_module(application):
    """Loads the Spam Guard module."""
    admin_cmds = {
        "spamguard": "Toggle the spam guard system on or off.",
        "setquarantine": "Set the restriction time for new members (e.g., 24h, 30m, off)."
    }
    for cmd, help_text in admin_cmds.items():
        COMMAND_REGISTRY[cmd] = {"module": "Spam", "category": "admin", "help": help_text}
    HELP_REGISTRY["Spam"] = admin_cmds
    
    handlers = {
        "spamguard": toggle_spam_guard,
        "setquarantine": set_quarantine_time
    }
    for cmd_name, handler_func in handlers.items():
        application.add_handler(CommandHandler(cmd_name, handler_func))
        application.add_handler(MessageHandler(
            filters.Regex(rf'^{re.escape("!")}{cmd_name}(\s|$)'), handler_func
        ))

    application.add_handler(ChatMemberHandler(track_new_member, ChatMemberHandler.CHAT_MEMBER))
    
    # This listener runs in a very early group to catch spam before other modules.
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, check_for_spam), group=4)
