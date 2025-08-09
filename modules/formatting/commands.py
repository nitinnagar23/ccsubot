from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from utils.decorators import check_disabled

# This help text is a summary of all formatting options.
# NOTE: Characters like '.', '!', '-', '{', '}' must be escaped with a '\' for MARKDOWN_V2.
HELP_TEXT = """
*Bot Formatting Help*

You can format your messages in notes, filters, and greetings\.

*Markdown*
`*bold words*` -> *bold words*
`_italic words_` -> _italic words_
`__underline__` -> __underline__
`~strike~` -> ~strike~
`||spoiler||` -> ||spoiler||
`[hyperlink](https://telegram.org)`

*Buttons*
`[My button](buttonurl://example.com)`
To place buttons on the same row, add `:same` to the URL of the second button\.
`[Btn1](buttonurl://site.com)`
`[Btn2](buttonurl://othersite.com:same)`

*Fillings*
Personalize messages with dynamic info:
`{first}` \- User's first name
`{fullname}` \- User's full name
`{id}` \- User's ID
`{chatname}` \- Chat's name
`{rules}` \- A button to the chat's rules

*Random Replies*
Separate replies with `%%%` on a new line to have the bot pick one at random\.
"""

@check_disabled
async def markdown_help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends the formatting help message, recommending a private chat."""
    if update.effective_chat.type != "private":
        # If in a group, send a button to avoid cluttering the chat.
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton(
                "📖 Open Formatting Help",
                url=f"https://t.me/{context.bot.username}?start=markdownhelp"
            )
        ]])
        await update.message.reply_text(
            "Formatting help is best viewed in a private chat. Please press the button below.", 
            reply_markup=keyboard
        )
        return
        
    # If already in a private chat, send the full help text.
    await update.message.reply_text(HELP_TEXT, parse_mode=ParseMode.MARKDOWN_V2)

