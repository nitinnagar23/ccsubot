import logging
import sys

# Create logger
logger = logging.getLogger("BotLogger")
logger.setLevel(logging.DEBUG)

# Formatter
formatter = logging.Formatter(
    "[%(asctime)s] [%(levelname)s] [%(name)s] - %(message)s", "%Y-%m-%d %H:%M:%S"
)

# Console Handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(formatter)

# Add handlers
logger.addHandler(console_handler)
