import re
import random
from telegram import Update, Message, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode

from database.db import db

# --- The Message Formatting Pipeline ---

def select_random(text: str) -> str:
    """If text contains '%%%', splits it and returns one random part."""
    if "%%%" in text:
        parts = [part.strip() for part in text.split("%%%")]
        return random.choice(parts) if parts else ""
    return text

def apply_fillings(text: str, update: Update):
    """Replaces all {fillings} with their corresponding values."""
    user = update.effective_user
    chat = update.effective_chat
    
    # User-based fillings
    if user:
        text = text.replace("{first}", user.first_name)
        text = text.replace("{last}", user.last_name or "")
        text = text.replace("{fullname}", user.full_name)
        text = text.replace("{username}", f"@{user.username}" if user.username else user.mention_html())
        text = text.replace("{mention}", user.mention_html())
        text = text.replace("{id}", str(user.id))
    
    # Chat-based fillings
    if chat:
        text = text.replace("{chatname}", chat.title)

    # Special {rules} filling - converts to a button
    if "{rules}" in text:
        chat_settings = db.chat_settings.find_one({"_id": chat.id}) or {}
        button_text = chat_settings.get("rules_button_text", "Read The Rules")
        
        # We convert the filling into markdown for a button that links to a special #rules note
        text = text.replace("{rules:same}", f"[{button_text}](buttonurl://#rules:same)")
        text = text.replace("{rules}", f"[{button_text}](buttonurl://#rules)")
        
    return text

def parse_buttons(text: str) -> tuple[str, InlineKeyboardMarkup | None]:
    """
    Parses [Button](buttonurl://...) syntax and returns the cleaned text
    and an InlineKeyboardMarkup.
    """
    buttons = []
    # Regex to find [text](buttonurl://url)
    matches = list(re.finditer(r"\[(.+?)\]\(buttonurl:\/\/(.+?)\)", text))
    
    clean_text = re.sub(r"\[(.+?)\]\(buttonurl:\/\/(.+?)\)\n?", "", text).strip()
    
    if not matches:
        return text, None # Return original text if no buttons

    row = []
    for match in matches:
        button_text = match.group(1)
        button_url = match.group(2)

        is_same_line = False
        if button_url.endswith(':same'):
            is_same_line = True
            button_url = button_url[:-5]

        if button_url.startswith("#"):
            note_trigger = button_url[1:]
            row.append(InlineKeyboardButton(button_text, callback_data=f"note:open:{note_trigger}"))
        else:
            row.append(InlineKeyboardButton(button_text, url=button_url))
        
        if not is_same_line:
            buttons.append(row)
            row = []
    
    if row:
        buttons.append(row)
        
    return clean_text, InlineKeyboardMarkup(buttons) if buttons else None

def extract_send_options(text: str) -> dict:
    """
    Parses special {fillings} to determine send options like notifications
    and content protection.
    """
    options = {}
    if "{nonotif}" in text:
        options['disable_notification'] = True
    if "{protect}" in text:
        options['protect_content'] = True
    # TODO: Add {preview} and {mediaspoiler} support here
    
    return options
