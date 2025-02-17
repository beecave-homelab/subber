"""
Constants used throughout the subber package.
"""

from pathlib import Path
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
LOGS_DIR: Path = Path(__file__).parent.parent.parent / "subber_logs"

# Rich console styling
CONSOLE_STYLES: Dict[str, str] = {
    "success": "green",
    "error": "red",
    "warning": "yellow",
    "info": "cyan",
    "dim": "dim",
}

# Display settings for panels
PANEL_SETTINGS = {
    "EXACT_MATCHES": {
        "title": "Exact Matches",
        "border_style": "green",
        "title_align": "left",
    },
    "CLOSE_MATCHES": {
        "title": "Close Matches",
        "border_style": "yellow",
        "title_align": "left",
    },
    "UNMATCHED_VIDEOS": {
        "title": "Unmatched Video Files",
        "border_style": "red",
        "title_align": "left",
    },
    "UNMATCHED_SUBTITLES": {
        "title": "Unmatched Subtitle Files",
        "border_style": "red",
        "title_align": "left",
    },
}

# Display settings for tables
TABLE_SETTINGS = {
    "EXACT_MATCHES": {
        "title": "Exact Matches",
        "border_style": "green",
        "header_style": "bold green",
    },
    "CLOSE_MATCHES": {
        "title": "Close Matches",
        "border_style": "yellow",
        "header_style": "bold yellow",
    },
    "UNMATCHED_VIDEOS": {
        "title": "Unmatched Video Files",
        "border_style": "red",
        "header_style": "bold red",
    },
    "UNMATCHED_SUBTITLES": {
        "title": "Unmatched Subtitle Files",
        "border_style": "red",
        "header_style": "bold red",
    },
}

# Audio conversion settings
AUDIO_CONVERSION = {
    "DEFAULT_OUTPUT_DIR": "audio_files",
    "FFMPEG_SETTINGS": {
        "quality": "0",  # Highest quality
        "log_level": "error",
        "map": "a",  # Extract only audio
    },
}

# Messages
MESSAGES = {
    "NO_EXACT_MATCHES": "No exact matches found.",
    "NO_CLOSE_MATCHES": "No close matches found.",
    "ALL_VIDEOS_MATCHED": "All video files have matching subtitles.",
    "ALL_SUBS_MATCHED": "All subtitle files have matching videos.",
    "OPERATION_CANCELLED": "Operation cancelled by user",
    "FFMPEG_NOT_INSTALLED": "Error: ffmpeg is not installed. Please install it to use the conversion feature.",
}

# Default log levels for third-party packages
THIRD_PARTY_LOG_LEVELS = {
    "questionary": "WARNING",
    "rich": "WARNING",
    "click": "WARNING",
}
