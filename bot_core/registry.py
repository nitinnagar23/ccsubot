# A central place to store information about loaded modules and commands.

# This is the primary, detailed registry for the bot's internal logic.
# It's used by modules like Disabling, Clean Commands, and the advanced Help system.
COMMAND_REGISTRY = {}
# The structure will be:
# {
#   "command_name": {
#     "module": "ModuleName",
#     "category": "admin" or "user" or "owner",
#     "help": "Description for the command."
#   }
# }

# This is a simpler registry, primarily for backward compatibility or simpler
# help menu implementations. We will populate both for maximum flexibility.
HELP_REGISTRY = {}
# The structure will be:
# {
#   "ModuleName": {
#     "command1": "Description for command 1.",
#     "command2": "Description for command 2."
#   }
#}
