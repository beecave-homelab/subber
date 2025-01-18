"""
File operation utilities for renaming and moving files.
"""

import logging
import shutil
from pathlib import Path
from typing import List, Tuple
import questionary
from rich.console import Console
from rich.text import Text
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..core.constants import CONSOLE_STYLES

# Initialize Rich console and logger
console = Console()
logger = logging.getLogger(__name__)

class FileOperationError(Exception):
    """Base exception for file operations."""
    pass

def create_rich_label(video_file: Path, subtitle_file: Path, similarity: float) -> Text:
    """Create a formatted label for file pairs using Rich's Text class."""
    label = Text()
    label.append(video_file.name, style=CONSOLE_STYLES["info"])
    label.append(" -> ")
    label.append(subtitle_file.name, style=CONSOLE_STYLES["success"])
    label.append(" (Similarity: ")
    label.append(f"{similarity:.2f}", style=CONSOLE_STYLES["dim"])
    label.append(")")
    return label

def rename_close_matches(
    close_matches: List[Tuple[Path, Path, float]]
) -> None:
    """
    Ask users which close-matched subtitle files to rename.
    
    Args:
        close_matches: List of tuples containing (video_file, subtitle_file, similarity)
        
    Raises:
        FileOperationError: If there's an error during file operations
    """
    if not close_matches:
        logger.info("No close matches to rename")
        return

    try:
        # Build choices for questionary
        choices = []
        for (vf, sf, sim) in close_matches:
            label = create_rich_label(vf, sf, sim)
            choices.append({"name": str(label), "value": (vf, sf)})

        selected_pairs = questionary.checkbox(
            "Select which pairs you want to rename:",
            choices=choices
        ).ask()

        if not selected_pairs:
            console.print(Panel(
                "No pairs selected for renaming.",
                border_style=CONSOLE_STYLES["warning"],
                title="Status",
                title_align="left"
            ))
            return

        # Create a table for rename operations
        table = Table(
            title="Rename Operations",
            border_style=CONSOLE_STYLES["info"],
            header_style=f"bold {CONSOLE_STYLES['info']}"
        )
        table.add_column("Source", style=CONSOLE_STYLES["info"])
        table.add_column("Target", style=CONSOLE_STYLES["success"])
        table.add_column("Status", style=CONSOLE_STYLES["warning"])

        # Show progress during rename operations
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            rename_task = progress.add_task("Renaming files...", total=len(selected_pairs))
            
            # Perform rename on selected pairs
            for (vf, sf) in selected_pairs:
                new_subtitle = sf.with_name(vf.stem + sf.suffix)
                progress.update(
                    rename_task,
                    description=f"Renaming {sf.name} -> {new_subtitle.name}"
                )
                
                if new_subtitle.exists():
                    logger.warning("Target file already exists: %s", new_subtitle)
                    table.add_row(
                        str(sf),
                        str(new_subtitle),
                        "❌ File exists"
                    )
                    continue
                
                try:
                    sf.rename(new_subtitle)
                    logger.info("Renamed %s to %s", sf, new_subtitle)
                    table.add_row(
                        str(sf),
                        str(new_subtitle),
                        "✓ Renamed"
                    )
                except Exception as e:
                    logger.error("Error renaming file %s: %s", sf, e)
                    table.add_row(
                        str(sf),
                        str(new_subtitle),
                        f"❌ Error: {e}"
                    )
                finally:
                    progress.advance(rename_task)

        console.print(table)
        
    except Exception as e:
        raise FileOperationError(f"Error during rename operation: {e}")

def move_unmatched_files(
    unmatched_videos: List[Path],
    destination_folder: str,
    base_directory: Path
) -> None:
    """
    Move unmatched video files to the specified destination folder.
    
    Args:
        unmatched_videos: List of video files to move
        destination_folder: Name of the destination folder
        base_directory: Base directory for the destination folder
        
    Raises:
        FileOperationError: If there's an error during file operations
    """
    if not unmatched_videos:
        logger.info("No unmatched files to move")
        return
        
    if not destination_folder:
        logger.warning("No destination folder specified")
        console.print(Panel(
            "No destination folder specified. Skipping move.",
            border_style=CONSOLE_STYLES["warning"],
            title="Status",
            title_align="left"
        ))
        return

    try:
        dest_path = base_directory.joinpath(destination_folder)
        dest_path.mkdir(exist_ok=True)
        logger.info("Created destination directory: %s", dest_path)

        # Create a table for move operations
        table = Table(
            title="Move Operations",
            border_style=CONSOLE_STYLES["info"],
            header_style=f"bold {CONSOLE_STYLES['info']}"
        )
        table.add_column("File", style=CONSOLE_STYLES["info"])
        table.add_column("Destination", style=CONSOLE_STYLES["success"])
        table.add_column("Status", style=CONSOLE_STYLES["warning"])

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            move_task = progress.add_task("Moving files...", total=len(unmatched_videos))
            
            for vf in unmatched_videos:
                target_file = dest_path.joinpath(vf.name)
                progress.update(
                    move_task,
                    description=f"Moving {vf.name}"
                )
                
                if target_file.exists():
                    logger.warning("Target file already exists: %s", target_file)
                    table.add_row(
                        str(vf.name),
                        str(dest_path),
                        "❌ File exists"
                    )
                    continue

                answer = questionary.confirm(f"Move {vf.name} to {dest_path}?").ask()
                if answer:
                    try:
                        shutil.move(str(vf), str(target_file))
                        logger.info("Moved %s to %s", vf, target_file)
                        table.add_row(
                            str(vf.name),
                            str(dest_path),
                            "✓ Moved"
                        )
                    except Exception as e:
                        logger.error("Error moving file %s: %s", vf, e)
                        table.add_row(
                            str(vf.name),
                            str(dest_path),
                            f"❌ Error: {e}"
                        )
                else:
                    logger.info("Skipped moving %s", vf)
                    table.add_row(
                        str(vf.name),
                        str(dest_path),
                        "Skipped"
                    )
                progress.advance(move_task)

        console.print(table)
        
    except Exception as e:
        raise FileOperationError(f"Error during move operation: {e}") 