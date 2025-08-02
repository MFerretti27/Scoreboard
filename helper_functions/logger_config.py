"""Create Logging config."""

import logging

logging.getLogger("httpx").setLevel(logging.WARNING)  # Ignore httpx logging in terminal
logger = logging.getLogger("ScoreboardLogger")

# Remove all existing handlers
if logger.hasHandlers():
    logger.handlers.clear()

# Set up our custom stream handler
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(message)s"))
logger.addHandler(handler)

logger.setLevel(logging.INFO)
logger.propagate = False
