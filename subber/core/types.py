"""
Type definitions for the matcher module.
"""

from typing import List, Tuple, Set, Dict, Union, TypeVar, NewType
from pathlib import Path
from os import PathLike

# Type aliases for paths
FilePath = Union[str, PathLike, Path]
VideoPath = NewType("VideoPath", Path)
SubtitlePath = NewType("SubtitlePath", Path)

# Type aliases for matching results
ExactMatch = Tuple[VideoPath, SubtitlePath]
CloseMatch = Tuple[VideoPath, SubtitlePath, float]
MatchResult = Tuple[
    List[ExactMatch], List[CloseMatch], List[VideoPath], List[SubtitlePath]
]

# Type alias for normalized filename words
NormalizedWords = Set[str]

# Type alias for filename mapping
FileMapping = Dict[Path, NormalizedWords]

# Generic type for file collections
T = TypeVar("T", VideoPath, SubtitlePath)
FileCollection = List[T]
