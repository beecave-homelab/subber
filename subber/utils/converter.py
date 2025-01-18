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
from rich.panel import Panel
from rich.text import Text
from better_ffmpeg_progress import FfmpegProcess

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
            logger.debug(f"Skipping {video_file.name} (already exists)")
            return False

        logger.debug(f"Starting conversion of {video_file.name}")
        
        # Prepare ffmpeg command
        cmd = [
            'ffmpeg',
            '-i', str(video_file),
            '-q:a', '0',  # Use variable bit rate with highest quality
            '-map', 'a',  # Extract only audio
            '-y',  # Overwrite output file if it exists
            str(output_path)
        ]
        
        # Create FfmpegProcess instance with logging configuration
        ff = FfmpegProcess(
            cmd,
            ffmpeg_log_level="error",  # Only show errors in ffmpeg output
            print_stderr_new_line=True  # Print errors on new lines
        )
        
        try:
            # Start the process and let better-ffmpeg-progress handle the display
            return_code = ff.run()
            
            if return_code == 0:
                logger.debug(f"Successfully converted {video_file.name}")
                return True
            else:
                logger.error(f"FFmpeg process failed with return code {return_code}")
                return False
            
        except KeyboardInterrupt:
            logger.debug("Conversion interrupted by user")
            ff.terminate()
            if output_path.exists():
                output_path.unlink()
            return False
    
    except Exception as e:
        logger.error(f"Failed to convert {video_file.name}", extra={'error': str(e)})
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
            
        # Convert files one by one
        converted_count = 0
        total_files = len(selected)
        
        # Create header panel
        console.print(Panel(
            f"Converting {total_files} files",
            border_style=CONSOLE_STYLES["info"],
            title="Starting Conversion",
            title_align="left"
        ))
        
        for i, video_file in enumerate(selected, 1):
            # Create file header with counter
            header = Text()
            header.append(f"[{i}/{total_files}] ", style="bold blue")
            header.append("Converting ", style="bold")
            header.append(video_file.name, style="cyan")
            console.print(f"\n{header}")
            
            if convert_to_mp3(video_file, output_dir):
                converted_count += 1
                # Success message
                msg = Text("✓ ", style="bold green")
                msg.append("Converted ", style="green")
                msg.append(video_file.name, style="cyan")
                console.print(msg)
            else:
                # Error message
                msg = Text("✗ ", style="bold red")
                msg.append("Failed to convert ", style="red")
                msg.append(video_file.name, style="cyan")
                console.print(msg)
        
        logger.debug("Conversion complete", 
                    extra={'converted_count': converted_count, 'total_files': total_files})
        
        # Print summary panel
        status_style = "green" if converted_count == total_files else "yellow"
        console.print(Panel(
            Text.assemble(
                ("Conversion complete: ", "bold"),
                (f"{converted_count}/{total_files}", f"bold {status_style}"),
                " files converted successfully"
            ),
            border_style=status_style,
            title="Summary",
            title_align="left"
        ))
        return converted_count
            
    except (KeyboardInterrupt, EOFError):
        logger.debug("Conversion cancelled by user")
        console.print(Panel(
            "Operation cancelled by user",
            border_style="yellow",
            title="Cancelled",
            title_align="left"
        ))
        return 0 