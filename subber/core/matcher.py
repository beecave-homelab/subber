"""
Core functionality for matching video files with subtitle files.

This module provides functions for finding matches between video files and their corresponding
subtitle files based on filename similarity and embedded dates.

Example:
    >>> from pathlib import Path
    >>> video_dir = Path("movies")
    >>> videos, subs = collect_files(video_dir)
    >>> exact, close, unmatched_v, unmatched_s = find_matches(videos, subs)
    >>> print(f"Found {len(exact)} exact matches and {len(close)} close matches")
"""

import logging
import re
from pathlib import Path
from typing import List, Tuple, Set, Dict, Optional, cast
from datetime import datetime

from subber.core.constants import (
    VIDEO_EXTENSIONS,
    SUBTITLE_EXTENSIONS,
    DEFAULT_MIN_SIMILARITY,
    DATE_SIMILARITY_BOOST
)
from subber.core.types import (
    FilePath, VideoPath, SubtitlePath,
    ExactMatch, CloseMatch, MatchResult,
    NormalizedWords, FileMapping, FileCollection
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
    
    This function attempts to find and parse dates in filenames using multiple
    common formats including YYYY-MM-DD, DD-MM-YYYY, and their variations.
    
    Args:
        filename: The filename to extract date from
        
    Returns:
        Optional[datetime]: The extracted date or None if no date found
        
    Examples:
        >>> extract_date("video_2024-01-24_test.mp4")
        datetime(2024, 1, 24)
        >>> extract_date("Movie (24.01.2024).mkv")
        datetime(2024, 1, 24)
        >>> extract_date("no_date_here.mp4")
        None
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

def normalize_filename(filename: FilePath) -> NormalizedWords:
    """
    Normalize a filename by splitting into words based on non-alphanumeric characters.
    
    This function converts the filename to lowercase and splits it into individual
    words, removing common separators and empty strings.
    
    Args:
        filename: Path-like object representing the file
        
    Returns:
        Set[str]: Set of normalized words from the filename
        
    Raises:
        InvalidPathError: If the path is invalid
        
    Examples:
        >>> normalize_filename(Path("The.Big.Movie-2024.mp4"))
        {'the', 'big', 'movie', '2024'}
        >>> normalize_filename("My_Cool-Video_01.mkv")
        {'my', 'cool', 'video', '01'}
    """
    try:
        path = Path(filename)
        base = path.stem.lower()
        words = re.split(r'\W+', base)
        words = [word for word in words if word]  # remove empty strings
        return set(words)
    except Exception as e:
        raise InvalidPathError(f"Failed to normalize filename {filename}: {e}")

def collect_files(directory: FilePath) -> tuple[FileCollection[VideoPath], FileCollection[SubtitlePath]]:
    """
    Recursively collect video and subtitle files from a directory.
    
    This function walks through the directory tree and identifies video and subtitle
    files based on their extensions. It skips macOS resource fork files.
    
    Args:
        directory: Path-like object representing the directory to search
        
    Returns:
        tuple[List[VideoPath], List[SubtitlePath]]: Lists of video and subtitle files
        
    Raises:
        InvalidPathError: If the directory is invalid or inaccessible
        
    Examples:
        >>> videos, subs = collect_files("movies/")
        >>> print(f"Found {len(videos)} videos and {len(subs)} subtitles")
        Found 5 videos and 3 subtitles
    """
    dir_path = Path(directory)
    if not dir_path.is_dir():
        raise InvalidPathError(f"Invalid directory path: {dir_path}")

    try:
        video_files: list[VideoPath] = []
        subtitle_files: list[SubtitlePath] = []

        for file_path in dir_path.rglob("*"):
            if file_path.name.startswith("._"):
                continue  # skip macOS resource fork files
            if file_path.suffix.lower() in VIDEO_EXTENSIONS:
                video_files.append(cast(VideoPath, file_path))
            elif file_path.suffix.lower() in SUBTITLE_EXTENSIONS:
                subtitle_files.append(cast(SubtitlePath, file_path))

        logger.info("Collected %d video files and %d subtitle files.",
                    len(video_files), len(subtitle_files))
        logger.debug("Video files: %s", video_files)
        logger.debug("Subtitle files: %s", subtitle_files)
        
        return video_files, subtitle_files
    except Exception as e:
        raise InvalidPathError(f"Error collecting files from {dir_path}: {e}")

def find_matches(
    video_files: FileCollection[VideoPath],
    subtitle_files: FileCollection[SubtitlePath],
    min_similarity: float = DEFAULT_MIN_SIMILARITY
) -> MatchResult:
    """
    Find matches between video files and subtitle files.

    This function performs a two-step matching process:
    1. First, it looks for exact matches where filenames (without extensions) are identical
    2. Then, for remaining files, it looks for close matches using:
       - Word similarity (Jaccard index)
       - Date matching (with similarity boost for matching dates)

    Args:
        video_files: List of video file paths
        subtitle_files: List of subtitle file paths
        min_similarity: Minimum similarity threshold for close matches (0-1)

    Returns:
        MatchResult: A tuple containing:
            - List of exact matches (video_file, subtitle_file)
            - List of close matches with similarity scores
            - List of unmatched video files
            - List of unmatched subtitle files
        
    Raises:
        ValueError: If min_similarity is not between 0 and 1
        InvalidPathError: If any file paths are invalid
        
    Examples:
        >>> videos = [Path("movie1.mp4"), Path("show2.mkv")]
        >>> subs = [Path("movie1.srt"), Path("show2_eng.srt")]
        >>> exact, close, unmatched_v, unmatched_s = find_matches(videos, subs)
        >>> print(f"Exact matches: {len(exact)}")
        Exact matches: 1
    """
    if not 0 <= min_similarity <= 1:
        raise ValueError("min_similarity must be between 0 and 1")

    logger.debug("Finding matches with min_similarity=%f", min_similarity)
    
    # Initialize result collections with proper types
    exact_matches: list[ExactMatch] = []
    close_matches: list[CloseMatch] = []
    unmatched_videos: list[VideoPath] = []
    subtitles_left: set[SubtitlePath] = set(subtitle_files)

    # Phase 1: Find exact matches by comparing lowercase filenames
    for video_file in video_files:
        try:
            video_stem = video_file.stem.lower()
            # Find first subtitle with matching stem (case-insensitive)
            exact_subtitle = next(
                (subtitle_file for subtitle_file in subtitle_files
                 if subtitle_file.stem.lower() == video_stem),
                None
            )
            
            if exact_subtitle:
                # Add to exact matches and remove from available subtitles
                exact_matches.append((video_file, exact_subtitle))
                subtitles_left.discard(exact_subtitle)
                logger.debug("Found exact match: `%s` -> `%s`",
                           str(video_file), str(exact_subtitle))
            else:
                unmatched_videos.append(video_file)
        except Exception as e:
            logger.warning("Error processing video file `%s`: %s",
                         str(video_file), e)
            continue

    # Phase 2: Find close matches using word similarity and date matching
    try:
        # Convert remaining files to sets of normalized words
        unmatched_subtitles = list(subtitles_left)
        unmatched_subtitle_sets: FileMapping = {
            subtitle_file: normalize_filename(subtitle_file)
            for subtitle_file in unmatched_subtitles
        }
        unmatched_video_sets: FileMapping = {
            video_file: normalize_filename(video_file)
            for video_file in unmatched_videos
        }

        # Process each unmatched video file
        remaining_videos: list[VideoPath] = []
        for video_file, video_set in unmatched_video_sets.items():
            best_match: Optional[SubtitlePath] = None
            best_similarity = 0.0
            
            # Extract date from video filename for potential matching
            video_date = extract_date(video_file.stem)
            
            # Compare with each remaining subtitle
            for subtitle_file, subtitle_set in unmatched_subtitle_sets.items():
                # Calculate base similarity using Jaccard index
                # similarity = |A ∩ B| / |A ∪ B|
                intersection = video_set.intersection(subtitle_set)
                union = video_set.union(subtitle_set)
                similarity = len(intersection) / len(union) if union else 0.0
                
                # Apply date matching boost if dates are present and match
                if video_date:
                    subtitle_date = extract_date(subtitle_file.stem)
                    if subtitle_date and video_date == subtitle_date:
                        # Boost similarity but cap at 1.0
                        similarity = min(1.0, similarity + DATE_SIMILARITY_BOOST)
                
                # Update best match if this is the highest similarity so far
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = subtitle_file
            
            # If we found a good enough match, add it to results
            if best_match and best_similarity >= min_similarity:
                close_matches.append((
                    cast(VideoPath, video_file),
                    cast(SubtitlePath, best_match),
                    best_similarity
                ))
                subtitles_left.discard(best_match)
                del unmatched_subtitle_sets[best_match]
                logger.debug(
                    "Found close match: `%s` -> `%s` (similarity: %f)",
                    str(video_file), str(best_match), best_similarity
                )
            else:
                remaining_videos.append(cast(VideoPath, video_file))

        return (
            exact_matches,
            close_matches,
            remaining_videos,
            list(subtitles_left)
        )

    except Exception as e:
        logger.error("Error during close matching: %s", e)
        raise MatcherError(f"Failed to complete matching process: {e}") 