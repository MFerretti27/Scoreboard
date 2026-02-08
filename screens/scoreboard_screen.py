"""Script to Display a Scoreboard for your Favorite Teams."""
from __future__ import annotations

import contextlib
import copy
import json
import logging
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import FreeSimpleGUI as Sg  # type: ignore[import]
from adafruit_ticks import ticks_diff, ticks_ms  # type: ignore[import]

import helper_functions.ui.fetch_data_thread as fetch_data_thread_mod
import settings
from constants import colors, ui_keys
from get_data.get_espn_data import get_data
from gui_layouts import scoreboard_layout
from helper_functions.core.handle_error import handle_error
from helper_functions.logging.logger_config import logger
from helper_functions.system.internet_connection import is_connected, reconnect
from helper_functions.system.update import auto_update
from helper_functions.ui.event_checks import check_events, scroll, set_spoiler_mode
from helper_functions.ui.fetch_data_thread import (
    background_fetch_loop,
    get_display_data_from_thread,
)
from helper_functions.ui.scoreboard_helpers import (
    count_lines,
    increase_text_size,
    maximize_screen,
    reset_window_elements,
    will_text_fit_on_screen,
)
from screens.clock_screen import clock

logging.getLogger("httpx").setLevel(logging.WARNING)  # Ignore httpx logging in terminal

# Constants
MILLISECONDS_PER_SECOND = 1000
PLAYING_GAME_FETCH_INTERVAL_MS = 3000
SMALL_SCREEN_WIDTH_THRESHOLD = 1300
READ_TIMEOUT_MS = 100  # Reduced from 2000ms to 100ms for more responsive user input
SCORE_STATE_STYLES = [
    ("power_play", {"text_color": colors.POWER_PLAY_BLUE}),
    ("bonus", {"text_color": colors.BONUS_ORANGE}),
    ("possession", {"font": (settings.FONT, settings.SCORE_TXT_SIZE, "underline")}),
    ("redzone", {"font": (settings.FONT, settings.SCORE_TXT_SIZE, "underline"), "text_color": colors.SPORTS_RED}),
]

# Module-level state
saved_delay_data: list[list[dict[str, Any]]] = []  # Used to store delayed data
show_home_stats_next: bool = True  # Track which player stats to show on small screens

# Global thread control
fetch_thread_should_run: bool = False
fetch_thread: threading.Thread | None = None

@dataclass
class DisplayState:
    """Manage display state and timing information."""

    display_index: int = 0
    display_clock: int = 0
    update_clock: int = 0
    fetch_clock: int = 0
    delay_clock: int = 0
    display_first_time: bool = True
    fetch_first_time: bool = True
    delay_over: bool = False
    delay_started: bool = False
    original_index: int = 0

    def __post_init__(self) -> None:
        """Initialize timing clocks."""
        current_time = ticks_ms()
        self.display_clock = current_time
        self.update_clock = current_time
        self.fetch_clock = current_time
        self.delay_clock = current_time


@dataclass
class TeamStatus:
    """Bundle team state collections to reduce parameter count."""

    teams_with_data: list[bool]
    teams_currently_playing: list[bool]


def find_next_team_to_display(teams_currently_playing: list[bool],
                              display_index: int, teams_with_data: list[bool]) -> tuple[int, int]:
    """Find the next team to display.

    :param teams_currently_playing: List of currently playing teams
    :param display_index: Index of the team to display
    :param teams_with_data: List of teams with data

    :return: Index of the next team to display
    """
    original_index = display_index
    number_of_teams = len(settings.teams)

    if settings.stay_on_team:
        logger.info(
            f"Not Switching teams, staying on {settings.teams[display_index][0]}\n")
        return original_index, original_index

    teams_filter = (teams_currently_playing if settings.prioritize_playing_team and any(teams_currently_playing)
                    else teams_with_data)
    filter_desc = "currently playing" if teams_filter is teams_currently_playing else "with data"
    logger.info(f"Looking for next team {filter_desc}\n")

    for x in range(number_of_teams * 2):
        current_idx = (original_index + x) % number_of_teams

        if not teams_filter[current_idx]:
            display_index = (display_index + 1) % number_of_teams
            logger.info(f"skipping displaying {settings.teams[current_idx][0]}")
        elif x != 0:
            logger.info(f"Found next team to display {settings.teams[current_idx][0]}\n")
            display_index = current_idx
            break

    return display_index, original_index


