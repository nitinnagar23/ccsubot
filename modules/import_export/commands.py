import json
import io
from telegram import Update
from telegram.ext import ContextTypes, CallbackQueryHandler, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode

from database.db import db
from utils.decorators import admin_only, creator_only
from utils.context import resolve_target_chat_id
from utils.permissions import is_user_creator

# --- Mapping of modules to their data locations ---
# NOTE: We only handle settings and content, not user-specific runtime data (like warnings, xp).
MODULE_MAP = {
    'antiflood': {'settings_prefix': 'flood_'},
    'approval': {'settings_prefix': 'approved_users'},
    'blocklists': {'collection': db["blocklist_triggers"]},
    'captcha': {'settings_prefix': 'captcha_'},
    'clean_command': {'settings_prefix': 'clean_command_'},
    'clean_service': {'settings_prefix': 'clean_service_'},
    'disabled': {'settings_prefix': ('disabled_commands', 'disable_admin', 'disable_delete')},
    'filters': {'collection': db["filters"]},
    'greetings': {'settings_prefix': ('welcome_', 'goodbye_', 'clean_welcome_')},
    'locks': {'collection': db["locks"], 'settings_prefix': 'lock_'},
    'notes': {'collection': db["notes"]},
    'raids': {'settings_prefix': 'raid_'},
    'reports': {'settings_prefix': 'reports_'},
    'rules': {'settings_prefix': 'rules_'},
    'warns': {'settings_prefix': 'warn_'},
}

# --- Commands ---
@admin_only
async def export_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Exports chat settings to a JSON file."""
    chat_id = await resolve_target_chat_id(update, context)
    chat = await context.bot.get_chat(chat_id)
    
    categories_to_export = context.args or MODULE_MAP.keys()
    export_data = {}
    
    # 1. Export relevant chat_settings
    chat_settings_doc = db.chat_settings.find_one({"_id": chat_id}) or {}
    settings_to_export = {}
    for cat in categories_to_export:
        mod_info = MODULE_MAP.get(cat)
        if mod_info and 'settings_prefix' in mod_info:
            prefixes = mod_info['settings_prefix']
            if not isinstance(prefixes, tuple): prefixes = (prefixes,)
            for key, value in chat_settings_doc.items():
                if any(key.startswith(p) for p in prefixes): settings_to_export[key] = value
    if settings_to_export: export_data['chat_settings'] = settings_to_export

    # 2. Export data from collections
    for cat in categories_to_export:
        mod_info = MODULE_MAP.get(cat)
        if mod_info and 'collection' in mod_info:
            data = list(mod_info['collection'].find({"chat_id": chat_id}, {"_id": 0, "chat_id": 0}))
            if data: export_data[cat] = data

    if not export_data:
        await update.message.reply_text("No settings found to export for the selected categories.")
        return

    # 3. Send the file
    json_str = json.dumps(export_data, indent=2, default=str) # Use default=str for datetimes
    json_bytes = io.BytesIO(json_str.encode('utf-8'))
    file_name = f"bot_settings_{chat.id}.json"
    
    await update.message.reply_document(document=json_bytes, filename=file_name)

@creator_only
async def import_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Imports chat settings from a replied-to JSON file."""
    chat_id = await resolve_target_chat_id(update, context)
    
    if not update.message.reply_to_message or not update.message.reply_to_message.document:
        await update.message.reply_text("Please reply to an exported `.json` settings file.")
        return
        
    doc = update.message.reply_to_message.document
    if not doc.file_name.endswith('.json'): return
        
    file_bytes = await (await doc.get_file()).download_as_bytearray()
    try: import_data = json.loads(file_bytes.decode('utf-8'))
    except json.JSONDecodeError:
        await update.message.reply_text("This is not a valid JSON file.")
        return

    categories_to_import = context.args or import_data.keys()
    imported_cats = []

    # Import chat_settings
    if 'chat_settings' in import_data and ('chat_settings' in categories_to_import or not context.args):
        db.chat_settings.update_one({"_id": chat_id}, {"$set": import_data['chat_settings']}, upsert=True)
        imported_cats.append("General Settings")
        
    # Import collection data
    for cat in categories_to_import:
        if cat in import_data and 'collection' in MODULE_MAP.get(cat, {}):
            collection = MODULE_MAP[cat]['collection']
            data = import_data[cat]
            if isinstance(data, list):
                collection.delete_many({"chat_id": chat_id}) # Clean slate
                for item in data: item['chat_id'] = chat_id
                if data: collection.insert_many(data)
                imported_cats.append(cat.capitalize())

    await update.message.reply_text(f"✅ Imported settings for: {', '.join(imported_cats)}.")

@creator_only
async def reset_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Asks for confirmation to reset all chat settings."""
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("⚠️ Yes, delete ALL settings", callback_data="reset:confirm"),
        InlineKeyboardButton("Cancel", callback_data="reset:cancel")]])
    await update.message.reply_text(
        "Are you sure you want to reset ALL bot settings? This removes all notes, filters, blocklists, etc. This is irreversible.",
        reply_markup=keyboard)
    
async def reset_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    chat_id = query.message.chat.id
    if not await is_user_creator(context, chat_id, query.from_user.id):
        await query.answer("Only the chat creator can do this.", show_alert=True)
        return

    if query.data.endswith("confirm"):
        db.chat_settings.delete_one({"_id": chat_id})
        for mod in MODULE_MAP.values():
            if mod.get('collection'):
                mod['collection'].delete_many({"chat_id": chat_id})
        await query.edit_message_text("✅ All bot settings for this chat have been wiped.")
    else:
        await query.edit_message_text("Action cancelled.")
