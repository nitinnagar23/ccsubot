import re
from telegram.ext import CommandHandler, MessageHandler, filters

from .commands import report_command, admin_mention_handler, toggle_reports
from bot_core.registry import COMMAND_REGISTRY, HELP_REGISTRY

def load_module(application):
    """Loads the Reports module."""
    # Register commands
    COMMAND_REGISTRY["report"] = {"module": "Reports", "category": "user", "help": "Reply to a message to report it to admins."}
    COMMAND_REGISTRY["reports"] = {"module": "Reports", "category": "admin", "help": "Enable or disable the user reporting system."}
    
    help_text = {
        "/report or @admin": "Reply to a message to report it to admins.",
        "/reports": "Enable or disable user reports.",
    }
    HELP_REGISTRY["Reports"] = help_text

    # Command handlers
    application.add_handler(CommandHandler("report", report_command))
    application.add_handler(MessageHandler(filters.Regex(r'^!report(\s|$)'), report_command))
    application.add_handler(CommandHandler("reports", toggle_reports))
    application.add_handler(MessageHandler(filters.Regex(r'^!reports(\s|$)'), toggle_reports))

    # Message handler for @admin mentions. It must be a reply.
    application.add_handler(MessageHandler(
        filters.TEXT & (~filters.COMMAND) & filters.REPLY, 
        admin_mention_handler
    ), group=8)
