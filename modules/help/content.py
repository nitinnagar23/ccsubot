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

This module manages the bot's internal list of trusted administrators. Users promoted via the bot are granted more trust by certain security modules (like Misban).

<b>Admin commands:</b>
- <code>/promote &lt;user&gt;</code>: Promotes a user to a bot admin.
- <code>/demote &lt;user&gt;</code>: Demotes a user from being a bot admin.
- <code>/adminlist</code>: Lists all admins (Creator, Telegram Admins, and Bot Admins).
- <code>/anonadmin &lt;on/off&gt;</code>: Toggles whether anonymous admins can use bot commands.
""",
    "AI": """
<b>🧠 AI</b>

This module integrates powerful generative AI features into your chat, powered by Google's Gemini model.

<b>User commands:</b>
- <code>/ask &lt;question&gt;</code>: Ask a question to the AI. The bot will think for a moment and give you a detailed answer.

<b>Example:</b>
- Get a recipe for a local dish:
  -> <code>/ask What is the recipe for butter chicken?</code>
""",
    "Antiflood": """
<b>🌊 Antiflood</b>

Protects your chat from users who send many messages in a short period. You can configure the message limit and the punishment.

<b>Admin commands:</b>
- <code>/flood</code>: Get the current antiflood settings.
- <code>/setflood &lt;number/off&gt;</code>: Set the number of consecutive messages to trigger antiflood.
- <code>/floodmode &lt;action&gt;</code>: Choose the action to take (ban/mute/kick/tban/tmute).
- <code>/clearflood &lt;on/off&gt;</code>: Whether to delete the messages that triggered the flood.
""",
    "AntiRaid": """
<b>🛡️ AntiRaid</b>

Protects your chat from "raids" where many users join at once to spam. When enabled, new users will be temporarily banned.

<b>Admin commands:</b>
- <code>/antiraid &lt;on/off/time&gt;</code>: Manually toggle raid mode. Eg: <code>/antiraid 2h</code>
- <code>/autoantiraid &lt;number/off&gt;</code>: Automatically enable raid mode if X users join within a minute.
- <code>/raidactiontime &lt;time&gt;</code>: Set the temp-ban duration for new joins during a raid.
""",
    "Approval": """
<b>👍 Approval</b>

The approval system is a whitelist for trusted, non-admin users. Approved users are exempt from many restrictions, such as antiflood and locks.

<b>User commands:</b>
- <code>/approval &lt;user&gt;</code>: Check a user's approval status.

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

<i>Note: Use 'd' prefix to delete the user's message (e.g., <code>/dban</code>) or 's' prefix to perform the action silently (e.g., <code>/sban</code>).</i>
""",
    "Blocklist": """
<b>🚫 Blocklist</b>

A powerful content filter that allows you to block messages containing specific words, phrases, or patterns.

<b>Admin commands:</b>
- <code>/addblocklist &lt;trigger&gt; [reason]</code>: Add a trigger to the blocklist.
- <code>/rmblocklist &lt;trigger&gt;</code>: Remove a trigger.
- <code>/blocklist</code>: List all blocklisted items.
- <code>/blocklistmode &lt;action&gt;</code>: Set the default action for blocklisted messages (warn/ban/mute/etc).

<b>Examples:</b>
- Block a whole sentence:
  -> <code>/addblocklist "no advertising here"</code>
- Block links to a specific site:
  -> <code>/addblocklist "somebadsite.com/*"</code>
- Set a custom punishment for a single word:
  -> <code>/addblocklist badword ### This is a warning {warn}</code>
""",
    "Bot Status": """
<b>🛰️ Bot Status</b>

This is an automatic, background module with no commands. It keeps track of all the chats the bot is a part of to ensure that features like <b>/broadcast</b> work correctly.
""",
    "CAPTCHA": """
<b>🤖 CAPTCHA</b>

Protects your group from user-bots by requiring new members to solve a challenge before they can speak.

<b>Admin commands:</b>
- <code>/captcha &lt;on/off&gt;</code>: Enable or disable the CAPTCHA system.
- <code>/captchamode &lt;button/math&gt;</code>: Choose the type of challenge.
- <code>/captchakicktime &lt;time&gt;</code>: Set how long a user has to solve the CAPTCHA before being kicked.
""",
    "Clean Commands": """
<b>🧹 Clean Commands</b>

Keeps your chat tidy by automatically deleting command messages after they are used.

<b>Admin commands:</b>
- <code>/cleancommand &lt;type&gt;</code>: Start cleaning a command type.
- <code>/keepcommand &lt;type&gt;</code>: Stop cleaning a command type.
- <code>/cleancommandtypes</code>: List available types (all, admin, user, other).

