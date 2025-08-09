import re
from telegram.ext import CommandHandler, MessageHandler, filters, ChatMemberHandler, CallbackQueryHandler

from .commands import toggle_captcha, handle_new_member, handle_captcha_callback
from bot_core.registry import COMMAND_REGISTRY, HELP_REGISTRY

def load_module(application):
    """Loads the CAPTCHA module."""
    admin_cmds = {
        "captcha": "Enable or disable CAPTCHA for new members.",
        "captchamode": "Set the CAPTCHA type (button/math).",
        "captchakick": "Toggle kicking users who don't solve the CAPTCHA.",
        "captchakicktime": "Set the time after which to kick the user.",
        # ... other config commands
    }
    for cmd, help_text in admin_cmds.items():
        COMMAND_REGISTRY[cmd] = {"module": "Captcha", "category": "admin", "help": help_text}
    HELP_REGISTRY["Captcha"] = admin_cmds
    
    handlers = {"captcha": toggle_captcha} # Add other config handlers here
    for cmd_name, handler_func in handlers.items():
        application.add_handler(CommandHandler(cmd_name, handler_func))
        application.add_handler(MessageHandler(
            filters.Regex(rf'^{re.escape("!")}{cmd_name}(\s|$)'), handler_func
        ))
    
    # Add the core handlers
    application.add_handler(ChatMemberHandler(handle_new_member, ChatMemberHandler.CHAT_MEMBER))
    application.add_handler(CallbackQueryHandler(handle_captcha_callback, pattern="^captcha:"))