def _update_team_elements(window: Sg.Window, current_team: dict, score_state_fields: set, display_index: int) -> None:
    """Update individual team elements in the window.

    :param window: The window element to update
    :param current_team: The current team information dictionary
    :param score_state_fields: Set of score state field names to skip
    :param display_index: The index of the team to update
    """
    for key, value in current_team.items():
        if key in (ui_keys.HOME_LOGO, ui_keys.AWAY_LOGO, ui_keys.UNDER_SCORE_IMAGE):
            window[key].update(filename=value)
        elif key == ui_keys.SIGNATURE:
            window[key].update(value=value, text_color=colors.SPORTS_RED)
        elif (
            ui_keys.HOME_TIMEOUTS in key or ui_keys.AWAY_TIMEOUTS in key
        ) and (settings.teams[display_index][1] != "MLB"):
            window[key].update(value=value, text_color=colors.TIMEOUT_YELLOW)
        elif key not in score_state_fields:
            window[key].update(value=value)


def _update_score_states(window: Sg.Window, current_team: dict) -> None:
    """Update score display based on game states (power play, bonus, possession, redzone).

    :param window: The window element to update
    :param current_team: The current team information dictionary
    """
    for state, props in SCORE_STATE_STYLES:
        if current_team.get(f"home_{state}", False):
            window[ui_keys.HOME_SCORE].update(**props)
        elif current_team.get(f"away_{state}", False):
            window[ui_keys.AWAY_SCORE].update(**props)


def _update_player_stats(window: Sg.Window, current_team: dict,
                         display_index: int, *, show_home: bool) -> None:
    """Update player stats display for small screens.

    :param window: The window element to update
    :param current_team: The current team information dictionary
    :param display_index: The index of the team to update
    :param show_home: Whether to show home stats next
    """
    home_stats = current_team.get("home_player_stats", "")
    away_stats = current_team.get("away_player_stats", "")
    # NFL stats only have one column, so it can take up whole width
    stats_width = 60 if settings.teams[display_index][1] == "NFL" else 27

    if Sg.Window.get_screen_size()[0] < SMALL_SCREEN_WIDTH_THRESHOLD:
        if show_home and settings.teams[display_index][1] != "NFL":
            window[ui_keys.AWAY_PLAYER_STATS].update(value=home_stats)
        else:
            window[ui_keys.AWAY_PLAYER_STATS].update(value=away_stats)

        stats_width = 60  # Small screens only have one column

    # Change the height of the player stats box based on number of lines
    home_lines = count_lines(home_stats) + 1
    away_lines = count_lines(away_stats) + 1

    window[ui_keys.HOME_PLAYER_STATS].set_size(size=(stats_width, home_lines))
    window[ui_keys.AWAY_PLAYER_STATS].set_size(size=(stats_width, away_lines))


def _update_visibility(window: Sg.Window, current_team: dict, *,
                       currently_playing: bool) -> None:
    """Update visibility of player stats and timeout sections.

    :param window: The window element to update
    :param current_team: The current team information dictionary
    :param currently_playing: Whether the team is currently playing
    """
    has_home_stats = bool(current_team.get("home_player_stats", ""))
    has_away_stats = bool(current_team.get("away_player_stats", ""))
    show_stats = has_home_stats or has_away_stats

    if settings.display_player_stats and show_stats:
        window[ui_keys.PLAYER_STATS_CONTENT].update(visible=True)
        window[ui_keys.UNDER_SCORE_IMAGE_COLUMN].update(visible=False)
    elif current_team.get("under_score_image", ""):
        window[ui_keys.UNDER_SCORE_IMAGE_COLUMN].update(visible=True)
        window[ui_keys.PLAYER_STATS_CONTENT].update(visible=False)
    else:
        window[ui_keys.PLAYER_STATS_CONTENT].update(visible=False)
        window[ui_keys.UNDER_SCORE_IMAGE_COLUMN].update(visible=False)

    window[ui_keys.TIMEOUTS_CONTENT].update(visible=currently_playing)


def update_display(window: Sg.Window, team_info: list[dict], display_index: int, *, currently_playing: bool) -> None:
    """Update the display for a specific team.

    :param window: The window element to update
    :param team_info: The team information dictionary
    :param display_index: The index of the team to update

    :return: None
    """
    global show_home_stats_next
    filter_desc = "is currently playing" if currently_playing else "has data"
    logger.info(f"\n{settings.teams[display_index][0]} {filter_desc}, updating display")
    sport_league = settings.teams[display_index][1]
    current_team = team_info[display_index]
    reset_window_elements(window)

    score_state_fields = {f"{side}_{state}" for state, _ in SCORE_STATE_STYLES for side in ("home", "away")}

    _update_team_elements(window, current_team, score_state_fields, display_index)
    _update_score_states(window, current_team)

    _update_player_stats(window, current_team, display_index, show_home=show_home_stats_next)
    _update_visibility(window, current_team, currently_playing=currently_playing)

    if settings.no_spoiler_mode:
        set_spoiler_mode(window, current_team)

    increase_text_size(window, current_team, sport_league.upper(), currently_playing=currently_playing)

    show_home_stats_next = not show_home_stats_next


