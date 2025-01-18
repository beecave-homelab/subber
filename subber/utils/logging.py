"""
Logging configuration for the subber package.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

from ..core.constants import LOG_FORMAT, LOG_DATE_FORMAT

def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[Path] = None
) -> None:
    """
    Configure logging for the package.
    
    Args:
        log_level: The logging level to use (default: INFO)
        log_file: Optional path to write logs to (default: None, logs to stderr only)
    """
    # Convert string log level to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Basic configuration
    logging.basicConfig(
        level=numeric_level,
        format=LOG_FORMAT,
        datefmt=LOG_DATE_FORMAT,
        handlers=[
            logging.StreamHandler(sys.stderr),
            *([] if log_file is None else [logging.FileHandler(log_file)])
        ]
    )
    
    # Create logger for the package
    logger = logging.getLogger("subber")
    logger.setLevel(numeric_level)
    
    logger.debug("Logging configured with level %s", log_level)
    if log_file:
        logger.debug("Logging to file: %s", log_file) 