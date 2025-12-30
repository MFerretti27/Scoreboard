"""Module to Create and modify scoreboard GUI using FreeSimpleGUI."""
import gc
import json
import os
import platform
import subprocess
import sys
import tempfile
import time
import tkinter as tk
import typing
from datetime import datetime
from pathlib import Path
from tkinter import font as tk_font
from typing import Any

import FreeSimpleGUI as Sg  # type: ignore[import]
import orjson  # type: ignore[import]

import settings
from helper_functions.logger_config import logger
from helper_functions.main_menu_helpers import settings_to_json
from helper_functions.update import check_for_update, update_program


def will_text_fit_on_screen(text: str, txt_size: int | None = None) -> bool:
    """Check if text will fit on screen.

    :param text: str to compare to width of screen

    :return bool: boolean value representing if string will fit on screen
    """
    if settings.no_spoiler_mode:
        return False

    if txt_size is None:
        txt_size = settings.INFO_TXT_SIZE

    screen_width = Sg.Window.get_screen_size()[0]  # Get screen width

    root = tk.Tk()
    root.withdraw()  # Hide the root window
    font = tk_font.Font(family=settings.FONT, size=txt_size)
    txt_width: float = float(font.measure(text))
    txt_width = txt_width * 1.1  # Ensure text fits on screen by adding a buffer
    root.destroy()

    if txt_width >= screen_width:
        logger.info("Bottom Text will scroll, text size: %s, screen size: %s", int(txt_width), screen_width)
        return True

    return False


def reset_window_elements(window: Sg.Window) -> None:
    """Reset window elements to default values.

    :param window: element that can be updated for displaying information
    """
    window["top_info"].update(value="", font=(settings.FONT, settings.NOT_PLAYING_TOP_INFO_SIZE), text_color="white")
    window["bottom_info"].update(value="", font=(settings.FONT, settings.INFO_TXT_SIZE), text_color="white")
    window["home_timeouts"].update(value="", font=(settings.FONT, settings.TIMEOUT_SIZE), text_color="white")
    window["away_timeouts"].update(value="", font=(settings.FONT, settings.TIMEOUT_SIZE), text_color="white")
    window["home_record"].update(value="", font=(settings.FONT, settings.RECORD_TXT_SIZE), text_color="white")
    window["away_record"].update(value="", font=(settings.FONT, settings.RECORD_TXT_SIZE), text_color="white")
    window["home_score"].update(value="", font=(settings.FONT, settings.SCORE_TXT_SIZE), text_color="white")
    window["away_score"].update(value="", font=(settings.FONT, settings.SCORE_TXT_SIZE), text_color="white")
    window["above_score_txt"].update(value="", font=(settings.FONT, settings.NBA_TIMEOUT_SIZE),
                                     text_color="white")
    if Sg.Window.get_screen_size()[1] < 1000:
        window["home_player_stats"].update(value="", text_color="white")
    window["away_player_stats"].update(value="", text_color="white")
    window["hyphen"].update(value="-", font=(settings.FONT, settings.HYPHEN_SIZE), text_color="white")
    window["signature"].update(value="Created By: Matthew Ferretti",font=(settings.FONT, settings.SIGNATURE_SIZE),
                               text_color="white")

    window["home_team_stats"].update(value="", text_color="white")
    window["away_team_stats"].update(value="", text_color="white")


def _toggle_team_stats(window: Sg.Window, team: str, *, currently_playing: bool, event: str) -> None:
    """Toggle team stats display visibility.

    :param window: The window element to update
    :param team: Either 'home' or 'away'
    :param currently_playing: Whether game is currently playing
    :param event: The event that triggered this
    """
    logger.info(f"{event} key pressed, displaying team info")

    alignment = "center" if currently_playing else "left"
    elem = window[f"{team}_team_stats"]
    current_text = elem.get()
    elem.Widget.configure(state="normal")
    elem.Widget.delete("1.0", "end")
    elem.Widget.tag_configure(alignment, justify=alignment)
    elem.Widget.insert("1.0", current_text, alignment)
    elem.Widget.configure(state="disabled")

    window[f"{team}_logo_section"].update(visible=False)
    window[f"{team}_stats_section"].update(visible=True)
    window.refresh()
    wait(window, 10, currently_playing=currently_playing)
    window[f"{team}_logo_section"].update(visible=True)
    window[f"{team}_stats_section"].update(visible=False)


