import re
from telegram.ext import CommandHandler, MessageHandler, filters, ChatMemberHandler

from .commands import toggle_misban, handle_member_removal #, other_commands...
from bot_core.registry import COMMAND_REGISTRY, HELP_REGISTRY

def load_module(application):
    """Loads the Misban (Anti-Betrayal) module."""
    admin_cmds = {
        "misban": "Turn on/off the Anti-Betrayal mode.",
        "misbannotify": "Toggle in-chat notifications for misban actions.",
        "misbanmode": "Set the action (ban/kick) against rogue admins.",
        "misbanconfig": "View the current Anti-Betrayal configuration.",
    }
    for cmd, help_text in admin_cmds.items():
        COMMAND_REGISTRY[cmd] = {"module": "Misban", "category": "admin", "help": help_text}
    HELP_REGISTRY["Misban"] = admin_cmds

    handlers = {"misban": toggle_misban} # Add other config handlers here
    for cmd_name, handler_func in handlers.items():
        application.add_handler(CommandHandler(cmd_name, handler_func))
        application.add_handler(MessageHandler(
            filters.Regex(rf'^{re.escape("!")}{cmd_name}(\s|$)'),
            handler_func
        ))

    # Add the core listener for chat member updates
    application.add_handler(ChatMemberHandler(handle_member_removal, ChatMemberHandler.CHAT_MEMBER))
