import logging
import os
import structlog
from app.core.config import settings
from datetime import datetime

def setup_logging():
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    
    # Shared processors before formatting
    shared_processors = [
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]
    
    # Configure structlog
    structlog.configure(
        processors=shared_processors + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    
    # Formatter for console: clean, colored output for development
    console_formatter = structlog.stdlib.ProcessorFormatter(
        processor=structlog.dev.ConsoleRenderer(colors=True),
        foreign_pre_chain=shared_processors,
    )
    console_handler.setFormatter(console_formatter)
    
    # File handler
    backend_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    log_dir = os.path.join(backend_root, "logs")
    os.makedirs(log_dir, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    log_file_path = os.path.join(log_dir, f"app_{today}.log")
    
    file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
    file_handler.setLevel(log_level)
    
    # Formatter for file: pure JSON lines for structured logging
    file_formatter = structlog.stdlib.ProcessorFormatter(
        processor=structlog.processors.JSONRenderer(),
        foreign_pre_chain=shared_processors,
    )
    file_handler.setFormatter(file_formatter)
    
    # Configure root logger with standard handlers
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove existing handlers to avoid duplication
    for h in list(root_logger.handlers):
        root_logger.removeHandler(h)
        
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
