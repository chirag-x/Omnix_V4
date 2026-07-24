# Omnix V4 module
from loguru import logger
import sys
import os


def setup_logger():
    os.makedirs("logs", exist_ok=True)

    logger.remove()

    logger.add(
        sys.stdout,
        level="INFO",
        format="<green>{time}</green> | <level>{level}</level> | {message}"
    )

    logger.add(
        "logs/omnix.log",
        rotation="5 MB",
        retention="10 days",
        level="DEBUG"
    )

    return logger