def _should_rotate_team(state: DisplayState, display_timer: int) -> bool:
    """Determine if team rotation should occur based on timing."""
    return ticks_diff(ticks_ms(), state.display_clock) >= display_timer or state.display_first_time



def _handle_update_cycle(
    window: Sg.Window,
    team_info: list[dict[str, Any]],
    state: DisplayState,
    team_status: TeamStatus | None = None,
) -> dict[str, Any]:
    """Execute display update cycle and return currently displaying team info."""
    currently_displaying: dict[str, Any] = {}

    if team_status is not None and team_status.teams_with_data[state.display_index]:
        update_display(window, team_info, state.display_index,
                       currently_playing=team_status.teams_currently_playing[state.display_index])
        currently_displaying = team_info[state.display_index]

        if will_text_fit_on_screen(team_info[state.display_index].get(ui_keys.BOTTOM_INFO, "")):
            scroll(window, team_info[state.display_index][ui_keys.BOTTOM_INFO],
                   team_status=team_status, state=state, team_info=team_info)

    state.update_clock = ticks_ms()

    return currently_displaying


def _handle_rotation_cycle(
    state: DisplayState,
    teams_with_data: list[bool],
    teams_currently_playing: list[bool],
) -> None:
    """Execute team rotation cycle."""
    if teams_with_data[state.display_index]:
        state.display_first_time = False
        state.display_index, state.original_index = find_next_team_to_display(
            teams_currently_playing, state.display_index, teams_with_data)
        state.display_clock = ticks_ms()
    else:
        logger.info(f"\nTeam doesn't have data {settings.teams[state.display_index][0]}")
        state.display_index = (state.display_index + 1) % len(settings.teams)
        logger.info(f"Rest of teams: {teams_with_data}\n")


def check_thread_health(window: Sg.Window, stop_event: threading.Event) -> None:
    """Check if background fetch thread is alive and making progress, restart if not.

    :param window: The window element to update
    """
    global fetch_thread_should_run, fetch_thread
    # Check if thread is dead
    if fetch_thread is None or not fetch_thread.is_alive():
        fetch_thread_should_run = True
        logger.error("Background fetch thread has stopped unexpectedly.")
        fetch_thread = threading.Thread(target=background_fetch_loop, args=(stop_event,), daemon=True)
        fetch_thread.start()
        logger.info("Restarted background fetch thread.")
        wait_for_thread(window)
    else:
        # Heartbeat check: if no progress in 30 seconds, consider stuck
        now = time.time()
        heartbeat = getattr(fetch_data_thread_mod, "fetch_thread_heartbeat", 0)
        if heartbeat and now - heartbeat > 300:
            logger.error(f"Background fetch thread appears stuck (no heartbeat for {int(now-heartbeat)}s). Restarting.")
            fetch_thread_should_run = False
            with contextlib.suppress(Exception):
                fetch_thread.join(timeout=2)
            fetch_thread_should_run = True
            fetch_thread = threading.Thread(target=background_fetch_loop, args=(stop_event,), daemon=True)
            fetch_thread.start()
            logger.info("Restarted background fetch thread after no data was fetched after 5 minutes.")
            wait_for_thread(window)


def wait_for_thread(window: Sg.Window, wait_time_limit: float = 10.0) -> None:
    """Wait for background fetch thread to start.

    :param window: The window element to update
    :param wait_time_limit: Maximum time to wait for thread to start in seconds
    """
    wait_time: float = 0.0
    while (fetch_thread is None or not fetch_thread.is_alive()) and wait_time < wait_time_limit:
        time.sleep(0.1)
        wait_time += 0.1

    if fetch_thread is not None and fetch_thread.is_alive():
        logger.info("Background fetch thread started successfully.")
    else:
        logger.error("Background fetch thread failed to start within expected time.")
        clock(window, message="Error fetching data...")


def handle_resume_from_sleep(window: Sg.Window) -> None:
    """Handle system resume from sleep by running recovery logic.

    :param window: The window element to update
    """
    logger.info("Detected system resume, running recovery logic.")
    # 1. Check and restore internet connection
    if not is_connected():
        reconnect()
    # 2. Restart threads/timers if needed (depends on your architecture)
    # 3. Optionally clear/refresh cache
    # 4. Force data refresh for all teams
    for team in settings.teams:
        try:
            get_data(team)
        except Exception as e:
            logger.warning(f"Failed to refresh data for {team[0]} after resume: {e}")
    # 5. Update UI
    window.refresh()

##################################
#                                #
#        Main Event Loop         #
#                                #
##################################

