import logging
import sys
from pathlib import Path
from config.config import LOGS_DIR

def get_logger(name: str = "CorporateActionImpact") -> logging.Logger:
    """Configures and returns a centralized, thread-safe logger."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        # Formatter
        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        # Stream Handler (Console)
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

        # File Handler (logs/app.log)
        log_file = LOGS_DIR / "app.log"
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger
