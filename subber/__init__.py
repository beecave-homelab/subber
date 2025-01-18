"""
Subber - A tool for matching video files with subtitle files.
"""

__version__ = "0.1.0"
__author__ = "elvee"
__description__ = "A tool for matching video files with subtitle files"

from subber.core.matcher import collect_files, find_matches
from subber.utils.display import show_ascii_art, display_results
from subber.utils.file_ops import rename_close_matches, move_unmatched_files

__all__ = [
    'collect_files',
    'find_matches',
    'show_ascii_art',
    'display_results',
    'rename_close_matches',
    'move_unmatched_files',
]
