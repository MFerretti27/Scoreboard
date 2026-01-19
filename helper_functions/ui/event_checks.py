"""Event handling helpers for scoreboard screens."""
from __future__ import annotations

import gc
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import FreeSimpleGUI as Sg  # type: ignore[import]
import orjson  # type: ignore[import]

import settings
from constants import colors, messages, ui_keys
from gui_layouts import main_screen_layout
from gui_layouts.change_functionality_popup import show_scoreboard_popup
from helper_functions.logging.logger_config import logger
from screens import main_screen


def convert_paths_to_strings(obj: object) -> object:
    """Recursively convert Path and datetime objects in a nested structure to strings."""
    if isinstance(obj, dict):
        return {k: convert_paths_to_strings(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [convert_paths_to_strings(i) for i in obj]
    if isinstance(obj, Path):
        return str(obj)
    if isinstance(obj, datetime):
        return obj.isoformat()

    return obj


def go_to_main_screen_hard(window: Sg.Window) -> None:
    """Close current window and launch main screen module via subprocess."""
    window.close()
    gc.collect()
    time.sleep(0.5)
    json_ready_data = convert_paths_to_strings(settings.saved_data)
    settings.write_settings({"saved_data": json_ready_data})
    json_saved_data = orjson.dumps(json_ready_data).decode("utf-8")
    subprocess.Popen([sys.executable, "-m", "screens.main_screen", "--saved-data", json_saved_data])
    sys.exit()

def go_to_main_screen(window: Sg.Window) -> None:
    """Close current window and launch main screen window."""
    window_width = Sg.Window.get_screen_size()[0]
    window_height = Sg.Window.get_screen_size()[1]
    main_column = Sg.Frame("",
        main_screen_layout.create_main_layout(window_width),
        key="MAIN",
        size=(window_width, window_height),
        border_width=0,
    )

    layout = [[Sg.Column([[main_column]], key="VIEW_CONTAINER")]]
    new_window = Sg.Window("Scoreboard", layout, size=(window_width, window_height), resizable=True, finalize=True,
                       return_keyboard_events=True, alpha_channel=0).Finalize()

    window.close()
    gc.collect()  # Clean up memory

    # Fade in the new window
    fade_duration = 300  # milliseconds
    fade_steps = 20
    step_duration = fade_duration / fade_steps
    for step in range(fade_steps):
        alpha = (step + 1) / fade_steps
        new_window.set_alpha(alpha)
        new_window.read(timeout=int(step_duration))

    main_screen.main(new_window, settings.saved_data)


def _toggle_team_stats(window: Sg.Window, team: str, *, currently_playing: bool, event: str) -> None:
    """Temporarily show team stats instead of the logo."""
    logger.info("%s key pressed, displaying team info", event)

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


def check_keyboard_events(window: Sg.Window, event: str) -> None:
    """Handle basic keyboard events like exit, delay toggle, and spoiler mode toggle."""
    if event == Sg.WIN_CLOSED or "Escape" in event:
        go_to_main_screen(window)

    delay_triggers = ("Left", "Right")
    if any(key in event for key in delay_triggers):
        settings.delay = not settings.delay
        msg = (
            messages.DELAY_TURNING_OFF
            if not settings.delay
            else f"{messages.DELAY_TURNING_ON} ({settings.LIVE_DATA_DELAY} seconds)"
        )
        logger.info("%s key pressed, %s", event, msg)
        window[ui_keys.BOTTOM_INFO].update(value=msg)
        window.refresh()
        time.sleep(5)

    spoiler_triggers = ("Up", "Down")
    if any(key in event for key in spoiler_triggers):
        settings.no_spoiler_mode = not settings.no_spoiler_mode
        msg = messages.ENTERING_SPOILER if settings.no_spoiler_mode else messages.EXITING_SPOILER
        logger.info("%s key pressed, %s", event, msg)
        if settings.no_spoiler_mode:
            window = set_spoiler_mode(window, {})
        else:
            window[ui_keys.TOP_INFO].update(value="")
            window[ui_keys.BOTTOM_INFO].update(value=messages.EXITING_SPOILER)
        window.refresh()
        time.sleep(5)


def check_events(window: Sg.Window, events: list | str, *, currently_playing: bool = False) -> None:
    """Handle button and keyboard events on the scoreboard screen."""
    if isinstance(events, (list, tuple)) and events:
        event_raw = str(events[0])
    elif isinstance(events, str):
        event_raw = events
    else:
        event_raw = ""
    event = event_raw.split(":")[0] if ":" in event_raw else event_raw

    if event == Sg.WIN_CLOSED or "Escape" in event:
        go_to_main_screen(window)

    spoiler_triggers = (
        ui_keys.AWAY_SCORE,
        ui_keys.HOME_SCORE,
        ui_keys.AWAY_TIMEOUTS,
        ui_keys.HOME_TIMEOUTS,
        ui_keys.ABOVE_SCORE_TXT,
    )
    if any(key in event for key in spoiler_triggers):
        temp_spoiler = settings.no_spoiler_mode
        temp_delay = settings.delay
        action = show_scoreboard_popup()
        if action == "MENU":
            go_to_main_screen(window)
        if settings.no_spoiler_mode:
            logger.info(messages.ENTERING_SPOILER)
            window = set_spoiler_mode(window, {})
        elif temp_spoiler != settings.no_spoiler_mode:
            logger.info(messages.EXITING_SPOILER)
            window[ui_keys.TOP_INFO].update(value="")
            window[ui_keys.BOTTOM_INFO].update(value=messages.EXITING_SPOILER)
        if temp_delay != settings.delay:
            logger.info("Toggling Delay Mode")
            msg = (
                f"{messages.DELAY_TURNING_ON} ({settings.LIVE_DATA_DELAY} seconds)"
                if settings.delay
                else messages.DELAY_TURNING_OFF
            )
            window[ui_keys.TOP_INFO].update(value=msg)
        window.refresh()

    if any(key in event for key in (ui_keys.AWAY_LOGO, ui_keys.AWAY_TEAM_STATS)):
        _toggle_team_stats(window, "away", currently_playing=currently_playing, event=event)

    if any(key in event for key in (ui_keys.HOME_LOGO, ui_keys.HOME_TEAM_STATS)):
        _toggle_team_stats(window, "home", currently_playing=currently_playing, event=event)

    stay_on_team_triggers = (ui_keys.TOP_INFO, ui_keys.BOTTOM_INFO)
    if any(key in event for key in stay_on_team_triggers):
        settings.stay_on_team = not settings.stay_on_team
        rotating_time = settings.DISPLAY_NOT_PLAYING_TIMER if currently_playing else settings.DISPLAY_PLAYING_TIMER
        msg = (
            messages.STAYING_ON_TEAM
            if settings.stay_on_team
            else f"{messages.ROTATING_TEAMS} {rotating_time} seconds"
        )
        logger.info("%s key pressed, %s", event, msg)
        window[ui_keys.BOTTOM_INFO].update(value=msg)
        window.refresh()
        time.sleep(5)

    check_keyboard_events(window, event)


def set_spoiler_mode(window: Sg.Window, team_info: dict) -> Sg.Window:
    """Set screen to spoiler mode, hiding all data that can spoil game."""
    window[ui_keys.TOP_INFO].update(value=messages.WILL_NOT_DISPLAY, font=(settings.FONT,
                                                                          settings.NOT_PLAYING_TOP_INFO_SIZE))
    window[ui_keys.BOTTOM_INFO].update(value=messages.NO_SPOILER_ON, font=(settings.FONT, settings.INFO_TXT_SIZE))
    window[ui_keys.UNDER_SCORE_IMAGE].update(filename="")
    if "@" not in team_info.get("above_score_txt", ""):
        window[ui_keys.ABOVE_SCORE_TXT].update(value="")
    window[ui_keys.HOME_SCORE].update(value=" ", text_color=colors.TEXT_WHITE)
    window[ui_keys.AWAY_SCORE].update(value=" ", text_color=colors.TEXT_WHITE)
    window[ui_keys.HYPHEN].update(value="", text_color=colors.TEXT_WHITE)
    window[ui_keys.HOME_TIMEOUTS].update(value="")
    window[ui_keys.AWAY_TIMEOUTS].update(value="")
    window[ui_keys.HOME_RECORD].update(value="")
    window[ui_keys.AWAY_RECORD].update(value="")

    window[ui_keys.HOME_PLAYER_STATS].update(value="")
    window[ui_keys.AWAY_PLAYER_STATS].update(value="")

    window[ui_keys.PLAYER_STATS_CONTENT].update(visible=False)
    window[ui_keys.UNDER_SCORE_IMAGE_COLUMN].update(visible=False)
    window[ui_keys.TIMEOUTS_CONTENT].update(visible=False)

    return window


def scroll(window: Sg.Window, original_text: str, key: str = ui_keys.BOTTOM_INFO) -> None:
    """Scroll the display to show the next set of information."""
    text = original_text + "         "
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


def wait(window: Sg.Window, time_waiting: int, *, currently_playing: bool = False) -> None:
    """Wait while still servicing events."""
    for _ in range(int(time_waiting / 0.2)):
        event = window.read(timeout=0.1)
        check_events(window, event, currently_playing=currently_playing)
        time.sleep(0.1)
