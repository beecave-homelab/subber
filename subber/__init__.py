"""
Subber - A Python package for matching video files with subtitle files.

This package provides functionality to find and manage matches between video files
and their corresponding subtitle files in a media library.

Key Features:
    - Exact and fuzzy matching of video files with subtitle files
    - Date-based matching enhancement
    - Interactive subtitle file renaming
    - Support for moving unmatched files
    - Detailed logging and progress reporting

Basic Usage:
    >>> from subber import collect_files, find_matches
    >>> from pathlib import Path
    
    # Collect video and subtitle files
    >>> media_dir = Path("movies")
    >>> videos, subtitles = collect_files(media_dir)
    
    # Find matches
    >>> exact, close, unmatched_v, unmatched_s = find_matches(videos, subtitles)
    >>> print(f"Found {len(exact)} exact and {len(close)} close matches")

Advanced Usage:
    >>> from subber.utils.file_ops import rename_close_matches, move_unmatched_files
    
    # Rename close matches interactively
    >>> rename_close_matches(close_matches)
    
    # Move unmatched videos to a separate directory
    >>> move_unmatched_files(unmatched_v, "unmatched", media_dir)

Module Structure:
    - core/: Core matching functionality
        - matcher.py: Main matching algorithms
        - constants.py: Package constants and settings
        - types.py: Type definitions
    - utils/: Utility functions
        - file_ops.py: File operations (rename, move)
        - display.py: Output formatting
        - logging.py: Logging configuration
    - cli/: Command-line interface
        - main.py: CLI implementation

For more information, see the project documentation at:
https://github.com/beecave-homelab/subber
"""

from .core.matcher import collect_files, find_matches
from .core.types import VideoPath, SubtitlePath, ExactMatch, CloseMatch, MatchResult
from .utils.file_ops import rename_close_matches, move_unmatched_files
from .utils.display import display_results

__version__ = "0.2.0"
__author__ = "elvee"

__all__ = [
    # Core functionality
    "collect_files",
    "find_matches",
    
    # Type definitions
    "VideoPath",
    "SubtitlePath",
    "ExactMatch",
    "CloseMatch",
    "MatchResult",
    
    # Utility functions
    "rename_close_matches",
    "move_unmatched_files",
    "display_results",
]
