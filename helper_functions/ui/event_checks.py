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
from adafruit_ticks import ticks_ms  # type: ignore[import]

import settings
from constants import colors, messages, ui_keys
from gui_layouts import main_screen_layout
from gui_layouts.change_functionality_popup import show_scoreboard_popup
from helper_functions.logging.logger_config import logger
from helper_functions.ui.scoreboard_helpers import will_text_fit_on_screen
from screens import main_screen, scoreboard_screen


def _manually_change_team(
    window: Sg.Window,
    event: str,
    team_status: scoreboard_screen.TeamStatus | None,
    state: scoreboard_screen.DisplayState,
    team_info: list[dict],
) -> None:
    """Manually change the team being displayed."""
    if team_status is None:
        return

    info = ""
    changed_team = False

    is_visible = window["home_stats_section"].visible or window["away_stats_section"].visible
    if is_visible:
        logger.info("Cannot switch teams while team stats are visible")
        return

    number_of_teams = len(settings.teams)
    # Only restrict to live teams when more than one is live; otherwise allow switching across teams with data
    prefer_playing = settings.prioritize_playing_team and sum(team_status.teams_currently_playing) >= 1
    teams_filter = team_status.teams_currently_playing if prefer_playing else team_status.teams_with_data

    step = 1 if ui_keys.HOME_RECORD in event else -1  # Next or previous
    new_index = state.display_index

    for i in range(1, number_of_teams + 1):
        candidate = (state.display_index + step * i) % number_of_teams
        if teams_filter[candidate]:
            new_index = candidate
            break

    if new_index != state.display_index:
        if (step == -1 and state.display_index != state.original_index and
            team_status.teams_with_data[state.original_index]):
            state.display_index = state.original_index
        else:
            state.original_index = state.display_index
            state.display_index = new_index

        info = f"Switching to team: {settings.teams[state.display_index][0]}"
        window[ui_keys.BOTTOM_INFO].update(
            value=info,
            font=(settings.FONT, settings.NOT_PLAYING_TOP_INFO_SIZE),
        )
        logger.info(f"\nManually switched to team: {settings.teams[state.display_index][0]}\n"
                    f"Was on team index {state.original_index}, now on {state.display_index}\n",
                    )

        state.display_clock = ticks_ms()
        changed_team = True
    else:
        feedback_info = "Cannot switch teams"
        if prefer_playing and sum(team_status.teams_currently_playing) <= 1:
            info = "This is the only team currently playing (prioritize playing team is enabled)"
        elif sum(team_status.teams_with_data) <= 1:
            info = "This is the only team with data available"
        else:
            info = "No other eligible teams found"

        window[ui_keys.TOP_INFO].update(
            value=feedback_info,
            font=(settings.FONT, settings.NOT_PLAYING_TOP_INFO_SIZE),
        )
        window[ui_keys.BOTTOM_INFO].update(
            value=info,
            font=(settings.FONT, settings.NOT_PLAYING_TOP_INFO_SIZE),
        )
        logger.info(f"Cannot Switch Team - {info}")
        wait(window, 3, team_status=team_status, state=state, team_info=team_info)  # Pause, let user read message

    if info and will_text_fit_on_screen(info, txt_size=settings.NOT_PLAYING_TOP_INFO_SIZE):
        scroll(window, info, team_status=team_status, state=state, team_info=team_info)

    if changed_team and len(team_info) == len(settings.teams):
        # Force an immediate display update on manual switch (even mid-cycle)
        currently_playing_flag = bool(team_status.teams_currently_playing[state.display_index])
        scoreboard_screen.update_display(
            window,
            team_info,
            state.display_index,
            currently_playing=currently_playing_flag,
        )

        if will_text_fit_on_screen(team_info[state.display_index].get(ui_keys.BOTTOM_INFO, "")):
            scroll(
                window,
                team_info[state.display_index][ui_keys.BOTTOM_INFO],
                team_status=team_status,
                state=state,
                team_info=team_info,
            )

        state.update_clock = ticks_ms()
        state.display_clock = ticks_ms()
        state.display_first_time = False


def __toggle_stay_on_team(window: Sg.Window, event: str, team_status: scoreboard_screen.TeamStatus, *,
                          currently_playing: bool) -> None:
    """Toggle the stay on team feature."""
    if sum(team_status.teams_with_data) <= 1 and settings.stay_on_team:
        top_msg = f"{sum(team_status.teams_with_data)} team(s) have game information to display"
        bottom_msg = "Stay on team feature cannot be used when rotating is not possible"
        settings.stay_on_team = False
        window[ui_keys.TOP_INFO].update(value=top_msg, font=(settings.FONT, settings.NOT_PLAYING_TOP_INFO_SIZE))
        window[ui_keys.BOTTOM_INFO].update(value=bottom_msg,
                                            font=(settings.FONT, settings.NOT_PLAYING_TOP_INFO_SIZE))
        logger.info(top_msg + ", " + bottom_msg)
        window.refresh()

    if sum(team_status.teams_currently_playing) == 1 and settings.stay_on_team and settings.prioritize_playing_team:
        top_msg = "Only one team has live game, 'Prioritize Playing Team' is enabled in settings"
        bottom_msg = "Stay on team feature cannot be used when rotating is not possible"
        settings.stay_on_team = False
        window[ui_keys.TOP_INFO].update(value=top_msg, font=(settings.FONT, settings.NOT_PLAYING_TOP_INFO_SIZE))
        window[ui_keys.BOTTOM_INFO].update(value=bottom_msg,
                                            font=(settings.FONT, settings.NOT_PLAYING_TOP_INFO_SIZE))
        logger.info(top_msg + ", " + bottom_msg)
        window.refresh()

    else:
        settings.stay_on_team = not settings.stay_on_team
        rotating_time = settings.DISPLAY_NOT_PLAYING_TIMER if currently_playing else settings.DISPLAY_PLAYING_TIMER
        msg = (
            messages.STAYING_ON_TEAM
            if settings.stay_on_team
            else f"{messages.ROTATING_TEAMS} {rotating_time} seconds"
        )
        window[ui_keys.BOTTOM_INFO].update(value=msg,
                                    font=(settings.FONT, settings.NOT_PLAYING_TOP_INFO_SIZE))
        logger.info("%s key pressed, %s", event, msg)

    time.sleep(3)