def main(window: Sg.Window) -> None:
    """Run the scoreboard application with background fetch."""
    global fetch_thread_should_run

    # Reset UI flags
    settings.stay_on_team = False
    settings.no_spoiler_mode = False

    # Start background fetch thread
    fetch_thread_should_run = True  # Set flag to run thread
    stop_event = threading.Event()  # Event to signal error and to stop
    fetch_thread = threading.Thread(target=background_fetch_loop, args=(stop_event,), daemon=True)
    fetch_thread.start()

    state = DisplayState()
    currently_displaying: dict = {}
    team_info: list[dict[str, Any]] = []  # Always defined for error handling
    maximize_screen(window)

    last_time = time.time()

    while True:
        now = time.time()
        if now - last_time > 10:  # 10 seconds is a typical threshold
            handle_resume_from_sleep(window)
        last_time = now
        try:
            event = window.read(timeout=5000)

            # Ensure background thread is running
            check_thread_health(window, stop_event)

            if stop_event.is_set():
                logger.info("Background fetch thread reported an error, handling recovery.")
                handle_error(window, team_info=team_info)
                stop_event.clear()

            # Read latest data from background thread
            teams_with_data, team_info, teams_currently_playing = get_display_data_from_thread()

            # Defensive: skip loop if teams/settings mismatch
            if not settings.teams or not team_info or len(settings.teams) == 0 or len(team_info) != len(settings.teams):
                logger.warning("settings.teams or team_info is empty or mismatched; skipping display update.")
                time.sleep(0.2)
                continue

            team_status = TeamStatus(teams_with_data=teams_with_data, teams_currently_playing=teams_currently_playing)

            # Defensive: clamp display_index to valid range
            if state.display_index >= len(settings.teams):
                state.display_index = 0
            if state.original_index >= len(settings.teams):
                state.original_index = 0

            # Display Team Information
            currently_displaying = {}
            if team_info and len(team_info) == len(settings.teams):
                currently_displaying = _handle_update_cycle(
                    window, team_info, state, team_status)

            # Find next team to display
            if _should_rotate_team(state, settings.DISPLAY_NOT_PLAYING_TIMER * MILLISECONDS_PER_SECOND):
                _handle_rotation_cycle(state, teams_with_data, teams_currently_playing)

            # Handle events and settings changes
            prev_spoiler_mode, prev_delay = settings.no_spoiler_mode, settings.delay
            check_events(window, event, team_status=team_status, state=state, team_info=team_info)

            if prev_spoiler_mode and not settings.no_spoiler_mode:
                logger.info("No spoiler mode changed, refreshing data")

            if not any(teams_with_data):
                logger.info("\nNo Teams with Data Displaying Clock\n")
                teams_with_data = clock(window, message="No Data For Any Teams")

            if settings.auto_update:
                auto_update(window)

            if settings.delay and prev_delay != settings.delay:
                state.delay_clock = ticks_ms()
                state.delay_over = False

            if (settings.stay_on_team and state.display_index < len(team_info) and
                currently_displaying != team_info[state.display_index]):
                state.display_index = state.original_index

        except Exception as error:
            logger.info(f"Error: {error}")
            handle_error(window, error=error, team_info=team_info)


if __name__ == "__main__":
    saved_data = {}
    settings_saved = None

    args = sys.argv[1:]
    try:
        if "--settings" in args:
            idx = args.index("--settings")
            if idx + 1 < len(args):
                settings_path = Path(args[idx + 1])
                if settings_path.exists():
                    with settings_path.open(encoding="utf-8") as f:
                        settings_saved = json.load(f)
                    settings.write_settings(settings_saved)
                    logger.info("Settings updated and reloaded from JSON: %s", settings_path)
                else:
                    logger.warning("Settings file not found: %s", settings_path)

        if "--saved-data" in args:
            idx = args.index("--saved-data")
            if idx + 1 < len(args):
                raw_data = args[idx + 1]
                if raw_data.strip():  # Make sure it's not empty
                    try:
                        # Load saved data from command line argument
                        saved_data = json.loads(raw_data)
                        settings.saved_data = copy.deepcopy(saved_data)
                        logger.info("Loaded saved_data: %s", list(saved_data.keys()))
                    except json.JSONDecodeError as e:
                        logger.warning("Invalid JSON for --saved-data: %s", e)
                        saved_data = {}
                else:
                    logger.warning("--saved-data argument provided but empty")

    except Exception as e:
        logger.exception("Error parsing startup arguments: %s", e)
        saved_data = {}

    # Create the window with initial alpha of 0 for fade-in effect
    window = Sg.Window("Scoreboard", scoreboard_layout.create_scoreboard_layout(), no_titlebar=False,
                       resizable=True, return_keyboard_events=True, alpha_channel=0).Finalize()
    maximize_screen(window)
    logger.info("Launching scoreboard with saved_data=%s", bool(saved_data))
    main(window)
