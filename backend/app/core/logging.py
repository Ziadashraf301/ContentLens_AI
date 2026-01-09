import logging
from logging.handlers import RotatingFileHandler
from app.core.config import settings

# Logger Formatter
formatter = logging.Formatter(
    fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# Console Handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)

# File Handler (Rotating)
# Prevents logs from growing forever
# Keeps 3 backups, 5MB each
file_handler = RotatingFileHandler(
    filename="logs/app.log",
    maxBytes=5 * 1024 * 1024,
    backupCount=3,
)
file_handler.setFormatter(formatter)

# Logger Setup
logger = logging.getLogger(settings.APP_NAME)
logger.setLevel(settings.LOG_LEVEL.upper())
logger.addHandler(console_handler)
logger.addHandler(file_handler)

logger.propagate = False  # Prevent double logging if root logger is used
