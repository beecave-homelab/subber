"""
Command-line interface for the subber package.
"""

import logging
import click
from pathlib import Path
from rich.logging import RichHandler
from rich.console import Console
from rich import box
from rich.text import Text

from subber.core.matcher import collect_files, find_matches
from subber.utils.display import show_ascii_art, display_results
from subber.utils.file_ops import rename_close_matches, move_unmatched_files
from subber.utils.converter import batch_convert_to_mp3, check_ffmpeg_installed
from subber.utils.logging import setup_logging
from subber.core.constants import (
    LOGS_DIR, 
    AUDIO_CONVERSION, 
    MESSAGES, 
    THIRD_PARTY_LOG_LEVELS,
    CONSOLE_STYLES
)

# Initialize Rich console
console = Console()

class RichFileFormatter(logging.Formatter):
    """Custom formatter that handles extra parameters and formats them nicely."""
    
    def format(self, record):
        # Format the basic message
        message = super().format(record)
        
        # If there are extra parameters, format them nicely
        if hasattr(record, 'extra'):
            extras = []
            for key, value in record.extra.items():
                if key == 'path':
                    extras.append(f"path='{value}'")
                elif key == 'basename':
                    extras.append(f"file='{value}'")
                elif key == 'file_count':
                    extras.append(f"count={value}")
                elif key == 'input_file':
                    extras.append(f"input='{value}'")
                elif key == 'output_file':
                    extras.append(f"output='{value}'")
                elif key == 'error':
                    extras.append(f"error='{value}'")
                elif key == 'ffmpeg_output':
                    # Format ffmpeg output on new lines
                    message += f"\n{value}"
                    continue
                elif key == 'ffmpeg_error':
                    # Format ffmpeg errors on new lines
                    message += f"\n{value}"
                    continue
                else:
                    extras.append(f"{key}={value}")
            
            if extras:
                message += f" ({', '.join(extras)})"
        
        return message

@click.command()
@click.option("-d", "--directory", default=".", show_default=True, help="Directory to search for files")
@click.option("-o", "--output-file", help="File path to save the output")
@click.option("-n", "--no-table", is_flag=True, help="Output results without table formatting")
@click.option("-p", "--path", is_flag=True, help="Show the full path of the files in the output")
@click.option("-m", "--move-unmatched", help="Folder to move unmatched video files into")
@click.option("-r", "--rename", is_flag=True, help="Interactively rename close-matched subtitle files to match video names")
@click.option("-c", "--convert", is_flag=False, flag_value=AUDIO_CONVERSION['DEFAULT_OUTPUT_DIR'], default=None, 
          help=f"Convert selected video files to MP3 format. Optionally specify output subdirectory (default: '{AUDIO_CONVERSION['DEFAULT_OUTPUT_DIR']}')")
@click.option("-v", "--verbose", is_flag=True, help="Enable verbose output with debug information")
@click.option("--log-file", type=click.Path(), help="Specify a custom log file path (default: timestamped file in subber_logs/)")
def main(directory, output_file, no_table, path, move_unmatched, rename, convert, verbose, log_file):
    """
    Find and match video files with their corresponding subtitle files.
    
    This tool recursively searches a directory for video files (.mkv, .mov, .mp4)
    and subtitle files (.srt), matches them based on filename similarity, and
    provides options for renaming and organizing the files.
    """
    # Configure logging
    log_level = "DEBUG" if verbose else "WARNING"
    log_file_path = Path(log_file) if log_file else None
    setup_logging(log_level=log_level, log_file=log_file_path)
    
    # Configure Rich handler
    rich_handler = RichHandler(
        rich_tracebacks=True,
        markup=True,
        show_time=True,
        show_level=True,
        show_path=False,
        level=logging.DEBUG if verbose else logging.WARNING,
        console=console,
        tracebacks_extra_lines=2,
        tracebacks_theme="monokai",
    )
    rich_handler.setFormatter(RichFileFormatter("%(message)s"))
    
    # Add Rich handler to root logger
    logging.getLogger().addHandler(rich_handler)
    
    # Silence other loggers unless in verbose mode
    if not verbose:
        for logger_name, level in THIRD_PARTY_LOG_LEVELS.items():
            logging.getLogger(logger_name).setLevel(getattr(logging, level))

    show_ascii_art()

    # Log the start of execution
    logger = logging.getLogger(__name__)
    logger.info("Starting subber with directory: %s", directory)
    logger.debug("Log file location: %s", LOGS_DIR)

    dir_path = Path(directory).resolve()
    if not dir_path.exists():
        console.print(f"[red]Directory {dir_path} does not exist![/red]")
        return

    # 1. Collect files
    video_files, subtitle_files = collect_files(dir_path)

    # 2. Match them
    exact_matches, close_matches, unmatched_videos, unmatched_subtitles = find_matches(video_files, subtitle_files)

    # 3. Display
    display_results(
        exact_matches,
        close_matches,
        unmatched_videos,
        unmatched_subtitles,
        directory=dir_path,
        no_table=no_table,
        show_full_path=path,
        output_file=output_file
    )

    # 4. Optionally rename
    if rename and close_matches:
        rename_close_matches(close_matches)

    # 5. Optionally convert videos to MP3
    if convert is not None and unmatched_videos:
        if not check_ffmpeg_installed():
            console.print(MESSAGES["FFMPEG_NOT_INSTALLED"], style=CONSOLE_STYLES["error"])
            return
            
        convert_output_dir = dir_path / convert
        
        # Convert selected video files
        converted = batch_convert_to_mp3([Path(v) for v in unmatched_videos], convert_output_dir)
        if converted > 0:
            console.print(f"\nSuccessfully converted {converted} files to MP3.", style=CONSOLE_STYLES["success"])
            console.print(f"MP3 files saved in: {convert_output_dir}", style=CONSOLE_STYLES["success"])

    # 6. Optionally move unmatched
    if move_unmatched:
        move_unmatched_files(unmatched_videos, move_unmatched, dir_path)

if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        console.print(f"\n{MESSAGES['OPERATION_CANCELLED']}", style=CONSOLE_STYLES["warning"])
        exit(0) 