def check_events(window: Sg.Window, events: list, *, currently_playing: bool = False) -> None:
    """Check for specific key presses.

    :param window: element that can be updated for displaying information
    :param events: key presses that were recorded
    :param currently_playing: current state of scoreboard allowing for more or less key presses
    """
    event = events[0].split(":")[0] if ":" in events[0] else events[0]

    # Exit/close handling
    if event == Sg.WIN_CLOSED or "Escape" in event or "above_score_txt" in event:
        window.close()
        gc.collect()  # Clean up memory
        time.sleep(0.5)  # Give OS time to destroy the window
        json_ready_data = convert_paths_to_strings(settings.saved_data)  # Convert all Path type to string
        json_saved_data = orjson.dumps(json_ready_data)
        subprocess.Popen([sys.executable, "-m", "screens.main_screen", "--saved-data", json_saved_data])
        sys.exit()

    # Spoiler mode toggle
    spoiler_triggers = ("Up", "away_score", "home_score")
    if any(key in event for key in spoiler_triggers) and not settings.no_spoiler_mode:
        settings.no_spoiler_mode = True
        window = set_spoiler_mode(window, {"above_score_txt": ""})
        window.refresh()
    elif any(
        key in event for key in (*spoiler_triggers, "Down", "away_timeouts", "home_timeouts")
    ) and settings.no_spoiler_mode:
        settings.no_spoiler_mode = False
        window["top_info"].update(value="")
        window["bottom_info"].update(value="Exiting No Spoiler Mode")
        window.refresh()
        time.sleep(2)

    # Team stats display
    if any(key in event for key in ("away_logo", "away_record", "away_team_stats")):
        _toggle_team_stats(window, "away", currently_playing=currently_playing, event=event)

    if any(key in event for key in ("home_logo", "home_record", "home_team_stats")):
        _toggle_team_stats(window, "home", currently_playing=currently_playing, event=event)

    # Delay toggle
    delay_triggers = ("Left", "Right", "top_info", "bottom_info")
    if any(key in event for key in delay_triggers):
        logger.info(f"{event} key pressed, delay off")
        settings.delay = not settings.delay
        msg = "Turning delay OFF" if not settings.delay else f"Turning delay ON ({settings.LIVE_DATA_DELAY} seconds)"
        window["bottom_info"].update(value=msg)
        window.refresh()
        time.sleep(5)


def set_spoiler_mode(window: Sg.Window, team_info: dict) -> Sg.Window:
    """Set screen to spoiler mode, hiding all data that can spoil game.

    :param window: element that can be updated for displaying information
    :param currently_playing: boolean value to tell what message to display
    :param team_info: team data that shows if certain elements should be changed so as to not spoil anything

    :return window: element updates for window to change
    """
    window["top_info"].update(value="Will Not Display Game Info", font=(settings.FONT,
                                                                        settings.NOT_PLAYING_TOP_INFO_SIZE))
    window["bottom_info"].update(value="No Spoiler Mode On", font=(settings.FONT, settings.INFO_TXT_SIZE))
    window["under_score_image"].update(filename="")
    if "@" not in team_info.get("above_score_txt", ""):  # Only remove if text doesn't contain team names
        window["above_score_txt"].update(value="")
    window["home_score"].update(value="0", text_color="white")
    window["away_score"].update(value="0", text_color="white")
    window["home_timeouts"].update(value="")
    window["away_timeouts"].update(value="")
    window["home_record"].update(value="")
    window["away_record"].update(value="")

    if Sg.Window.get_screen_size()[1] < 1000:  # If screen height is small, hide player stats
        window["home_player_stats"].update(value="")
    window["away_player_stats"].update(value="")

    return window


