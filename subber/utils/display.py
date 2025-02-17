"""
Display utilities for formatting and presenting results.
"""

import logging
from pathlib import Path
from typing import List, Tuple

from rich.console import Console
from rich.text import Text
from rich.panel import Panel
from rich.table import Table

from subber.core.constants import PANEL_SETTINGS, TABLE_SETTINGS, MESSAGES

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
    unmatched_subtitles: List[Path],
    directory: Path,
    no_table: bool = False,
    show_full_path: bool = False,
    output_file: str = None,
):
    """
    Display the results either as plain text or using tabulate for nice table formatting.
    Also optionally write to an output file.
    """

    def fmt_path(p: Path) -> str:
        return (
            str(p.resolve())
            if show_full_path
            else str(p.relative_to(directory.resolve()))
        )

    # Prepare text lines for each section
    exact_section = []
    close_section = []
    unmatched_video_section = []
    unmatched_subtitle_section = []

    if exact_matches:
        for video_file, subtitle_file in exact_matches:
            exact_section.append((fmt_path(video_file), fmt_path(subtitle_file)))
    if close_matches:
        for video_file, subtitle_file, sim in close_matches:
            close_section.append(
                (fmt_path(video_file), fmt_path(subtitle_file), f"{sim:.2f}")
            )
    if unmatched_videos:
        for video_file in unmatched_videos:
            unmatched_video_section.append((fmt_path(video_file),))
    if unmatched_subtitles:
        for subtitle_file in unmatched_subtitles:
            unmatched_subtitle_section.append((fmt_path(subtitle_file),))

    # If no_table, print plain text
    if no_table:
        # Exact matches section
        exact_content = Text()
        if exact_section:
            for video_file, subtitle_file in exact_section:
                exact_content.append(f"{video_file} --> {subtitle_file}\n")
        else:
            exact_content.append(f"{MESSAGES['NO_EXACT_MATCHES']}\n")
        console.print(Panel(exact_content, **PANEL_SETTINGS["EXACT_MATCHES"]))

        # Close matches section
        close_content = Text()
        if close_section:
            for video_file, subtitle_file, sim in close_section:
                close_content.append(
                    f"{video_file} --> {subtitle_file} (Similarity: {sim})\n"
                )
        else:
            close_content.append(f"{MESSAGES['NO_CLOSE_MATCHES']}\n")
        console.print(Panel(close_content, **PANEL_SETTINGS["CLOSE_MATCHES"]))

        # Unmatched video files section
        unmatched_video_content = Text()
        if unmatched_video_section:
            for (video_file,) in unmatched_video_section:
                unmatched_video_content.append(f"{video_file}\n")
        else:
            unmatched_video_content.append(f"{MESSAGES['ALL_VIDEOS_MATCHED']}\n")
        console.print(
            Panel(unmatched_video_content, **PANEL_SETTINGS["UNMATCHED_VIDEOS"])
        )

        # Unmatched subtitle files section
        unmatched_subtitle_content = Text()
        if unmatched_subtitle_section:
            for (subtitle_file,) in unmatched_subtitle_section:
                unmatched_subtitle_content.append(f"{subtitle_file}\n")
        else:
            unmatched_subtitle_content.append(f"{MESSAGES['ALL_SUBS_MATCHED']}\n")
        console.print(
            Panel(unmatched_subtitle_content, **PANEL_SETTINGS["UNMATCHED_SUBTITLES"])
        )
    else:
        # Use Rich tables with borders
        # Exact matches table
        if exact_section:
            table = Table(**TABLE_SETTINGS["EXACT_MATCHES"])
            table.add_column("Video File")
            table.add_column("Subtitle File")
            for video_file, subtitle_file in exact_section:
                table.add_row(video_file, subtitle_file)
            console.print(table)
        else:
            console.print(
                Panel(MESSAGES["NO_EXACT_MATCHES"], **PANEL_SETTINGS["EXACT_MATCHES"])
            )

        # Close matches table
        if close_section:
            table = Table(**TABLE_SETTINGS["CLOSE_MATCHES"])
            table.add_column("Video File")
            table.add_column("Subtitle File")
            table.add_column("Similarity")
            for video_file, subtitle_file, sim in close_section:
                table.add_row(video_file, subtitle_file, sim)
            console.print(table)
        else:
            console.print(
                Panel(MESSAGES["NO_CLOSE_MATCHES"], **PANEL_SETTINGS["CLOSE_MATCHES"])
            )

        # Unmatched video files table
        if unmatched_video_section:
            table = Table(**TABLE_SETTINGS["UNMATCHED_VIDEOS"])
            table.add_column("Video File")
            for (video_file,) in unmatched_video_section:
                table.add_row(video_file)
            console.print(table)
        else:
            console.print(
                Panel(
                    MESSAGES["ALL_VIDEOS_MATCHED"], **PANEL_SETTINGS["UNMATCHED_VIDEOS"]
                )
            )

        # Unmatched subtitle files table
        if unmatched_subtitle_section:
            table = Table(**TABLE_SETTINGS["UNMATCHED_SUBTITLES"])
            table.add_column("Subtitle File")
            for (subtitle_file,) in unmatched_subtitle_section:
                table.add_row(subtitle_file)
            console.print(table)
        else:
            console.print(
                Panel(
                    MESSAGES["ALL_SUBS_MATCHED"],
                    **PANEL_SETTINGS["UNMATCHED_SUBTITLES"],
                )
            )

    # Write to output file if specified
    if output_file:
        all_text = []
        all_text.append("\nExact Matches:")
        if exact_section:
            for video_file, subtitle_file in exact_section:
                all_text.append(f"{video_file} --> {subtitle_file}")
        else:
            all_text.append("No exact matches found.")

        all_text.append("\nClose Matches:")
        if close_section:
            for video_file, subtitle_file, sim in close_section:
                all_text.append(f"{video_file} --> {subtitle_file} (Similarity: {sim})")
        else:
            all_text.append("No close matches found.")

        all_text.append("\nUnmatched Video Files:")
        if unmatched_video_section:
            for (video_file,) in unmatched_video_section:
                all_text.append(video_file)
        else:
            all_text.append("All video files have matching subtitles.")

        all_text.append("\nUnmatched Subtitle Files:")
        if unmatched_subtitle_section:
            for (subtitle_file,) in unmatched_subtitle_section:
                all_text.append(subtitle_file)
        else:
            all_text.append("All subtitle files have matching videos.")

        with open(output_file, "w", encoding="utf-8") as f:
            f.write("\n".join(all_text))

    # If output_file is provided, save text-based results to file
    if output_file:
        all_text = []
        all_text.append("Exact Matches:")
        if exact_section:
            for video_file, subtitle_file in exact_section:
                all_text.append(f"{video_file} --> {subtitle_file}")
        else:
            all_text.append("No exact matches found.")

        all_text.append("\nClose Matches:")
        if close_section:
            for video_file, subtitle_file, sim in close_section:
                all_text.append(f"{video_file} --> {subtitle_file} (Similarity: {sim})")
        else:
            all_text.append("No close matches found.")

        all_text.append("\nUnmatched Video Files:")
        if unmatched_video_section:
            for (video_file,) in unmatched_video_section:
                all_text.append(video_file)
        else:
            all_text.append("All video files have matching subtitles.")

        all_text.append("\nUnmatched Subtitle Files:")
        if unmatched_subtitle_section:
            for (subtitle_file,) in unmatched_subtitle_section:
                all_text.append(subtitle_file)
        else:
            all_text.append("All subtitle files have matching videos.")

        try:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write("\n".join(all_text) + "\n")
            console.print(
                Panel(
                    f"Results written to {output_file}",
                    border_style="green",
                    title="Success",
                    title_align="left",
                )
            )
        except Exception as e:
            logging.error("Error writing to file %s: %s", output_file, e)
            console.print(
                Panel(
                    f"Error writing to file {output_file}: {e}",
                    border_style="red",
                    title="Error",
                    title_align="left",
                )
            )
