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
@click.option("-c", "--convert", is_flag=False, flag_value="audio_files", default=None, help="Convert selected video files to MP3 format. Optionally specify output subdirectory (default: 'audio_files')")
@click.option("-v", "--verbose", is_flag=True, help="Enable verbose output with debug information")
def main(directory, output_file, no_table, path, move_unmatched, rename, convert, verbose):
    """
    Find and match video files with their corresponding subtitle files.
    
    This tool recursively searches a directory for video files (.mkv, .mov, .mp4)
    and subtitle files (.srt), matches them based on filename similarity, and
    provides options for renaming and organizing the files.
    """
    # Configure logging based on verbose flag
    log_level = logging.DEBUG if verbose else logging.WARNING
    
    # Configure root logger with Rich handler and custom formatter
    handler = RichHandler(
        rich_tracebacks=True,
        markup=True,
        show_time=True,
        show_level=True,
        show_path=False,
        level=log_level,
        console=console,
        tracebacks_extra_lines=2,
        tracebacks_theme="monokai",
    )
    handler.setFormatter(RichFileFormatter("%(message)s"))
    
    logging.basicConfig(
        level=log_level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[handler]
    )
    
    # Silence other loggers unless in verbose mode
    if not verbose:
        logging.getLogger('questionary').setLevel(logging.WARNING)
        logging.getLogger('rich').setLevel(logging.WARNING)
        logging.getLogger('click').setLevel(logging.WARNING)

    show_ascii_art()

    dir_path = Path(directory).resolve()
    if not dir_path.exists():
        print(click.style(f"Directory {dir_path} does not exist!", fg="red"))
        return

    # 1. Collect files
    video_files, subtitle_files = collect_files(dir_path)

    # 2. Match them
    exact_matches, close_matches, unmatched_videos = find_matches(video_files, subtitle_files)

    # 3. Display
    display_results(
        exact_matches,
        close_matches,
        unmatched_videos,
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
            print(click.style("Error: ffmpeg is not installed. Please install it to use the conversion feature.", fg="red"))
            return
            
        convert_output_dir = dir_path / convert
        
        # Convert selected video files
        converted = batch_convert_to_mp3([Path(v) for v in unmatched_videos], convert_output_dir)
        if converted > 0:
            print(click.style(f"\nSuccessfully converted {converted} files to MP3.", fg="green"))
            print(click.style(f"MP3 files saved in: {convert_output_dir}", fg="green"))

    # 6. Optionally move unmatched
    if move_unmatched:
        move_unmatched_files(unmatched_videos, move_unmatched, dir_path)

if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        console.print("\nOperation cancelled by user.", style="yellow")
        exit(0) 