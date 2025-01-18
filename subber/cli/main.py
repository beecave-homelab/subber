"""
Command-line interface for the subber package.
"""

import logging
import click
from pathlib import Path

from subber.core.matcher import collect_files, find_matches
from subber.utils.display import show_ascii_art, display_results
from subber.utils.file_ops import rename_close_matches, move_unmatched_files

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

@click.command()
@click.option("-d", "--directory", default=".", show_default=True, help="Directory to search for files")
@click.option("-o", "--output-file", help="File path to save the output")
@click.option("-n", "--no-table", is_flag=True, help="Output results without table formatting")
@click.option("-p", "--path", is_flag=True, help="Show the full path of the files in the output")
@click.option("-m", "--move-unmatched", help="Folder to move unmatched video files into")
@click.option("-r", "--rename", is_flag=True, help="Interactively rename close-matched subtitle files to match video names")
def main(directory, output_file, no_table, path, move_unmatched, rename):
    """
    Find and match video files with their corresponding subtitle files.
    
    This tool recursively searches a directory for video files (.mkv, .mov, .mp4)
    and subtitle files (.srt), matches them based on filename similarity, and
    provides options for renaming and organizing the files.
    """
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

    # 5. Optionally move unmatched
    if move_unmatched:
        move_unmatched_files(unmatched_videos, move_unmatched, dir_path)

if __name__ == "__main__":
    main() 