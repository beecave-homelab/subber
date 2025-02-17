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

from subber.core.constants import CONSOLE_STYLES, AUDIO_CONVERSION, MESSAGES

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
            '-q:a', AUDIO_CONVERSION['FFMPEG_SETTINGS']['quality'],
            '-map', AUDIO_CONVERSION['FFMPEG_SETTINGS']['map'],
            '-y',  # Overwrite output file if it exists
            str(output_path)
        ]
        
        # Create FfmpegProcess instance with logging configuration
        ff = FfmpegProcess(
            cmd,
            ffmpeg_log_level=AUDIO_CONVERSION['FFMPEG_SETTINGS']['log_level'],
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
                # Clean up incomplete file on failure
                if output_path.exists():
                    output_path.unlink()
                    logger.debug(f"Cleaned up incomplete file: {output_path}")
                return False
            
        except KeyboardInterrupt:
            logger.debug("Conversion interrupted by user")
            ff.terminate()
            # Clean up incomplete file on interruption
            if output_path.exists():
                output_path.unlink()
                logger.debug(f"Cleaned up incomplete file: {output_path}")
            return False
    
    except Exception as e:
        logger.error(f"Failed to convert {video_file.name}", extra={'error': str(e)})
        # Clean up incomplete file on error
        if output_path.exists():
            output_path.unlink()
            logger.debug(f"Cleaned up incomplete file: {output_path}")
        return False

def batch_convert_to_mp3(video_files: List[Path], output_dir: Optional[Path] = None) -> int:
    """
    Convert a batch of video files to MP3 format.
    
    Args:
        video_files: List of video files to convert
        output_dir: Directory to save the converted files. If None, uses default from constants.
        
    Returns:
        int: Number of successfully converted files
    """
    if not video_files:
        logger.debug("No files to convert")
        return 0
    
    # Use default output directory if none provided
    if output_dir is None:
        output_dir = Path(AUDIO_CONVERSION['DEFAULT_OUTPUT_DIR'])
        
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
        files_to_convert = []
        if "ALL" in selected:
            files_to_convert = [choice["value"] for choice in file_choices]
            logger.debug("Selected all files for conversion", 
                        extra={'file_count': len(files_to_convert)})
        else:
            files_to_convert = selected
            logger.debug("Selected specific files for conversion", 
                        extra={'file_count': len(files_to_convert)})
            
        # Convert files one by one
        converted_count = 0
        total_files = len(files_to_convert)
        
        # Create header panel
        console.print(Panel(
            f"Converting {total_files} files",
            border_style=CONSOLE_STYLES["info"],
            title="Starting Conversion",
            title_align="left"
        ))
        
        for i, video_file in enumerate(files_to_convert, 1):
            # Create file header with counter
            header = Text()
            header.append(f"[{i}/{total_files}] ", style="bold blue")
            header.append("Converting ", style="bold")
            header.append(video_file.name, style="cyan")
            console.print(f"\n{header}")
            
            try:
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
                    # Continue with next file on error
                    continue
                    
            except KeyboardInterrupt:
                # Clean up the current file
                output_path = output_dir / f"{video_file.stem}.mp3"
                if output_path.exists():
                    output_path.unlink()
                    logger.debug(f"Cleaned up incomplete file: {output_path}")
                
                # Show cancellation message
                console.print(Panel(
                    Text.assemble(
                        (f"{MESSAGES['OPERATION_CANCELLED']}\n", "yellow"),
                        ("Converted ", "bold"),
                        (f"{converted_count}/{total_files}", "bold yellow"),
                        " files before cancellation"
                    ),
                    border_style="yellow",
                    title="Cancelled",
                    title_align="left"
                ))
                return converted_count
        
        # Print summary panel only if all files were processed
        logger.debug("Conversion complete", 
                    extra={'converted_count': converted_count, 'total_files': total_files})
        
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
        
    except KeyboardInterrupt:
        console.print(Panel(
            Text.assemble(
                (f"{MESSAGES['OPERATION_CANCELLED']}\n", "yellow"),
                ("No files were converted.", "dim")
            ),
            border_style="yellow",
            title="Cancelled",
            title_align="left"
        ))
        return 0 