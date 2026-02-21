"""Logging configuration and utilities."""

import logging
from app.config import LOG_LEVEL

def setup_logging():
    """Configure application logging."""
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

logger = setup_logging()