def resize_text() -> None:
    """Resize text to fit screen size."""
    window_width = Sg.Window.get_screen_size()[0]

    # Common base screen widths
    common_base_widths = [1366, 1920, 1440, 1280]
    # Find the largest base width that doesn't exceed the window width using `max()`
    base_width = max([width for width in common_base_widths if width <= window_width], default=1366)
    scale = window_width / base_width

    logger.info("Closest screen size: %s, multiplier: %s\n", base_width, scale)

    max_size = 200
    settings.SCORE_TXT_SIZE = min(max_size, max(40, int(80 * scale)))
    settings.INFO_TXT_SIZE = min(max_size, max(20, int(68 * scale)))
    settings.RECORD_TXT_SIZE = min(max_size, max(35, int(72 * scale)))
    settings.CLOCK_TXT_SIZE = min(max_size, max(60, int(150 * scale)))
    settings.HYPHEN_SIZE = min(max_size, max(30, int(50 * scale)))
    settings.TIMEOUT_SIZE = min(max_size, max(18, int(26 * scale)))
    settings.NBA_TOP_INFO_SIZE = min(max_size, max(14, int(38 * scale)))
    settings.NHL_TOP_INFO_SIZE = min(max_size, max(15, int(42 * scale)))
    settings.MLB_BOTTOM_INFO_SIZE = min(max_size, max(20, int(60 * scale)))
    settings.PLAYING_TOP_INFO_SIZE = min(max_size, max(60, int(57 * scale)))
    settings.NOT_PLAYING_TOP_INFO_SIZE = min(max_size, max(10, int(34 * scale)))
    settings.TOP_TXT_SIZE = min(max_size, max(10, int(35 * scale)))
    settings.SIGNATURE_SIZE = min(15, max(7, int(9 * scale)))
    settings.PLAYER_STAT_SIZE = min(18, max(4, int(14 * scale)))
    settings.PLAYER_STAT_COLUMN = min(50, max(12, int(14 * scale)))
    settings.NBA_TIMEOUT_SIZE = min(max_size, max(8, int(16 * scale)))

    logger.info("\nScore txt size: %s", settings.SCORE_TXT_SIZE)
    logger.info("Info txt size: %s", settings.INFO_TXT_SIZE)
    logger.info("Record txt size: %s", settings.RECORD_TXT_SIZE)
    logger.info("Clock txt size: %s", settings.CLOCK_TXT_SIZE)
    logger.info("Hyphen txt size: %s", settings.HYPHEN_SIZE)
    logger.info("Timeout txt size: %s", settings.TIMEOUT_SIZE)
    logger.info("NBA timeouts txt size: %s", settings.NBA_TIMEOUT_SIZE)
    logger.info("NBA top txt size: %s", settings.NBA_TOP_INFO_SIZE)
    logger.info("NHL top txt size: %s", settings.NHL_TOP_INFO_SIZE)
    logger.info("MLB bottom txt size: %s", settings.MLB_BOTTOM_INFO_SIZE)
    logger.info("Playing txt size: %s", settings.PLAYING_TOP_INFO_SIZE)
    logger.info("Not playing top txt size: %s", settings.NOT_PLAYING_TOP_INFO_SIZE)
    logger.info("Top txt size: %s", settings.TOP_TXT_SIZE)
    logger.info("Signature txt size: %s", settings.SIGNATURE_SIZE)
    logger.info("Player Stat txt size: %s", settings.PLAYER_STAT_SIZE)
    logger.info("Player Stat column size: %s\n", settings.PLAYER_STAT_COLUMN)



