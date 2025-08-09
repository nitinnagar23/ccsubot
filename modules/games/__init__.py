import re
from telegram.ext import CommandHandler, MessageHandler, filters, PollAnswerHandler

from .quiz import start_quiz, stop_quiz, handle_quiz_answer #, quiz_top
from bot_core.registry import COMMAND_REGISTRY, HELP_REGISTRY

def load_module(application):
    """Loads all game-related handlers and commands."""
    
    # --- Register Quiz Commands ---
    quiz_cmds = {
        "quiz": "Start a random quiz.",
        "stopquiz": "Admin-only: Stop the ongoing quiz.",
        "quiztop": "Show all-time top quiz players.",
        "quizscore": "View the current quiz round's leaderboard.",
    }
    for cmd, help_text in quiz_cmds.items():
        category = "admin" if cmd == "stopquiz" else "user"
        COMMAND_REGISTRY[cmd] = {"module": "Games", "category": category, "help": help_text}

    HELP_REGISTRY["Games"] = quiz_cmds
    
    handlers = {
        "quiz": start_quiz,
        "stopquiz": stop_quiz,
        # "quiztop": quiz_top,
    }
    
    for cmd_name, handler_func in handlers.items():
        application.add_handler(CommandHandler(cmd_name, handler_func))
        application.add_handler(MessageHandler(
            filters.Regex(rf'^{re.escape("!")}{cmd_name}(\s|$)'),
            handler_func
        ))
    
    # Add the PollAnswerHandler to listen for quiz answers
    application.add_handler(PollAnswerHandler(handle_quiz_answer))
