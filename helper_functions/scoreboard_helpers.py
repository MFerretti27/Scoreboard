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
    window["above_score_txt"].update(value="", font=(settings.FONT, settings.NOT_PLAYING_TOP_INFO_SIZE),
                                     text_color="white")
    if Sg.Window.get_screen_size()[1] < 1000:
        window["home_player_stats"].update(value="", text_color="white")
    window["away_player_stats"].update(value="", text_color="white")
    window["hyphen"].update(value="-", font=(settings.FONT, settings.HYPHEN_SIZE), text_color="white")
    window["signature"].update(value="Created By: Matthew Ferretti",font=(settings.FONT, settings.SIGNATURE_SIZE),
                               text_color="white")

    window["home_team_stats"].update(value="", text_color="white")
    window["away_team_stats"].update(value="", text_color="white")


def check_events(window: Sg.Window, events: list, *, currently_playing: bool = False) -> None:
    """Check for specific key presses.

    :param window: element that can be updated for displaying information
    :param events: key presses that were recorded
    :param currently_playing: current state of scoreboard allowing for more or less key presses
    """
    event = events[0].split(":")[0] if ":" in events[0] else events[0]

    if event == Sg.WIN_CLOSED or "Escape" in event or "above_score_txt" in event:
        window.close()
        gc.collect()  # Clean up memory
        time.sleep(0.5)  # Give OS time to destroy the window
        json_ready_data = convert_paths_to_strings(settings.saved_data)  # Convert all Path type to string
        json_saved_data = orjson.dumps(json_ready_data)
        subprocess.Popen([sys.executable, "-m", "screens.main_screen", "--saved-data", json_saved_data])
        sys.exit()

    elif any(key in event for key in ("Up", "away_score", "home_score")) and not settings.no_spoiler_mode:
        settings.no_spoiler_mode = True
        team_info = {"above_score_txt": ""}
        window = set_spoiler_mode(window, team_info)
        window.refresh()

    elif any(key in event for key in ("Down", "away_score", "home_score")) and settings.no_spoiler_mode:
        settings.no_spoiler_mode = False
        window["top_info"].update(value="")
        window["bottom_info"].update(value="Exiting No Spoiler Mode")
        window.refresh()
        time.sleep(2)

    if any(key in event for key in ("away_logo", "away_record", "away_team_stats")):
            logger.info(f"{event} key pressed, displaying team info")
            window["away_logo_section"].update(visible=False)
            window["away_stats_section"].update(visible=True)
            window.refresh()
            wait(window, 10)
            window["away_logo_section"].update(visible=True)
            window["away_stats_section"].update(visible=False)

    if any(key in event for key in ("home_logo", "home_record", "home_team_stats")):
            logger.info(f"{event} key pressed, displaying team info")
            window["home_logo_section"].update(visible=False)
            window["home_stats_section"].update(visible=True)
            window.refresh()
            wait(window, 10)
            window["home_logo_section"].update(visible=True)
            window["home_stats_section"].update(visible=False)

    # if currently_playing:
    #     if any(key in event for key in ("Caps_Lock", "away_logo", "away_record")) and not settings.stay_on_team:
    #         logger.info(f"{event} key pressed, Staying on team")
    #         settings.stay_on_team = True
    #         window["bottom_info"].update(value="Staying on Team")
    #         window.refresh()
    #         time.sleep(5)
    #     elif (any(key in event for key in ("Shift_L", "Shift_R", "away_logo", "away_record")) and
    #           settings.stay_on_team):
    #         logger.info(f"{event} key pressed, Rotating teams")
    #         settings.stay_on_team = False
    #         window["bottom_info"].update(value="Rotating Teams")
    #         window.refresh()
    #         time.sleep(5)

    if any(key in event for key in ("Left", "top_info", "bottom_info")) and settings.delay:
        logger.info(f"{event} key pressed, delay off")
        settings.delay = False
        window["bottom_info"].update(value="Turning delay OFF")
        window.refresh()
        time.sleep(5)
    elif any(key in event for key in ("Right", "top_info", "bottom_info")) and not settings.delay:
        logger.info(f"{event} key pressed, delay on")
        settings.delay = True
        window["bottom_info"].update(value=f"Turning delay ON ({settings.LIVE_DATA_DELAY} seconds)")
        window.refresh()
        time.sleep(5)


