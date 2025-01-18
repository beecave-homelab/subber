"""
Utility functions for converting video files to MP3 format using ffmpeg.
"""

import subprocess
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
import questionary
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..core.constants import CONSOLE_STYLES

# Initialize Rich console and logger
console = Console()
logger = logging.getLogger(__name__)

def _format_path(path: Path) -> Dict[str, Any]:
    """Helper to format path for logging with extra parameters."""
    return {
        'path': str(path),
        'basename': path.name,
        'path_type': 'file' if path.is_file() else 'directory'
    }

def check_ffmpeg_installed() -> bool:
    """Check if ffmpeg is installed on the system."""
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        return False

def convert_to_mp3(video_file: Path, output_dir: Path) -> bool:
    """
    Convert a video file to MP3 format using ffmpeg.
    
    Args:
        video_file: Path to the video file
        output_dir: Directory for the output MP3 file
    
    Returns:
        bool: True if conversion was successful, False otherwise
    """
    try:
        output_path = output_dir / f"{video_file.stem}.mp3"
        
        if output_path.exists():
            logger.debug("Output file already exists, skipping conversion", 
                        extra={'output_file': str(output_path)})
            return False

        logger.debug("Converting video to MP3", 
                    extra={'input_file': str(video_file), 'output_file': str(output_path)})
        
        result = subprocess.run([
            'ffmpeg',
            '-i', str(video_file),
            '-q:a', '0',  # Use variable bit rate with highest quality
            '-map', 'a',  # Extract only audio
            '-y',  # Overwrite output file if it exists
            str(output_path)
        ], check=True, capture_output=True, text=True)
        
        # Log ffmpeg output only in debug mode
        if result.stderr:
            logger.debug("ffmpeg output", extra={'ffmpeg_output': result.stderr})
        
        logger.debug("Successfully converted video to MP3",
                    extra={'input_file': str(video_file), 'output_file': str(output_path)})
        return True
    
    except subprocess.SubprocessError as e:
        logger.error("Error converting video to MP3",
                    extra={'input_file': str(video_file), 'error': str(e)})
        # Log detailed error output in debug mode
        if hasattr(e, 'stderr') and e.stderr:
            logger.debug("ffmpeg error output", extra={'ffmpeg_error': e.stderr})
        return False

def batch_convert_to_mp3(video_files: List[Path], output_dir: Path) -> int:
    """
    Convert a batch of video files to MP3 format.
    
    Args:
        video_files: List of video files to convert
        output_dir: Directory to save the converted files
        
    Returns:
        int: Number of successfully converted files
    """
    if not video_files:
        logger.debug("No files to convert")
        return 0
        
    # Create output directory if it doesn't exist
    output_dir.mkdir(exist_ok=True)
    logger.debug("Created/verified output directory", 
                extra=_format_path(output_dir))

    # Build choices for questionary
    choices = []
    # Add "Select All" option at the top
    choices.append({
        "name": "Select All",
        "value": "ALL",
        "checked": False
    })
    
    # Add file choices
    file_choices = []
    for video_file in video_files:
        output_path = output_dir / f"{video_file.stem}.mp3"
        if output_path.exists():
            logger.debug("Output file already exists, skipping", 
                        extra={'output_file': str(output_path)})
            continue
        file_choices.append({"name": video_file.name, "value": video_file})

    if not file_choices:
        logger.debug("No files available for conversion")
        console.print(Panel(
            "No files available for conversion.",
            border_style=CONSOLE_STYLES["warning"],
            title="Status",
            title_align="left"
        ))
        return 0

    choices.extend(file_choices)
    logger.debug("Found files available for conversion", 
                extra={'file_count': len(file_choices)})

    try:
        selected = questionary.checkbox(
            "Select which video files to convert to MP3:",
            choices=choices
        ).ask()
        
        if not selected:
            logger.debug("No files selected for conversion")
            return 0
            
        # Handle "Select All" option
        if "ALL" in selected:
            selected = [choice["value"] for choice in file_choices]
            logger.debug("Selected all files for conversion", 
                        extra={'file_count': len(selected)})
            
        # Convert files with progress bar
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("[blue]Converting files...[/blue]", total=len(selected))
            converted_count = 0
            
            for video_file in selected:
                if convert_to_mp3(video_file, output_dir):
                    converted_count += 1
                progress.advance(task)
            
            logger.debug("Conversion complete", 
                        extra={'converted_count': converted_count, 'total_files': len(selected)})
            return converted_count
            
    except (KeyboardInterrupt, EOFError):
        logger.debug("Conversion cancelled by user")
        console.print("\nOperation cancelled by user.", style="yellow")
        return 0 