<b>Example:</b>
- Delete commands used by regular users and commands for other bots:
  -> <code>/cleancommand user other</code>
""",
    "Clean Service": """
<b>🗑️ Clean Service</b>

Automatically deletes those small, grey Telegram system messages (e.g., "User joined the group").

<b>Admin commands:</b>
- <code>/cleanservice &lt;type&gt;</code>: Start cleaning a service message type.
- <code>/keepservice &lt;type&gt;</code>: Stop cleaning a type.
- <code>/cleanservicetypes</code>: List available types (all, join, leave, pin, etc.).

<b>Example:</b>
- Delete the "user joined" and "user left" messages:
  -> <code>/cleanservice join leave</code>
""",
    "Cleaning Bot Messages": """
<b>✨ Cleaning Bot Messages</b>

Allows the bot to clean up its own responses after a 5-minute delay to reduce clutter.

<b>Admin commands:</b>
- <code>/cleanmsg &lt;type&gt;</code>: Enable cleanup for a message type.
- <code>/keepmsg &lt;type&gt;</code>: Disable cleanup.
- <code>/cleanmsgtypes</code>: List available types (action, filter, note).

<b>Example:</b>
- Automatically delete the bot's replies to filters and notes:
  -> <code>/cleanmsg filter note</code>
""",
    "Connections": """
<b>🔌 Connections</b>

Manage your groups remotely! This feature allows you to issue commands to another group from a private message with the bot.

<b>Admin commands (must be used in PM with the bot):</b>
- <code>/connect &lt;chat_id&gt;</code>: Connect to a chat where you are an admin.
- <code>/disconnect</code>: Disconnect from the chat.
- <code>/connection</code>: See which chat you are currently connected to.
""",
    "Disabling": """
<b>🔌 Disabling</b>

Allows you to disable specific user-facing commands in your chat to prevent abuse or spam.

<b>Admin commands:</b>
- <code>/disable &lt;command&gt;</code>: Disable a command for non-admins.
- <code>/enable &lt;command&gt;</code>: Re-enable a command.
- <code>/disableable</code>: List all commands that can be disabled.
- <code>/disableadmin &lt;on/off&gt;</code>: Make disabled commands apply to admins too.
- <code>/disabledel &lt;on/off&gt;</code>: Delete disabled commands when they are used.
""",
    "Echo": """
<b>🗣️ Echo</b>

Allows administrators to speak through the bot, or for the bot owner to broadcast a message to all chats.

<b>Admin commands:</b>
- <code>/echo &lt;message&gt;</code>: The bot deletes your command and repeats your message. Preserves formatting.

<b>Bot Owner commands:</b>
- <code>/broadcast &lt;message&gt;</code>: Sends a message to every single group the bot is in.
""",
    "Federations": """
<b>🌐 Federations</b>

Federations are a network of chats that share a single, unified ban list. Banning a user in one federated chat can ban them from all.

<b>Owner/Admin commands:</b>
- <code>/newfed &lt;name&gt;</code>: Create a new federation.
- <code>/joinfed &lt;fed_id&gt;</code>: Join your chat to a federation.
- <code>/fban &lt;user&gt; [reason]</code>: Ban a user from every chat in the federation.
- <code>/unfban &lt;user&gt;</code>: Unban a user from the federation.
- <code>/fedinfo</code>: Get information about the current chat's federation.
""",
    "Filters": """
<b>💬 Filters</b>

Make the bot automatically reply to certain words or phrases. Filters are a powerful way to create custom commands and interactive content.

<b>Admin commands:</b>
- <code>/filter &lt;trigger&gt; &lt;reply&gt;</code>: Sets a filter. Quote multi-word triggers.
- <code>/stop &lt;trigger&gt;</code>: Stops a filter.
- <code>/filters</code>: Lists all active filters.

