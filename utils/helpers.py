from pyrogram.enums import ChatType
from pyrogram.types import ChatMember
from config import OWNER_ID


def get_user_from_message(message):
    if message.reply_to_message:
        return message.reply_to_message.from_user
    if message.entities:
        for entity in message.entities:
            if entity.type.name == "text_mention":
                return entity.user
    return None


def is_group(chat_type: ChatType) -> bool:
    return chat_type in [ChatType.GROUP, ChatType.SUPERGROUP]


def format_time(seconds: int) -> str:
    mins, sec = divmod(seconds, 60)
    hour, mins = divmod(mins, 60)
    day, hour = divmod(hour, 24)

    time_parts = []
    if day > 0:
        time_parts.append(f"{day}d")
    if hour > 0:
        time_parts.append(f"{hour}h")
    if mins > 0:
        time_parts.append(f"{mins}m")
    if sec > 0 or not time_parts:
        time_parts.append(f"{sec}s")

    return " ".join(time_parts)


def is_owner(user_id: int) -> bool:
    return user_id in OWNER_ID


def is_admin(member: ChatMember) -> bool:
    return member.status in ["administrator", "creator"]
