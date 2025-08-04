# bot/modules/help_menu.py

from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from bot.utils.pagination import paginate_help
from bot.modules import __all__ as loaded_modules

HELP_MODULES = {
    mod.__name__.split('.')[-1]: mod.__doc__ or "No description available."
    for mod in loaded_modules
}


@Client.on_message(filters.command(["help", "!help"]))
async def help_command(client: Client, message: Message):
    if message.chat.type != "private":
        return await message.reply("Please use /help in private chat for detailed help.")

    page = 0
    text, markup = paginate_help(page, HELP_MODULES)
    await message.reply(text, reply_markup=markup, disable_web_page_preview=True)


@Client.on_callback_query(filters.regex(r"^help_module\((.+)\)$"))
async def show_module_help(client: Client, callback_query: CallbackQuery):
    module_name = callback_query.data.split("(", 1)[1].rstrip(")")
    description = HELP_MODULES.get(module_name, "No help found for this module.")

    await callback_query.message.edit_text(
        f"📚 **Help for `{module_name}`**\n\n{description}",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("« Back", callback_data="help_home(0)")]
        ]),
    )


@Client.on_callback_query(filters.regex(r"^help_home\((\d+)\)$"))
async def show_help_page(client: Client, callback_query: CallbackQuery):
    page = int(callback_query.data.split("(", 1)[1].rstrip(")"))
    text, markup = paginate_help(page, HELP_MODULES)
    await callback_query.message.edit_text(text, reply_markup=markup, disable_web_page_preview=True)
