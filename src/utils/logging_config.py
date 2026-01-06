import sys
from loguru import logger


def setup_logging():
    """Configures loguru once for the entire project."""
    # Clear existing handlers to avoid duplicate logs
    logger.remove()

    # Add Console Handler (readable)
    logger.add(
        sys.stderr,
        level="INFO",
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    )

    # Add File Handler (For debugging long running jobs)
    logger.add(
        "logs/buglens.log",
        rotation="10 MB",
        retention="10 days",
        compression="zip",
        level="DEBUG",  # Store more detail in files than on screen
    )

    logger.info("Logging initialized successfully.")
