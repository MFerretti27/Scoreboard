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
        logger.info("Bottom Text will scroll, text size: %s, screen size: %s", txt_width, screen_width)
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

    if currently_playing:
        if any(key in event for key in ("Caps_Lock", "away_logo", "away_record")) and not settings.stay_on_team:
            logger.info(f"{event} key pressed, Staying on team")
            settings.stay_on_team = True
            window["bottom_info"].update(value="Staying on Team")
            window.refresh()
            time.sleep(5)
        elif (any(key in event for key in ("Shift_L", "Shift_R", "away_logo", "away_record")) and
              settings.stay_on_team):
            logger.info(f"{event} key pressed, Rotating teams")
            settings.stay_on_team = False
            window["bottom_info"].update(value="Rotating Teams")
            window.refresh()
            time.sleep(5)

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
    settings.INFO_TXT_SIZE = min(max_size, max(20, int(45 * scale)))
    settings.RECORD_TXT_SIZE = min(max_size, max(35, int(65 * scale)))
    settings.CLOCK_TXT_SIZE = min(max_size, max(60, int(150 * scale)))
    settings.HYPHEN_SIZE = min(max_size, max(30, int(50 * scale)))
    settings.TIMEOUT_SIZE = min(max_size, max(18, int(26 * scale)))
    settings.NBA_TOP_INFO_SIZE = min(max_size, max(15, int(30 * scale)))
    settings.NHL_TOP_INFO_SIZE = min(max_size, max(40, int(42 * scale)))
    settings.MLB_BOTTOM_INFO_SIZE = min(max_size, max(60, int(60 * scale)))
    settings.PLAYING_TOP_INFO_SIZE = min(max_size, max(60, int(57 * scale)))
    settings.NOT_PLAYING_TOP_INFO_SIZE = min(max_size, max(10, int(25 * scale)))
    settings.TOP_TXT_SIZE = min(max_size, max(10, int(35 * scale)))
    settings.SIGNATURE_SIZE = min(15, max(6, int(9 * scale)))
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
    for _ in range(2):
        for _ in range(len(text)):
            event = window.read(timeout=100)
            text = text[1:] + text[0]
            window[key].update(value=text)
            check_events(window, event)

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
    screen_width = Sg.Window.get_screen_size()[0] / 3  # Get column width

    home_score = team_info.get("home_score", "0")
    away_score = team_info.get("away_score", "0")

    text = f"{home_score}-{away_score}"

    for i in range(100):
        new_txt_size = settings.SCORE_TXT_SIZE + i
        root = tk.Tk()
        root.withdraw()  # Hide the root window
        font = tk_font.Font(family=settings.FONT, size=new_txt_size)
        txt_width: float = float(font.measure(text))
        txt_width = txt_width * 1.1  # Ensure text fits on screen by adding a buffer
        root.destroy()

        if txt_width > screen_width:
            logger.info("Increasing score text size to: %s from %s", new_txt_size - 1, settings.SCORE_TXT_SIZE)
            logger.info("Increasing hyphen text size to: %s from %s", settings.HYPHEN_SIZE + (i - 10),
                        settings.HYPHEN_SIZE)
            window["home_score"].update(font=(settings.FONT, new_txt_size - 1))
            window["away_score"].update(font=(settings.FONT, new_txt_size - 1))
            window["hyphen"].update(font=(settings.FONT, settings.HYPHEN_SIZE + (i - 10)))
            break

    if "home_timeouts" in team_info:
        screen_width = (Sg.Window.get_screen_size()[0] / 3) / 2  # Get column width

        size = settings.TIMEOUT_SIZE if team_league != "NBA" else settings.NBA_TIMEOUT_SIZE

        nba_max_timeouts_size = "\u25CF  \u25CF  \u25CF  \u25CF  \u25CF  \u25CF  \u25CF"
        nfl_max_timeouts_size = "\u25CF  \u25CF  \u25CF"
        text = nba_max_timeouts_size if team_league == "NBA" else nfl_max_timeouts_size

        for i in range(100):
            new_txt_size = size + i
            root = tk.Tk()
            root.withdraw()  # Hide the root window
            font = tk_font.Font(family=settings.FONT, size=new_txt_size)
            txt_width: float = float(font.measure(text))
            txt_width = txt_width * 1.4  # Ensure text fits on screen by adding a buffer
            root.destroy()

            if txt_width > screen_width:
                logger.info("Increasing timeouts text size to: %s from %s", new_txt_size - 2, settings.TIMEOUT_SIZE)
                window["home_timeouts"].update(font=(settings.FONT, new_txt_size - 2))
                window["away_timeouts"].update(font=(settings.FONT, new_txt_size - 2))
                break

    if "above_score_txt" in team_info:
            text = team_info.get("above_score_txt", "")

            if "@" in text:
                screen_width = (Sg.Window.get_screen_size()[0] / 4)
                size = settings.NOT_PLAYING_TOP_INFO_SIZE
            else:
                screen_width = (Sg.Window.get_screen_size()[0] / 3) / 2
                size = settings.TOP_TXT_SIZE

            for i in range(100):
                new_txt_size = size + i
                root = tk.Tk()
                root.withdraw()  # Hide the root window
                font = tk_font.Font(family=settings.FONT, size=new_txt_size)
                txt_width: float = float(font.measure(team_info["above_score_txt"]))
                txt_width = txt_width * 1.1  # Ensure text fits on screen by adding a buffer
                root.destroy()

                if txt_width > screen_width:
                    logger.info("Increasing above score text size to: %s from %s", new_txt_size - 1, size)
                    window["above_score_txt"].update(font=(settings.FONT, new_txt_size - 1))
                    break

