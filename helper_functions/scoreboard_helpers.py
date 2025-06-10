"""Module to Create and modify scoreboard GUI using FreeSimpleGUI."""

import gc
import subprocess
import sys
import time
import tkinter as tk
from tkinter import font as tkFont

import FreeSimpleGUI as sg  # type: ignore
import orjson  # type: ignore

import settings


def will_text_fit_on_screen(text: str) -> bool:
    """Check if text will fit on screen.

    :param text: str to compare to width of screen

    :return bool: boolean value representing if string will fit on screen
    """
    screen_width = sg.Window.get_screen_size()[0]  # Get screen width

    root = tk.Tk()
    root.withdraw()  # Hide the root window
    font = tkFont.Font(family=settings.FONT, size=settings.INFO_TXT_SIZE)
    width = font.measure(text)
    width = width * 1.1  # Ensure text fits on screen by adding a buffer
    root.destroy()

    if width >= screen_width:
        print(f"Bottom Text will scroll, text size: {width}, screen size: {screen_width}")
        return True
    else:
        return False


def reset_window_elements(window: sg.Window) -> None:
    """Reset window elements to default values.

    :param window: element that can be updated for displaying information
    """
    window['top_info'].update(value='', font=(settings.FONT, settings.NOT_PLAYING_TOP_INFO_SIZE), text_color='white')
    window['bottom_info'].update(value='', font=(settings.FONT, settings.INFO_TXT_SIZE), text_color='white')
    window['home_timeouts'].update(value='', font=(settings.FONT, settings.TIMEOUT_SIZE), text_color='white')
    window['away_timeouts'].update(value='', font=(settings.FONT, settings.TIMEOUT_SIZE), text_color='white')
    window['home_record'].update(value='', font=(settings.FONT, settings.RECORD_TXT_SIZE), text_color='white')
    window['away_record'].update(value='', font=(settings.FONT, settings.RECORD_TXT_SIZE), text_color='white')
    window['home_score'].update(value='', font=(settings.FONT, settings.SCORE_TXT_SIZE), text_color='white')
    window['away_score'].update(value='', font=(settings.FONT, settings.SCORE_TXT_SIZE), text_color='white')
    window['above_score_txt'].update(value='', font=(settings.FONT, settings.NOT_PLAYING_TOP_INFO_SIZE),
                                     text_color='white')
    window["hyphen"].update(value='-', font=(settings.FONT, settings.HYPHEN_SIZE), text_color='white')


def check_events(window: sg.Window, events, currently_playing=False) -> None:
    """Check for specific key presses.

    :param window: element that can be updated for displaying information
    :param events: key presses that were recorded
    :param currently_playing: current state of scoreboard allowing for more or less key presses
    """
    if events[0] == sg.WIN_CLOSED or 'Escape' in events[0]:
        window.close()
        gc.collect()  # Clean up memory
        time.sleep(0.5)  # Give OS time to destroy the window
        json_saved_data = orjson.dumps(settings.saved_data)
        subprocess.Popen([sys.executable, "-m", "screens.main_screen", json_saved_data])
        sys.exit()

    elif 'Up' in events[0] and not settings.no_spoiler_mode:
        settings.no_spoiler_mode = True
        # Setting window elements will be handled in other functions to continue making sure no spoilers are displayed

    elif 'Down' in events[0] and settings.no_spoiler_mode:
        settings.no_spoiler_mode = False
        window["top_info"].update(value="")
        window["bottom_info"].update(value="Exiting No Spoiler Mode")
        window.refresh()
        time.sleep(2)

    if currently_playing:
        if 'Caps_Lock' in events[0] and not settings.stay_on_team:
            print("Caps Lock key pressed, Staying on team")
            settings.stay_on_team = True
            window["bottom_info"].update(value="Staying on Team")
            window.refresh()
            time.sleep(5)
        elif ('Shift_L' in events[0] or 'Shift_R' in events[0]) and settings.stay_on_team:
            print("shift key pressed, Rotating teams")
            settings.stay_on_team = False
            window["bottom_info"].update(value="Rotating Teams")
            window.refresh()
            time.sleep(5)

    if 'Left' in events[0] and settings.delay:
        print("left key pressed, delay off")
        settings.delay = False
        window["bottom_info"].update(value="Turning delay OFF")
        window.refresh()
        time.sleep(5)
    elif 'Right' in events[0] and not settings.delay:
        print("Right key pressed, delay on")
        settings.delay = True
        window["bottom_info"].update(value=f"Turning delay ON ({settings.LIVE_DATA_DELAY} seconds)")
        window.refresh()
        time.sleep(5)


