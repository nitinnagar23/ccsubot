import re
from telegram.ext import CommandHandler, MessageHandler, filters

from .commands import get_pinned, pin_message, perma_pin, unpin_message, handle_auto_unpin
from bot_core.registry import COMMAND_REGISTRY, HELP_REGISTRY

def load_module(application):
    """Loads the Pin module."""
    # User command
    COMMAND_REGISTRY["pinned"] = {"module": "Pin", "category": "user", "help": "Get the current pinned message."}
    
    # Admin commands
    admin_cmds = {
        "pin": "Pin the message you replied to. Add 'loud' to notify.",
        "permapin": "Pin a custom, formatted message via the bot.",
        "unpin": "Unpin the replied-to message or the latest pin.",
        "unpinall": "Unpins all messages in the chat.",
        "antichannelpin": "Toggle auto-unpinning of linked channel posts.",
        "cleanlinked": "Toggle auto-deletion of linked channel posts.",
    }
    for cmd, help_text in admin_cmds.items():
        COMMAND_REGISTRY[cmd] = {"module": "Pin", "category": "admin", "help": help_text}

    HELP_REGISTRY["Pin"] = {**{"pinned": COMMAND_REGISTRY["pinned"]["help"]}, **admin_cmds}
    
    handlers = {
        "pinned": get_pinned, "pin": pin_message,
        "permapin": perma_pin, "unpin": unpin_message
        # ... add handlers for other config commands here ...
    }

    for cmd_name, handler_func in handlers.items():
        application.add_handler(CommandHandler(cmd_name, handler_func))
        application.add_handler(MessageHandler(
            filters.Regex(rf'^{re.escape("!")}{cmd_name}(\s|$)'),
            handler_func
        ))

    # Add listeners for automated features
    application.add_handler(MessageHandler(filters.StatusUpdate.PINNED_MESSAGE, handle_auto_unpin))
    # handler for /cleanlinked would go here:
    # application.add_handler(MessageHandler(filters.SenderChat, handle_linked_channel_posts))