def set_spoiler_mode(window: Sg.Window, team_info: dict) -> Sg.Window:
    """Set screen to spoiler mode, hiding all data that can spoil game.

    :param window: element that can be updated for displaying information
    :param currently_playing: boolean value to tell what message to display
    :param team_info: team data that shows if certain elements should be changed so as to not spoil anything

    :return window: element updates for window to change
    """
    window["top_info"].update(value="Will Not Display Game Info", font=(settings.FONT, settings.MLB_BOTTOM_INFO_SIZE))
    window["bottom_info"].update(value="No Spoiler Mode On", font=(settings.FONT, settings.MLB_BOTTOM_INFO_SIZE))
    window["under_score_image"].update(filename="")
    if "@" not in team_info["above_score_txt"]:  # Only remove if text doesn't contain team names
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
    settings.RECORD_TXT_SIZE = min(max_size, max(35, int(65 * scale)))
    settings.CLOCK_TXT_SIZE = min(max_size, max(60, int(150 * scale)))
    settings.HYPHEN_SIZE = min(max_size, max(30, int(50 * scale)))
    settings.TIMEOUT_SIZE = min(max_size, max(18, int(26 * scale)))
    settings.NBA_TOP_INFO_SIZE = min(max_size, max(15, int(30 * scale)))
    settings.NHL_TOP_INFO_SIZE = min(max_size, max(15, int(42 * scale)))
    settings.MLB_BOTTOM_INFO_SIZE = min(max_size, max(60, int(60 * scale)))
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
            window[key].update(value=text)
            check_events(window, event)

        if i == 0:
            window[key].update(value=original_text)
            event = window.read(timeout=100)
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


def wait(window: Sg.Window, time_waiting: int) -> None:
    """Wait for a short period to allow GUI to update.

    :param window: Window Element that controls GUI
    :param time_waiting: Time to wait in seconds
    """
    for _ in range(int(time_waiting / 0.2)):
        event = window.read(timeout=0.1)
        check_events(window, event)  # Check for button presses
        time.sleep(0.1)

def increase_text_size(window: Sg.Window, team_info: dict, team_league: str = "") -> None:
    """Increase the size of the score text and timeouts text if there is more room on the screen.

    :param window: The window element to update
    :param team_info: The team information dictionary
    :param team_league: The league of the teams playing
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
        screen_width = (Sg.Window.get_screen_size()[0] / 3) / 2

        # Update score text
        home_score = team_info.get("home_score", "0")
        away_score = team_info.get("away_score", "0")
        score_text = f"{home_score}-{away_score}"
        new_score_size = find_max_font_size(score_text, settings.SCORE_TXT_SIZE, screen_width,
                                            max_iterations=100)
        new_hyphen_size = settings.HYPHEN_SIZE + (new_score_size - settings.SCORE_TXT_SIZE - 10)

        window["home_score"].update(font=(settings.FONT, new_score_size))
        window["away_score"].update(font=(settings.FONT, new_score_size))
        window["hyphen"].update(font=(settings.FONT, new_hyphen_size))
        log_entries.append(f"score: {settings.SCORE_TXT_SIZE}->{new_score_size}, "
                           f"hyphen: {settings.HYPHEN_SIZE}->{new_hyphen_size}")

        # Update timeouts text if present
        if "home_timeouts" in team_info:
            size = settings.TIMEOUT_SIZE if team_league != "NBA" else settings.NBA_TIMEOUT_SIZE
            timeout_text = ("\u25CF  \u25CF  \u25CF  \u25CF  \u25CF  \u25CF  \u25CF"
                            if team_league == "NBA" else "\u25CF  \u25CF  \u25CF")
            new_timeout_size = find_max_font_size(timeout_text, size, screen_width, max_iterations=50, buffer=1.4)

            window["home_timeouts"].update(font=(settings.FONT, new_timeout_size))
            window["away_timeouts"].update(font=(settings.FONT, new_timeout_size))
            log_entries.append(f"timeouts_txt: {size}->{new_timeout_size}")

        # Update above score text if present
        if "above_score_txt" in team_info:
            text = team_info.get("above_score_txt", "")
            if text:
                if "@" in text:
                    screen_width = Sg.Window.get_screen_size()[0] / 4
                    size = settings.NOT_PLAYING_TOP_INFO_SIZE
                else:
                    screen_width = (Sg.Window.get_screen_size()[0] / 3) / 2
                    size = settings.TOP_TXT_SIZE

                new_size = find_max_font_size(text, size, screen_width, max_iterations=50)
                window["above_score_txt"].update(font=(settings.FONT, new_size))
                log_entries.append(f"above_score_txt: {size}->{new_size}")

        if log_entries:
            logger.info("Increased Size: %s", ", ".join(log_entries))

    finally:
        root.destroy()
