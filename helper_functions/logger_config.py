"""Create Logging config."""

import logging
from pathlib import Path

logging.getLogger("httpx").setLevel(logging.WARNING)  # Ignore httpx logging in terminal
logger = logging.getLogger("ScoreboardLogger")

# Remove all existing handlers
if logger.hasHandlers():
    logger.handlers.clear()

# Set up our custom stream handler
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(message)s"))
logger.addHandler(handler)

# Add a file handler for errors with timestamps
log_dir = Path.cwd() / "logs"
log_dir.mkdir(parents=True, exist_ok=True)
error_handler = logging.FileHandler(log_dir / "error.log")
error_handler.setLevel(logging.ERROR)
error_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
logger.addHandler(error_handler)

logger.setLevel(logging.INFO)
logger.propagate = False