def __toggle_menu(window: Sg.Window) -> None:
    """Show the change functionality popup and handle changes."""
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
    # Stop scoreboard background thread if running
    from helper_functions.ui.fetch_data_thread import stop_background_thread
    stop_background_thread()
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

    # Stop scoreboard background thread if running
    from helper_functions.ui.fetch_data_thread import stop_background_thread
    stop_background_thread()

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


def _toggle_team_stats(
    window: Sg.Window,
    team: str,
    team_status: scoreboard_screen.TeamStatus,
    state: scoreboard_screen.DisplayState,
    *,
    event: str,
) -> None:
    """Temporarily show team stats instead of the logo."""
    logger.info("%s key pressed, displaying team info", event)

    currently_playing = team_status.teams_currently_playing[state.display_index]
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
    wait(window, 10, state=state, team_status=team_status)
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
        time.sleep(3)

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
        time.sleep(3)

    if event == Sg.WIN_CLOSED or "Escape" in event:
        go_to_main_screen(window)


def check_events(
    window: Sg.Window,
    events: list | str,
    *,
    team_status: scoreboard_screen.TeamStatus | None = None,
    state: scoreboard_screen.DisplayState | None = None,
    team_info: list[dict] | None = None,
) -> None:
    """Handle button and keyboard events on the scoreboard screen."""
    if team_status is None or state is None:
        return
    currently_playing = team_status.teams_currently_playing[state.display_index]

    # Sanitize event input
    if isinstance(events, (list, tuple)) and events:
        event_raw = str(events[0])
    elif isinstance(events, str):
        event_raw = events
    else:
        event_raw = ""
    event = event_raw.split(":")[0] if ":" in event_raw else event_raw

    menu_triggers = (ui_keys.AWAY_SCORE, ui_keys.HOME_SCORE, ui_keys.AWAY_TIMEOUTS,
                     ui_keys.HOME_TIMEOUTS, ui_keys.ABOVE_SCORE_TXT,
                     )
    if any(key in event for key in menu_triggers):
        __toggle_menu(window)

    if any(key in event for key in (ui_keys.AWAY_LOGO, ui_keys.AWAY_TEAM_STATS)):
        _toggle_team_stats(window, "away", team_status, state, event=event)

    if any(key in event for key in (ui_keys.HOME_LOGO, ui_keys.HOME_TEAM_STATS)):
        _toggle_team_stats(window, "home", team_status, state, event=event)

    if any(key in event for key in (ui_keys.HOME_RECORD, ui_keys.AWAY_RECORD)):
        _manually_change_team(window, event, team_status, state, team_info)

    if any(key in event for key in (ui_keys.TOP_INFO, ui_keys.BOTTOM_INFO)):
        __toggle_stay_on_team(window, event, team_status, currently_playing=currently_playing)

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


def scroll(window: Sg.Window, original_text: str, key: str = ui_keys.BOTTOM_INFO, *,  # noqa: PLR0913
           team_status: object = None, state: object = None, team_info: list | None = None) -> None:
    """Scroll the display to show the next set of information while checking for manual team changes."""
    text = original_text + "         "
    for i in range(2):
        for _ in range(len(text)):
            event = window.read(timeout=100)
            text = text[1:] + text[0]

            if event[0] != Sg.TIMEOUT_KEY:
                check_events(window, event, team_status=team_status, state=state, team_info=team_info)
                if event[0] not in ("top_info", "bottom_info", "away_record", "home_record"):
                    logger.info("%s key pressed, restored original text", event[0])
                else:
                    return

            if settings.no_spoiler_mode:
                set_spoiler_mode(window, {})
                window.refresh()
                break

            window[key].update(value=text)

        if i == 0:
            window[key].update(value=original_text)
            wait(window, 5, team_status=team_status, state=state, team_info=team_info)


def wait(window: Sg.Window, time_waiting: int, *, team_status: object = None,
         state: object = None, team_info: list | None = None) -> None:
    """Wait while still servicing events."""
    for _ in range(int(time_waiting / 0.2)):
        event = window.read(timeout=0.1)
        check_events(window, event, team_status=team_status, state=state, team_info=team_info)
        time.sleep(0.1)
