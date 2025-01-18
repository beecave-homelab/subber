"""
Display utilities for formatting and presenting results.
"""

from pathlib import Path
from typing import List, Tuple
from rich.console import Console
from rich.text import Text
from rich.panel import Panel
from rich.table import Table
from tabulate import tabulate
import logging

# Initialize Rich console
console = Console()

def show_ascii_art():
    """
    Print ASCII art with color using Rich.
    """
    art = r"""
 ▗▄▄▖▗▖ ▗▖▗▄▄▖ ▗▄▄▖ ▗▄▄▄▖▗▄▄▖ 
▐▌   ▐▌ ▐▌▐▌ ▐▌▐▌ ▐▌▐▌   ▐▌ ▐▌
 ▝▀▚▖▐▌ ▐▌▐▛▀▚▖▐▛▀▚▖▐▛▀▀▘▐▛▀▚▖
▗▄▄▞▘▝▚▄▞▘▐▙▄▞▘▐▙▄▞▘▐▙▄▄▖▐▌ ▐▌
    """
    # Print art in cyan panel
    console.print(Panel(art, border_style="cyan", title="subber", expand=False))

def display_results(
    exact_matches: List[Tuple[Path, Path]],
    close_matches: List[Tuple[Path, Path, float]],
    unmatched_videos: List[Path],
    directory: Path,
    no_table: bool = False,
    show_full_path: bool = False,
    output_file: str = None
):
    """
    Display the results either as plain text or using tabulate for nice table formatting.
    Also optionally write to an output file.
    """
    def fmt_path(p: Path) -> str:
        return str(p.resolve()) if show_full_path else str(p.relative_to(directory.resolve()))

    # Prepare text lines for each section
    exact_section = []
    close_section = []
    unmatched_section = []

    if exact_matches:
        for vf, sf in exact_matches:
            exact_section.append((fmt_path(vf), fmt_path(sf)))
    if close_matches:
        for vf, sf, sim in close_matches:
            close_section.append((fmt_path(vf), fmt_path(sf), f"{sim:.2f}"))
    if unmatched_videos:
        for vf in unmatched_videos:
            unmatched_section.append((fmt_path(vf),))

    # If no_table, print plain text
    if no_table:
        # Exact matches section
        exact_content = Text()
        if exact_section:
            for vf, sf in exact_section:
                exact_content.append(f"{vf} --> {sf}\n")
        else:
            exact_content.append("No exact matches found.\n")
        console.print(Panel(exact_content, title="Exact Matches", border_style="green", title_align="left"))

        # Close matches section
        close_content = Text()
        if close_section:
            for vf, sf, sim in close_section:
                close_content.append(f"{vf} --> {sf} (Similarity: {sim})\n")
        else:
            close_content.append("No close matches found.\n")
        console.print(Panel(close_content, title="Close Matches", border_style="yellow", title_align="left"))

        # Unmatched files section
        unmatched_content = Text()
        if unmatched_section:
            for (vf,) in unmatched_section:
                unmatched_content.append(f"{vf}\n")
        else:
            unmatched_content.append("All video files have matching subtitles.\n")
        console.print(Panel(unmatched_content, title="Unmatched Video Files", border_style="red", title_align="left"))
    else:
        # Use Rich tables with borders
        if exact_section:
            table = Table(title="Exact Matches", border_style="green", header_style="bold green")
            table.add_column("Video File")
            table.add_column("Subtitle File")
            for vf, sf in exact_section:
                table.add_row(vf, sf)
            console.print(table)
        else:
            console.print(Panel("No exact matches found.", title="Exact Matches", border_style="green", title_align="left"))

        if close_section:
            table = Table(title="Close Matches", border_style="yellow", header_style="bold yellow")
            table.add_column("Video File")
            table.add_column("Subtitle File")
            table.add_column("Similarity")
            for vf, sf, sim in close_section:
                table.add_row(vf, sf, sim)
            console.print(table)
        else:
            console.print(Panel("No close matches found.", title="Close Matches", border_style="yellow", title_align="left"))

        if unmatched_section:
            table = Table(title="Unmatched Video Files", border_style="red", header_style="bold red")
            table.add_column("Video File")
            for (vf,) in unmatched_section:
                table.add_row(vf)
            console.print(table)
        else:
            console.print(Panel("All video files have matching subtitles.", title="Unmatched Video Files", border_style="red", title_align="left"))

    # If output_file is provided, save text-based results to file
    if output_file:
        all_text = []
        all_text.append("Exact Matches:")
        if exact_section:
            for vf, sf in exact_section:
                all_text.append(f"{vf} --> {sf}")
        else:
            all_text.append("No exact matches found.")

        all_text.append("\nClose Matches:")
        if close_section:
            for vf, sf, sim in close_section:
                all_text.append(f"{vf} --> {sf} (Similarity: {sim})")
        else:
            all_text.append("No close matches found.")

        all_text.append("\nUnmatched Video Files:")
        if unmatched_section:
            for (vf,) in unmatched_section:
                all_text.append(vf)
        else:
            all_text.append("All video files have matching subtitles.")

        try:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write("\n".join(all_text) + "\n")
            console.print(Panel(f"Results written to {output_file}", border_style="green", title="Success", title_align="left"))
        except Exception as e:
            logging.error("Error writing to file %s: %s", output_file, e)
            console.print(Panel(f"Error writing to file {output_file}: {e}", border_style="red", title="Error", title_align="left")) 