def convert_paths_to_strings(obj: object) -> object:
    """Recursively convert all Path objects in a nested structure to strings."""
    if isinstance(obj, dict):
        return {k: convert_paths_to_strings(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [convert_paths_to_strings(i) for i in obj]
    if isinstance(obj, Path):
        return str(obj)

    return obj


def scroll(window: Sg.Window, original_text: str, key: str="bottom_info") -> None:
    """Scroll the display to show the next set of information.

    :param window: The window element to update
    :param text: The text to scroll
    :param display_index: The index of the team to update
    :param key: The key of the window element to update
    """
    text = original_text + "         "  # Add spaces to end for smooth scrolling
    for i in range(2):
        for _ in range(len(text)):
            event = window.read(timeout=100)
            text = text[1:] + text[0]
            check_events(window, event)
            if settings.no_spoiler_mode:
                set_spoiler_mode(window, {})
                window.refresh()
                break

            window[key].update(value=text)

        if i == 0:
            window[key].update(value=original_text)
            wait(window, 5)

def maximize_screen(window: Sg.Window) -> None:
    """Maximize the window to fullscreen."""
    # Maximize does not work on MacOS, so we use attributes to set fullscreen
    if platform.system() == "Darwin":
        window.TKroot.attributes("-fullscreen", True)  # noqa: FBT003
    else:
        window.Maximize()


def auto_update(window: Sg.Window, saved_data: dict[str, Any]) -> None:
    """Automatically update the program at 4:30 AM if auto_update is enabled."""
    if settings.auto_update and datetime.now().hour == 4 and datetime.now().minute == 30:
        logger.info("Updating program automatically at 4:30 AM")

        message, successful, latest = check_for_update()
        logger.info(message)
        if successful and not latest:
            window.read(timeout=100)
            saved_settings = settings_to_json()
            serializable_settings = {
                k: v for k, v in saved_settings.items()
                if not isinstance(v, type) and not isinstance(v, typing._SpecialForm)  # noqa: SLF001
            }

            settings_json = json.dumps(serializable_settings, indent=2)

            with tempfile.NamedTemporaryFile("w", delete=False, suffix=".json") as tmp:
                tmp.write(settings_json)
                tmp_path = tmp.name
            _, successful = update_program()
            if successful:
                window.read(timeout=5)
                time.sleep(3)

                # Relaunch script, passing temp filename as argument
                python = sys.executable
                os.execl(
                    python,
                    python,
                    "-m", "screens.not_playing_screen",
                    "--settings", tmp_path,
                    "--saved-data", json.dumps(saved_data),
                )


def wait(window: Sg.Window, time_waiting: int, *, currently_playing: bool = False) -> None:
    """Wait for a short period to allow GUI to update.

    :param window: Window Element that controls GUI
    :param time_waiting: Time to wait in seconds
    :param currently_playing: current state of scoreboard allowing for more or less key presses
    """
    for _ in range(int(time_waiting / 0.2)):
        event = window.read(timeout=0.1)
        check_events(window, event, currently_playing=currently_playing)  # Check for button presses
        time.sleep(0.1)

def increase_text_size(window: Sg.Window, team_info: dict,team_league: str = ""
                       ,*, currently_playing: bool = False) -> None:
    """Increase the size of the score text and timeouts text if there is more room on the screen.

    :param window: The window element to update
    :param team_info: The team information dictionary
    :param team_league: The league of the teams playing
    :param currently_playing: Whether a game is currently in progress; defaults to False.
    :return: None
    """
    # Create root window once for font measurements (major performance improvement)
    root = tk.Tk()
    root.withdraw()

    def find_max_font_size(text: str, base_size: int, screen_width: float,
                           max_iterations: int = 100, buffer: float = 1.1) -> int:
        """Find the maximum font size that fits within screen width."""
        for i in range(max_iterations):
            new_txt_size = base_size + i
            font = tk_font.Font(family=settings.FONT, size=new_txt_size)
            txt_width = float(font.measure(text)) * buffer

            if txt_width > screen_width:
                return new_txt_size - 1 if i > 0 else base_size
        return base_size + max_iterations - 1

    try:
        log_entries = []
        screen_width = (Sg.Window.get_screen_size()[0] / 3)

        # Update score text
        if (Sg.Window.get_screen_size()[0] < 1000 and "FINAL" in team_info.get("bottom_info", "").upper() and
            settings.display_player_stats and team_league == "NHL"):
            # if small screen and game is final and player stats are displayed, limit score size so stats fit
            score_text = "888-888"
        else:
            score_text = f"{team_info.get('home_score', '0')}-{team_info.get('away_score', '0')}"

        new_score_size = find_max_font_size(score_text, settings.SCORE_TXT_SIZE, screen_width,
                                            max_iterations=100)
        new_hyphen_size = settings.HYPHEN_SIZE + (new_score_size - settings.SCORE_TXT_SIZE - 10)

        window["home_score"].update(font=(settings.FONT, new_score_size))
        window["away_score"].update(font=(settings.FONT, new_score_size))
        window["hyphen"].update(font=(settings.FONT, new_hyphen_size))
        if new_score_size != settings.SCORE_TXT_SIZE or new_hyphen_size != settings.HYPHEN_SIZE:
            log_entries.append(f"score: {settings.SCORE_TXT_SIZE}->{new_score_size}, "
                             f"hyphen: {settings.HYPHEN_SIZE}->{new_hyphen_size}")

        # Update timeouts text if present
        if currently_playing:
            screen_width = (Sg.Window.get_screen_size()[0] / 3) / 2
            size = settings.TIMEOUT_SIZE if team_league != "NBA" else settings.NBA_TIMEOUT_SIZE
            timeout_text = ("\u25CF  \u25CF  \u25CF  \u25CF  \u25CF  \u25CF  \u25CF"
                            if team_league == "NBA" else "\u25CF  \u25CF  \u25CF")
            new_timeout_size = find_max_font_size(timeout_text, size, screen_width, max_iterations=50, buffer=1.4)

            window["home_timeouts"].update(font=(settings.FONT, new_timeout_size))
            window["away_timeouts"].update(font=(settings.FONT, new_timeout_size))
            if new_timeout_size != size:
                log_entries.append(f"timeouts_txt: {size}->{new_timeout_size}")

        # Update above score text if present
        if "above_score_txt" in team_info:
            text = team_info.get("above_score_txt", "")
            if "@" not in text:
                screen_width = Sg.Window.get_screen_size()[0] / 3
                size = settings.NBA_TIMEOUT_SIZE
            else:
                screen_width = (Sg.Window.get_screen_size()[0] / 3) / 2
                size = settings.TOP_TXT_SIZE

                new_size = find_max_font_size(text, size, screen_width, max_iterations=50)
                window["above_score_txt"].update(font=(settings.FONT, new_size))
                if new_size != size:
                    log_entries.append(f"above_score_txt: {size}->{new_size}")

        if log_entries:
            logger.info("Increased Size: %s", ", ".join(log_entries))

    finally:
        root.destroy()


def decrease_text_size(window: Sg.Window, team_info: dict, team_league: str) -> None:
    """Decrease the size of the text to fit on the screen.

    :param window: The window element to update
    """
    root = tk.Tk()
    root.withdraw()

    def find_min_font_size(text: str, base_size: int, screen_width: float,
                        max_iterations: int = 100, buffer: float = 1.2) -> int:
        # Replace tabs with spaces for accurate measurement
        measured_text = text.replace("\t", "    ")
        size = base_size
        for _ in range(max_iterations):
            txt_width = tk_font.Font(family=settings.FONT, size=size).measure(measured_text) * buffer
            if txt_width <= screen_width:
                return size
            size = max(1, size - 1)  # step down
        return size  # smallest tried (or 1)

    try:
        log_entries = []
        screen_width = Sg.Window.get_screen_size()[0]

        # Update score text
        top_info = team_info.get("top_info", "")

        if team_league == "NBA":
            size = settings.NBA_TOP_INFO_SIZE
        elif team_league == "NHL":
            size = settings.NHL_TOP_INFO_SIZE
        else:
            size = settings.PLAYING_TOP_INFO_SIZE

        new_top_info_size = find_min_font_size(top_info, size, screen_width, max_iterations=100)

        window["top_info"].update(font=(settings.FONT, new_top_info_size))
        if new_top_info_size != size:
            log_entries.append(f"top_info: {size}->{new_top_info_size}")

        if log_entries:
            logger.info("Decreased Size: %s", ", ".join(log_entries))

    finally:
        root.destroy()
