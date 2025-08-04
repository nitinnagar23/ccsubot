from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from typing import List, Tuple


def paginate_modules(
    page: int,
    modules: List[Tuple[str, str]],
    prefix: str,
    module_name: str = "module",
    per_page: int = 5
) -> InlineKeyboardMarkup:
    max_pages = (len(modules) + per_page - 1) // per_page
    page = max(0, min(page, max_pages - 1))

    start = page * per_page
    end = start + per_page
    module_slice = modules[start:end]

    buttons = [
        [
            InlineKeyboardButton(
                text=name,
                callback_data=f"{prefix}_module({key})"
            )
        ]
        for key, name in module_slice
    ]

    navigation = []
    if page > 0:
        navigation.append(InlineKeyboardButton("⏪ Prev", callback_data=f"{prefix}_prev({page - 1})"))
    if page < max_pages - 1:
        navigation.append(InlineKeyboardButton("Next ⏩", callback_data=f"{prefix}_next({page + 1})"))

    if navigation:
        buttons.append(navigation)

    return InlineKeyboardMarkup(buttons)
