# --- Main Help Menu Introduction ---
HELP_BIO = """
Hello! I'm a modular group management bot, here to help you keep your chat safe and active.

If you have any bugs or questions, please ask in my support chat.
All commands can be used with the following prefixes: `!` or `/`
"""

# --- Detailed Help Text for Each Module ---
# This is the central repository for all detailed help messages.
# Use HTML for formatting (<b>, <code>, <i>, <a href="">).
MODULE_HELP_TEXTS = {
    "Admins": """
<b>👮 Admins</b>

This module manages the bot's internal list of trusted administrators. Users promoted via the bot are granted more trust by certain modules (like Misban).

<b>Admin commands:</b>
- <code>/promote &lt;user&gt;</code>: Promotes a user to a bot admin.
- <code>/demote &lt;user&gt;</code>: Demotes a user from being a bot admin.
- <code>/adminlist</code>: Lists all admins (Creator, TG Admins, Bot Admins).
- <code>/anonadmin &lt;on/off&gt;</code>: Toggles permissions for anonymous admins.
""",
    "AI": """
<b>🧠 AI</b>

This module integrates powerful generative AI features into your chat.

<b>User commands:</b>
- <code>/ask &lt;question&gt;</code>: Ask a question to the Gemini AI model. The bot will think for a moment and give you a detailed answer.

<b>Example:</b>
-> <code>/ask What are the most popular tourist attractions in Uttar Pradesh?</code>
""",
    "Antiflood": """
<b>🌊 Antiflood</b>

Antiflood protects your chat from users who send many messages in a short period. You can configure the message limit and the punishment.

<b>Admin commands:</b>
- <code>/flood</code>: Get the current antiflood settings.
- <code>/setflood &lt;number/off&gt;</code>: Set the number of messages to trigger antiflood.
- <code>/floodmode &lt;action&gt;</code>: Choose the action to take (ban/mute/kick/tban/tmute).
""",
    "AntiRaid": """
<b>🛡️ AntiRaid</b>

Protects your chat from "raids" where hundreds of users join at once to spam. When enabled, new users will be temporarily banned.

<b>Admin commands:</b>
- <code>/antiraid &lt;on/off/time&gt;</code>: Manually toggle raid mode.
- <code>/autoantiraid &lt;number/off&gt;</code>: Automatically enable raid mode if X users join within a minute.
- <code>/raidactiontime &lt;time&gt;</code>: Set the temp-ban duration for new joins during a raid.
""",
    "Approval": """
<b>👍 Approval</b>

The approval system is a whitelist for trusted users. Approved users are exempt from many restrictions, such as antiflood, locks, and blocklists, without being an admin.

<b>Admin commands:</b>
- <code>/approve &lt;user&gt;</code>: Approves a user.
- <code>/unapprove &lt;user&gt;</code>: Revokes a user's approval.
- <code>/approved</code>: Lists all approved users.
""",
    "Bans": """
<b>🔨 Bans</b>

This module contains the essential tools for moderating users. Most commands can be used by replying to a user or by providing their ID/username.

<b>Admin commands:</b>
- <code>/ban &lt;user&gt; [reason]</code>: Ban a user.
- <code>/tban &lt;user&gt; &lt;time&gt; [reason]</code>: Temporarily ban a user.
- <code>/unban &lt;user&gt;</code>: Unban a user.
- <code>/mute &lt;user&gt; [reason]</code>: Mute a user.
- <code>/tmute &lt;user&gt; &lt;time&gt; [reason]</code>: Temporarily mute a user.
- <code>/unmute &lt;user&gt;</code>: Unmute a user.
- <code>/kick &lt;user&gt; [reason]</code>: Kick a user (they can rejoin).
<i>Note: Use 'd' prefix to delete the user's message (e.g., /dban) or 's' prefix to perform the action silently (e.g., /sban).</i>
""",
    "CAPTCHA": """
<b>🤖 CAPTCHA</b>

Protects your group from user-bots by requiring new members to solve a challenge before they can speak.

<b>Note:</b> This system works best with welcome messages enabled.

<b>Admin commands:</b>
- <code>/captcha &lt;on/off&gt;</code>: Enable or disable the CAPTCHA system.
- <code>/captchamode &lt;button/math&gt;</code>: Choose the type of challenge.
- <code>/captchakicktime &lt;time&gt;</code>: Set how long a user has to solve the CAPTCHA before being kicked.
""",
    "Connections": """
<b>🔌 Connections</b>

Manage your groups remotely! This feature allows you to issue commands to another group from a private message with the bot.

<b>Admin commands (PM only):</b>
- <code>/connect &lt;chat_id&gt;</code>: Connect to a chat where you are an admin.
- <code>/disconnect</code>: Disconnect from the chat.
- <code>/connection</code>: See which chat you are currently connected to.
""",
    "Filters": """
<b>💬 Filters</b>

Make the bot automatically reply to certain words or phrases. Filters are a powerful way to create custom commands and interactive content.

<b>Admin commands:</b>
- <code>/filter &lt;trigger&gt; &lt;reply&gt;</code>: Sets a filter. Quote multi-word triggers (e.g., /filter "hi there" Hello!).
- <code>/stop &lt;trigger&gt;</code>: Stops a filter.
- <code>/filters</code>: Lists all active filters.

<i>This feature supports advanced formatting, media, random replies, and fillings. Use the /markdownhelp command for more info.</i>
""",
    "Greetings": """
<b>👋 Greetings</b>

Set custom welcome and goodbye messages for your chat. These messages fully support the bot's advanced formatting, including buttons, fillings, and random content.

<b>Admin commands:</b>
- <code>/welcome &lt;on/off&gt;</code>: Toggle welcome messages.
- <code>/setwelcome &lt;message&gt;</code>: Set the welcome message.
- <code>/goodbye &lt;on/off&gt;</code>: Toggle goodbye messages.
- <code>/setgoodbye &lt;message&gt;</code>: Set the goodbye message.
- <code>/cleanwelcome &lt;on/off&gt;</code>: Auto-delete old welcome messages.
""",
    "Notes": """
<b>📝 Notes</b>

Save and retrieve information, media, or reminders. Notes can be fetched with /get or by typing #notename.

<b>Admin commands:</b>
- <code>/save &lt;notename&gt; &lt;content&gt;</code>: Save a note. Reply to media to save it.
- <code>/clear &lt;notename&gt;</code>: Clear a note.
- <code>/notes</code>: List all saved notes.

<b>Advanced Usage:</b>
- <b>Repeating Note:</b> Add <code>{repeat 6h}</code> to a note's content to make it repeat every 6 hours.
- <b>Private Note:</b> Add <code>{private}</code> to send a note to the user's PM.
""",
    "Warnings": """
<b>⚠️ Warnings</b>

A progressive discipline system. Warn users for infractions; if they reach the warn limit, a pre-configured punishment is automatically applied.

<b>Admin commands:</b>
- <code>/warn &lt;user&gt; [reason]</code>: Issue a warning.
- <code>/warns &lt;user&gt;</code>: See a user's warning history.
- <code>/rmwarn &lt;user&gt;</code>: Remove a user's most recent warning.
- <code>/warnlimit &lt;number&gt;</code>: Set the number of warnings before punishment.
- <code>/warnmode &lt;action&gt;</code>: Set the punishment (ban/mute/kick/etc.).
- <code>/warntime &lt;time&gt;</code>: Set how long warnings last before expiring.
""",
    # Add more modules here as you see fit...
}
