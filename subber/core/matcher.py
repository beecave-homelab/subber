"""
Core functionality for matching video files with subtitle files.
"""

import logging
import re
from pathlib import Path
from typing import List, Tuple, Set, Dict, Optional
from datetime import datetime

from .constants import (
    VIDEO_EXTENSIONS,
    SUBTITLE_EXTENSIONS,
    DEFAULT_MIN_SIMILARITY,
    DATE_SIMILARITY_BOOST
)

logger = logging.getLogger(__name__)

class MatcherError(Exception):
    """Base exception for matcher module."""
    pass

class InvalidPathError(MatcherError):
    """Raised when a path is invalid or inaccessible."""
    pass

def extract_date(filename: str) -> Optional[datetime]:
    """
    Extract a date from a filename using various common formats.
    
    Args:
        filename: The filename to extract date from
        
    Returns:
        Optional[datetime]: The extracted date or None if no date found
        
    Examples:
        >>> extract_date("video_2024-01-24_test.mp4")
        datetime(2024, 1, 24)
    """
    # Common separator pattern that matches dots, hyphens, and spaces
    sep = r'[\.\- ]+'
    
    # Pattern for YYYY-MM-DD format
    pattern_ymd = rf'(?:^|\D)(?P<year_ymd>[0-9]{{4}}){sep}(?P<month_ymd>[0-9]{{2}}){sep}(?P<day_ymd>[0-9]{{2}})(?:\D|$)'
    
    # Pattern for DD-MM-YYYY format
    pattern_dmy = rf'(?:^|\D)(?P<day_dmy>[0-9]{{2}}){sep}(?P<month_dmy>[0-9]{{2}}){sep}(?P<year_dmy>[0-9]{{4}})(?:\D|$)'
    
    # Pattern for YY-MM-DD format
    pattern_short_ymd = rf'(?:^|\D)(?P<year_short_ymd>[0-9]{{2}}){sep}(?P<month_short_ymd>[0-9]{{2}}){sep}(?P<day_short_ymd>[0-9]{{2}})(?:\D|$)'
    
    # Pattern for DD-MM-YY format
    pattern_short_dmy = rf'(?:^|\D)(?P<day_short_dmy>[0-9]{{2}}){sep}(?P<month_short_dmy>[0-9]{{2}}){sep}(?P<year_short_dmy>[0-9]{{2}})(?:\D|$)'
    
    # Compact formats without separators
    pattern_compact_ymd = r'(?:^|\D)(?P<year_compact>[0-9]{4})(?P<month_compact>[0-9]{2})(?P<day_compact>[0-9]{2})(?:\D|$)'
    pattern_compact_dmy = r'(?:^|\D)(?P<day_compact_dmy>[0-9]{2})(?P<month_compact_dmy>[0-9]{2})(?P<year_compact_dmy>[0-9]{4})(?:\D|$)'
    pattern_compact_short_dmy = r'(?:^|\D)(?P<day_compact_short>[0-9]{2})(?P<month_compact_short>[0-9]{2})(?P<year_compact_short>[0-9]{2})(?:\D|$)'
    
    # All patterns to try
    patterns = [
        pattern_ymd,                    # YYYY-MM-DD
        pattern_dmy,                    # DD-MM-YYYY
        pattern_short_ymd,              # YY-MM-DD
        pattern_short_dmy,              # DD-MM-YY
        pattern_compact_ymd,            # YYYYMMDD
        pattern_compact_dmy,            # DDMMYYYY
        pattern_compact_short_dmy,      # DDMMYY
        
        # Parentheses enclosed versions
        rf'\({pattern_ymd}\)',
        rf'\({pattern_dmy}\)',
        rf'\({pattern_short_ymd}\)',
        rf'\({pattern_short_dmy}\)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, filename)
        if match:
            try:
                groups = match.groupdict()
                
                # Find the matched group names (they'll end with the format type)
                year_key = next(k for k in groups.keys() if k.startswith('year_') and groups[k])
                month_key = next(k for k in groups.keys() if k.startswith('month_') and groups[k])
                day_key = next(k for k in groups.keys() if k.startswith('day_') and groups[k])
                
                year = groups[year_key]
                month = int(groups[month_key])
                day = int(groups[day_key])
                
                # Handle 2-digit years
                if len(year) == 2:
                    year = '20' + year if int(year) < 50 else '19' + year
                
                return datetime(int(year), month, day)
            except (ValueError, IndexError, StopIteration):
                continue
    
    return None

def normalize_filename(filename: Path) -> Set[str]:
    """
    Normalize a filename by splitting into words based on non-alphanumeric characters.
    
    Args:
        filename: Path object representing the file
        
    Returns:
        Set[str]: Set of normalized words from the filename
        
    Raises:
        InvalidPathError: If the path is invalid
    """
    try:
        base = filename.stem.lower()
        words = re.split(r'\W+', base)
        words = [word for word in words if word]  # remove empty strings
        return set(words)
    except Exception as e:
        raise InvalidPathError(f"Failed to normalize filename {filename}: {e}")

def collect_files(directory: Path) -> Tuple[List[Path], List[Path]]:
    """
    Recursively collect video and subtitle files from a directory.
    
    Args:
        directory: Path object representing the directory to search
        
    Returns:
        Tuple[List[Path], List[Path]]: Lists of video and subtitle files
        
    Raises:
        InvalidPathError: If the directory is invalid or inaccessible
    """
    if not directory.is_dir():
        raise InvalidPathError(f"Invalid directory path: {directory}")

    try:
        video_files = []
        subtitle_files = []

        for file_path in directory.rglob("*"):
            if file_path.name.startswith("._"):
                continue  # skip macOS resource fork files
            if file_path.suffix.lower() in VIDEO_EXTENSIONS:
                video_files.append(file_path)
            elif file_path.suffix.lower() in SUBTITLE_EXTENSIONS:
                subtitle_files.append(file_path)

        logger.info("Collected %d video files and %d subtitle files.",
                    len(video_files), len(subtitle_files))
        logger.debug("Video files: %s", video_files)
        logger.debug("Subtitle files: %s", subtitle_files)
        
        return video_files, subtitle_files
    except Exception as e:
        raise InvalidPathError(f"Error collecting files from {directory}: {e}")

def find_matches(
    video_files: List[Path],
    subtitle_files: List[Path],
    min_similarity: float = DEFAULT_MIN_SIMILARITY
) -> Tuple[List[Tuple[Path, Path]],
           List[Tuple[Path, Path, float]],
           List[Path]]:
    """
    Find matches between video and subtitle files.
    
    Args:
        video_files: List of video file paths
        subtitle_files: List of subtitle file paths
        min_similarity: Minimum similarity threshold (0-1)
        
    Returns:
        Tuple containing:
        - List of exact matches (same stem)
        - List of close matches with similarity scores
        - List of unmatched video files
        
    Raises:
        ValueError: If min_similarity is not between 0 and 1
        InvalidPathError: If any file paths are invalid
    """
    if not 0 <= min_similarity <= 1:
        raise ValueError("min_similarity must be between 0 and 1")

    logger.debug("Finding matches with min_similarity=%f", min_similarity)
    
    exact_matches = []
    close_matches = []
    unmatched_videos = []

    # Convert subtitles to a set to track what's left
    subtitles_left = set(subtitle_files)

    # 1. Exact matches
    for vf in video_files:
        try:
            vf_stem = vf.stem.lower()
            exact_sub = next((sf for sf in subtitle_files
                            if sf.stem.lower() == vf_stem), None)
            if exact_sub:
                exact_matches.append((vf, exact_sub))
                subtitles_left.discard(exact_sub)
                logger.debug("Found exact match: %s -> %s", vf, exact_sub)
            else:
                unmatched_videos.append(vf)
        except Exception as e:
            logger.warning("Error processing video file %s: %s", vf, e)
            continue

    # 2. Close matches
    try:
        unmatched_subtitles = list(subtitles_left)
        unmatched_subtitle_sets = {sf: normalize_filename(sf) for sf in unmatched_subtitles}
        unmatched_video_sets = {vf: normalize_filename(vf) for vf in unmatched_videos}

        remaining_videos = []
        for vf, v_set in unmatched_video_sets.items():
            best_match = None
            best_similarity = 0.0
            
            # Extract date from video filename
            video_date = extract_date(vf.stem)
            
            for sf, s_set in unmatched_subtitle_sets.items():
                # Calculate base similarity using Jaccard index
                intersection = v_set.intersection(s_set)
                union = v_set.union(s_set)
                similarity = len(intersection) / len(union) if union else 0.0
                
                # Check for matching dates and boost similarity
                if video_date:
                    sub_date = extract_date(sf.stem)
                    if sub_date and video_date == sub_date:
                        similarity = min(1.0, similarity + DATE_SIMILARITY_BOOST)
                
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = sf
                    
            if best_match and best_similarity >= min_similarity:
                close_matches.append((vf, best_match, best_similarity))
                subtitles_left.discard(best_match)
                del unmatched_subtitle_sets[best_match]
                logger.debug("Found close match: %s -> %s (similarity: %f)",
                           vf, best_match, best_similarity)
            else:
                remaining_videos.append(vf)
    except Exception as e:
        logger.error("Error during close matching: %s", e)
        remaining_videos = unmatched_videos

    logger.info("Found %d exact matches, %d close matches, %d unmatched videos",
                len(exact_matches), len(close_matches), len(remaining_videos))
    
    return exact_matches, close_matches, remaining_videos 