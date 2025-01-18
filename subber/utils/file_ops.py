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
        logger.debug("[yellow]No close matches to rename[/yellow]")
        return

    try:
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
        for (video_file, subtitle_file, sim) in close_matches:
            label = create_rich_label(video_file, subtitle_file, sim)
            file_choices.append({"name": str(label), "value": (video_file, subtitle_file)})

        choices.extend(file_choices)
        logger.debug(f"[blue]Found[/blue] [cyan]{len(file_choices)}[/cyan] [blue]pairs available for renaming[/blue]")

        selected = questionary.checkbox(
            "Select which pairs you want to rename:",
            choices=choices
        ).ask()

        # Handle selection
        if not selected:
            logger.debug("[yellow]No pairs selected for renaming[/yellow]")
            console.print(Panel(
                "No pairs selected for renaming.",
                border_style=CONSOLE_STYLES["warning"],
                title="Status",
                title_align="left"
            ))
            return

        # If "Select All" is chosen, use all file pairs
        selected_pairs = []
        if "ALL" in selected:
            selected_pairs = [choice["value"] for choice in file_choices]
            logger.debug("[blue]Selected all pairs for renaming[/blue]")
        else:
            selected_pairs = selected
            logger.debug(f"[blue]Selected[/blue] [cyan]{len(selected_pairs)}[/cyan] [blue]pairs for renaming[/blue]")

        if not selected_pairs:
            logger.debug("[yellow]No pairs selected after processing selection[/yellow]")
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
            for (video_file, subtitle_file) in selected_pairs:
                new_subtitle = subtitle_file.with_name(video_file.stem + subtitle_file.suffix)
                logger.debug(f"[blue]Processing rename:[/blue] [cyan]`{str(subtitle_file)}`[/cyan] [blue]->[/blue] [cyan]`{str(new_subtitle)}`[/cyan]")
                
                progress.update(
                    rename_task,
                    description=f"Renaming {subtitle_file.name} -> {new_subtitle.name}"
                )
                
                if new_subtitle.exists():
                    logger.debug(f"[yellow]Target file already exists:[/yellow] [cyan]`{str(new_subtitle)}`[/cyan]")
                    table.add_row(
                        str(subtitle_file),
                        str(new_subtitle),
                        "❌ File exists"
                    )
                    continue
                
                try:
                    subtitle_file.rename(new_subtitle)
                    logger.debug(f"[green]Successfully renamed:[/green] [cyan]`{str(subtitle_file)}`[/cyan] [green]->[/green] [cyan]`{str(new_subtitle)}`[/cyan]")
                    table.add_row(
                        str(subtitle_file),
                        str(new_subtitle),
                        "✓ Renamed"
                    )
                except Exception as e:
                    logger.error(f"[red]Error renaming file[/red] [cyan]`{str(subtitle_file)}`[/cyan][red]:[/red] {e}")
                    logger.debug(f"[red]Rename error details:[/red] {str(e)}")
                    table.add_row(
                        str(subtitle_file),
                        str(new_subtitle),
                        f"❌ Error: {e}"
                    )
                finally:
                    progress.advance(rename_task)

        logger.debug("[green]Rename operations complete[/green]")
        console.print(table)
        
    except Exception as e:
        logger.error(f"[red]Error during rename operation:[/red] {e}")
        logger.debug(f"[red]Rename operation error details:[/red] {str(e)}")
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
        logger.debug("[yellow]No unmatched files to move[/yellow]")
        return
        
    if not destination_folder:
        logger.debug("[yellow]No destination folder specified[/yellow]")
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
        logger.debug(f"[blue]Created/verified destination directory:[/blue] [cyan]`{str(dest_path)}`[/cyan]")

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
            
            for video_file in unmatched_videos:
                target_file = dest_path.joinpath(video_file.name)
                logger.debug(f"[blue]Processing move:[/blue] [cyan]`{str(video_file)}`[/cyan] [blue]->[/blue] [cyan]`{str(target_file)}`[/cyan]")
                
                progress.update(
                    move_task,
                    description=f"Moving {video_file.name}"
                )
                
                if target_file.exists():
                    logger.debug(f"[yellow]Target file already exists:[/yellow] [cyan]`{str(target_file)}`[/cyan]")
                    table.add_row(
                        str(video_file.name),
                        str(dest_path),
                        "❌ File exists"
                    )
                    continue

                answer = questionary.confirm(f"Move {video_file.name} to {dest_path}?").ask()
                if answer:
                    try:
                        shutil.move(str(video_file), str(target_file))
                        logger.debug(f"[green]Successfully moved:[/green] [cyan]`{str(video_file)}`[/cyan] [green]->[/green] [cyan]`{str(target_file)}`[/cyan]")
                        table.add_row(
                            str(video_file.name),
                            str(dest_path),
                            "✓ Moved"
                        )
                    except Exception as e:
                        logger.error(f"[red]Error moving file[/red] [cyan]`{str(video_file)}`[/cyan][red]:[/red] {e}")
                        logger.debug(f"[red]Move error details:[/red] {str(e)}")
                        table.add_row(
                            str(video_file.name),
                            str(dest_path),
                            f"❌ Error: {e}"
                        )
                else:
                    logger.debug(f"[yellow]User skipped moving:[/yellow] [cyan]`{str(video_file)}`[/cyan]")
                    table.add_row(
                        str(video_file.name),
                        str(dest_path),
                        "Skipped"
                    )
                progress.advance(move_task)

        logger.debug("[green]Move operations complete[/green]")
        console.print(table)
        
    except Exception as e:
        logger.error(f"[red]Error during move operation:[/red] {e}")
        logger.debug(f"[red]Move operation error details:[/red] {str(e)}")
        raise FileOperationError(f"Error during move operation: {e}") 