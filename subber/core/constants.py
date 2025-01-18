"""
Constants used throughout the subber package.
"""

from typing import Set, Dict

# File extensions
VIDEO_EXTENSIONS: Set[str] = {".mkv", ".mov", ".mp4"}
SUBTITLE_EXTENSIONS: Set[str] = {".srt"}

# Matching configuration
DEFAULT_MIN_SIMILARITY: float = 0.3
DATE_SIMILARITY_BOOST: float = 0.3

# Logging configuration
LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"

# Rich console styling
CONSOLE_STYLES: Dict[str, str] = {
    "success": "green",
    "error": "red",
    "warning": "yellow",
    "info": "cyan",
    "dim": "dim"
} 