<b>Example:</b>
- Create a custom command with a button:
  -> <code>/filter /website Our website is amazing! [Click Here](buttonurl://example.com) {command}</code>
""",
    "Force Subscribe": """
<b>🔒 Force Subscribe</b>

Requires users to be a member of a specific channel before they are allowed to speak in the group.

<b>Note:</b> The bot must be an admin in both the group and the required channel(s).

<b>Admin commands:</b>
- <code>/forcesubadd &lt;@channel&gt;</code>: Add a channel to the required list.
- <code>/forcesubdel &lt;@channel&gt;</code>: Remove a channel from the list.
- <code>/forcesubstatus</code>: View the current configuration.
""",
    "Formatting": """
<b>🎨 Formatting</b>

This module provides information on how to format your messages with markdown, buttons, and dynamic fillings.

<b>User commands:</b>
- <code>/markdownhelp</code>: Get the full formatting guide. It's best to use this in a private message with the bot.
""",
    "Gamification": """
<b>🎮 Gamification</b>

Adds a fun XP and Level system to your chat, rewarding users for their activity.

<b>User commands:</b>
- <code>/rank</code>: Check your (or another user's) current level and XP.
- <code>/leaderboard</code>: See the top-ranked users in the chat.

<b>Admin commands:</b>
- <code>/xp &lt;on/off&gt;</code>: Enable or disable the XP system.
- <code>/setxp &lt;user&gt; &lt;amount&gt;</code>: Manually set a user's XP.
""",
    "Games": """
<b>🎲 Games</b>

Engage your community with fun, interactive games.

<b>User commands:</b>
- <code>/quiz</code>: Start an interactive trivia quiz.
- <code>/quiztop</code>: Show the all-time top quiz players for the chat.

<b>Admin commands:</b>
- <code>/stopquiz</code>: Stop the currently running quiz.
<i>More games and features will be added here!</i>
""",
    "Greetings": """
<b>👋 Greetings</b>

Set custom welcome and goodbye messages for your chat. These messages fully support the bot's advanced formatting, including buttons, fillings, and random content.

<b>Admin commands:</b>
- <code>/welcome &lt;on/off&gt;</code>: Toggle welcome messages.
- <code>/setwelcome &lt;message&gt;</code>: Set the welcome message.
- <code>/goodbye &lt;on/off&gt;</code>: Toggle goodbye messages.
- <code>/cleanwelcome &lt;on/off&gt;</code>: Auto-delete old welcome messages.
""",
    "Import/Export": """
<b>📦 Import/Export</b>

Allows you to save a complete snapshot of your bot's configuration for a chat and then instantly apply it to new chats, saving a huge amount of setup time.

<b>Admin commands:</b>
- <code>/export [modules]</code>: Export settings to a JSON file.

<b>Chat Creator commands:</b>
- <code>/import [modules]</code>: Reply to an exported file to import its settings.
- <code>/reset</code>: Wipes all bot settings for the chat (use with caution!).
""",
    "Locks": """
<b>🔗 Locks</b>

Allows you to restrict certain types of content (e.g., stickers, links, photos) to admins only.

<b>Admin commands:</b>
- <code>/lock &lt;type&gt;</code>: Lock a content type.
- <code>/unlock &lt;type&gt;</code>: Unlock a content type.
- <code>/locks</code>: View the list of current locks.
- <code>/locktypes</code>: See all lockable items.

<b>Example:</b>
- Stop anyone but admins from sending stickers and GIFs:
  -> <code>/lock sticker animation</code>
""",
    "Log Channels": """
<b>📜 Log Channels</b>

Create a permanent, private audit trail of all administrative and bot actions.

<b>Setup:</b>
1. Add the bot to your log channel as an admin.
2. Send <code>/setlog</code> in the channel.
3. Forward that message to the group you want to log.

<b>Admin commands:</b>
- <code>/unsetlog</code>: Unlink the log channel.
- <code>/log &lt;category&gt;</code>: Enable logging for a category.
- <code>/nolog &lt;category&gt;</code>: Disable logging for a category.
- <code>/logcategories</code>: List all available log categories.
""",
    "Misban": """
<b>🛡️ Misban</b>

The "Anti-Betrayal" module. Protects your chat from rogue admins who were promoted via Telegram but not via the bot's <code>/promote</code> command.

<b>Note:</b> This module requires you to manage your trusted admins with <code>/promote</code>.

<b>Admin commands:</b>
- <code>/misban &lt;on/off&gt;</code>: Enable or disable the Anti-Betrayal system.
- <code>/misbanmode &lt;ban/kick&gt;</code>: Set the action to take against a rogue admin who removes a user.
""",
    "Misc": """
<b>🧩 Misc</b>

A collection of small, useful, and fun "odds and ends" commands.

<b>User commands:</b>
- <code>/id</code>: Get the ID of a user or chat.
- <code>/info &lt;user&gt;</code>: Get detailed information about a user.
- <code>/runs</code>: Sends a random "runs away" message.
- <code>/donate</code>: Get information on how to support the bot.
- <code>/limits</code>: Show some of the bot's operational limits.
""",
    "Night Mode": """
<b>🌙 Night Mode</b>

Automatically restricts certain types of content during a specified time window to keep the chat quiet.

<b>Admin commands:</b>
- <code>/nightmode &lt;start_HH:MM&gt; &lt;end_HH:MM&gt;</code>: Set the schedule.
- <code>/nightmode &lt;on/off&gt;</code>: Manually override the schedule.
- <code>/settimezone &lt;TZ&gt;</code>: Set your chat's timezone (e.g., <code>Asia/Kolkata</code>). This is essential for the schedule to work correctly.
- <code>/nightmodestatus</code>: Check the current status.
""",
    "Notes": """
<b>📝 Notes</b>

Save and retrieve information, media, or reminders. Notes can be fetched with <code>/get</code> or by typing <code>#notename</code>.

<b>Admin commands:</b>
- <code>/save &lt;notename&gt; &lt;content&gt;</code>: Save a note. Reply to media to save it.
- <code>/clear &lt;notename&gt;</code>: Clear a note.
- <code>/notes</code>: List all saved notes.

<b>Example (Repeating Note):</b>
- Add <code>{repeat 6h}</code> to a note's content to make it repeat every 6 hours.
""",
    "Pin": """
<b>📌 Pin</b>

Tools for managing pinned messages in your chat.

<b>User commands:</b>
- <code>/pinned</code>: Get the currently pinned message.

<b>Admin commands:</b>
- <code>/pin</code>: Reply to a message to pin it. Add 'loud' to notify users.
- <code>/permapin &lt;text&gt;</code>: Send and pin a new message via the bot. Supports full formatting.
- <code>/unpin</code>: Unpin the latest message.
- <code>/antichannelpin &lt;on/off&gt;</code>: Automatically unpin messages from your linked channel.
""",
    "Purges": """
<b>🔥 Purges</b>

Tools for bulk-deleting messages. Use with care!

<b>Note:</b> The bot can typically only delete messages less than 48 hours old.

<b>Admin commands:</b>
- <code>/del</code>: Deletes the replied-to message.
- <code>/purge</code>: Reply to a message to delete it and all messages sent after it, up to your command.
- <code>/purgefrom</code> & <code>/purgeto</code>: A two-step command to delete a specific range of messages.
""",
    "Reports": """
<b>📢 Reports</b>

Allows your community members to help with moderation by reporting messages to admins.

<b>User commands:</b>
- Reply to a message with <code>/report</code> or <code>@admin</code> to notify all chat admins.

<b>Note:</b> Users cannot report admins, and admins cannot use the report command.

<b>Admin commands:</b>
- <code>/reports &lt;on/off&gt;</code>: Enable or disable the reporting system.
""",
    "Rules": """
<b>📜 Rules</b>

Set and display the rules for your chat. The rules can be a rich, formatted message with buttons and other interactive elements.

<b>User commands:</b>
- <code>/rules</code>: View the chat rules.

<b>Admin commands:</b>
- <code>/setrules &lt;text&gt;</code>: Set the rules.
- <code>/privaterules &lt;on/off&gt;</code>: Toggle whether rules are sent in the user's PM.
- <code>/setrulesbutton &lt;text&gt;</code>: Set the text for the <code>{rules}</code> button used in other messages.
""",
    "Spam": """
<b>🛡️ Spam</b>

A non-AI, highly efficient spam protection system based on a "new user quarantine".

<b>How it works:</b> New members are temporarily restricted from sending media, links, or forwards for a configurable period, stopping most spam bots instantly.

<b>Admin commands:</b>
- <code>/spamguard &lt;on/off&gt;</code>: Toggle the spam protection system.
- <code>/setquarantine &lt;time&gt;</code>: Set the duration of the new user quarantine (e.g., <code>24h</code>).
""",
    "Start": """
<b>🚀 Start</b>

The main command for interacting with the bot in a private message.

<b>User commands:</b>
- <code>/start</code>: In PM, this command shows a welcome message with helpful buttons to get you started, add the bot to a group, or get help.
""",
    "Topics": """
<b>📂 Topics</b>

Tools for managing chats that have Topics (Forums) enabled.

<b>Note:</b> These commands only work in a forum-style group and require the bot to have "Manage Topics" permission.

<b>Admin commands:</b>
- <code>/setactiontopic</code>: Sets the current topic as the default for automated messages like welcomes.
- <code>/newtopic &lt;name&gt;</code>: Create a new topic.
- <code>/closetopic</code>: Close the current topic.
- <code>/renametopic &lt;new name&gt;</code>: Rename the current topic.
""",
    "Warnings": """
<b>⚠️ Warnings</b>

A progressive discipline system. Warn users for infractions; if they reach the warn limit, a pre-configured punishment is automatically applied.

<b>Admin commands:</b>
- <code>/warn &lt;user&gt; [reason]</code>: Issue a warning.
- <code>/warns &lt;user&gt;</code>: See a user's warning history.
- <code>/warnlimit &lt;number&gt;</code>: Set the number of warnings before punishment.
- <code>/warnmode &lt;action&gt;</code>: Set the punishment (ban/mute/kick/etc.).
- <code>/warntime &lt;time&gt;</code>: Set how long warnings last before expiring.
""",
}