def set_spoiler_mode(window: sg.Window, team_info: dict) -> sg.Window:
    """Set screen to spoiler mode, hiding all data that can spoil game.

    :param window: element that can be updated for displaying information
    :param currently_playing: boolean value to tell what message to display
    :param team_info: team data that shows if certain elements should be changed so as to not spoil anything

    :return window: element updates for window to change
    """

    window["top_info"].update(value="Will Not Display Game Info", font=(settings.FONT, settings.MLB_BOTTOM_INFO_SIZE))
    window['bottom_info'].update(value="No Spoiler Mode On", font=(settings.FONT, settings.MLB_BOTTOM_INFO_SIZE))
    window["under_score_image"].update(filename='')
    if "@" not in team_info["above_score_txt"]:  # Only remove if text doesn't contain team names
        window["above_score_txt"].update(value='')
    window["home_score"].update(value='0', text_color='white')
    window["away_score"].update(value='0', text_color='white')
    window['home_timeouts'].update(value='')
    window['away_timeouts'].update(value='')
    window['home_record'].update(value='')
    window['away_record'].update(value='')

    return window


def resize_text() -> None:
    """Resize text to fit screen size."""
    window_width = sg.Window.get_screen_size()[0]

    # Common base screen widths
    common_base_widths = [1366, 1920, 1440, 1280]
    # Find the largest base width that doesn't exceed the window width using `max()`
    base_width = max([width for width in common_base_widths if width <= window_width], default=1366)
    scale = window_width / base_width

    print(f"Closest screen size: {base_width}, multiplier: {scale}\n")

    max_size = 200
    settings.SCORE_TXT_SIZE = min(max_size, max(60, int(113 * scale)))
    settings.INFO_TXT_SIZE = min(max_size, max(60, int(68 * scale)))
    settings.RECORD_TXT_SIZE = min(max_size, max(60, int(72 * scale)))
    settings.CLOCK_TXT_SIZE = min(max_size, max(60, int(150 * scale)))
    settings.HYPHEN_SIZE = min(max_size, max(60, int(63 * scale)))
    settings.TIMEOUT_SIZE = min(max_size, max(10, int(26 * scale)))
    settings.NBA_TOP_INFO_SIZE = min(max_size, max(40, int(42 * scale)))
    settings.MLB_BOTTOM_INFO_SIZE = min(max_size, max(60, int(60 * scale)))
    settings.PLAYING_TOP_INFO_SIZE = min(max_size, max(60, int(57 * scale)))
    settings.NOT_PLAYING_TOP_INFO_SIZE = min(max_size, max(20, int(34 * scale)))
    settings.TOP_TXT_SIZE = min(max_size, max(40, int(60 * scale)))
    settings.SIGNATURE_SIZE = min(15, max(8, int(8 * scale)))

    print(f"\nScore txt size:{settings.SCORE_TXT_SIZE}")
    print(f"Info txt size:{settings.INFO_TXT_SIZE}")
    print(f"Record txt size:{settings.RECORD_TXT_SIZE}")
    print(f"Clock txt size:{settings.CLOCK_TXT_SIZE}")
    print(f"Hyphen txt size:{settings.HYPHEN_SIZE}")
    print(f"Timeout txt size:{settings.TIMEOUT_SIZE}")
    print(f"NBA top txt size:{settings.NBA_TOP_INFO_SIZE}")
    print(f"MLB bottom txt size:{settings.MLB_BOTTOM_INFO_SIZE}")
    print(f"Playing txt size:{settings.PLAYING_TOP_INFO_SIZE}")
    print(f"Not playing top txt size:{settings.NOT_PLAYING_TOP_INFO_SIZE}")
    print(f"Top txt size:{settings.TOP_TXT_SIZE}")
    print(f"Signature txt size:{settings.SIGNATURE_SIZE}\n")
