"""
Logging configuration for the subber package.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from subber.core.constants import LOG_FORMAT, LOG_DATE_FORMAT, LOGS_DIR

def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[Path] = None
) -> None:
    """
    Configure logging for the package.
    
    Args:
        log_level: The logging level to use (default: INFO)
        log_file: Optional path to write logs to (default: None, will create timestamped file in LOGS_DIR)
    """
    # Convert string log level to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create logs directory if it doesn't exist
    LOGS_DIR.mkdir(exist_ok=True)
    
    # If no log file specified, create a timestamped one in LOGS_DIR
    if log_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = LOGS_DIR / f"subber_{timestamp}.log"
    
    # Basic configuration
    logging.basicConfig(
        level=numeric_level,
        format=LOG_FORMAT,
        datefmt=LOG_DATE_FORMAT,
        handlers=[
            logging.StreamHandler(sys.stderr),
            logging.FileHandler(log_file)
        ]
    )
    
    # Create logger for the package
    logger = logging.getLogger("subber")
    logger.setLevel(numeric_level)
    
    logger.debug("Logging configured with level %s", log_level)
    logger.debug("Logging to file: %s", log_file) 