import sys

from loguru import logger


def setup_logger():
    """Setup logger."""
    logger.remove()
    logger.add(sys.stderr, level="CRITICAL")
