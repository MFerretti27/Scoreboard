"""Background fetch thread for scoreboard data."""
import copy
import threading
import time

from adafruit_ticks import ticks_diff, ticks_ms  # type: ignore[import]

import settings
from constants import messages, ui_keys
from get_data.get_espn_data import get_data
from helper_functions.logging.logger_config import logger
from helper_functions.ui.store_data_helpers import DisplayState, save_team_data

MILLISECONDS_PER_SECOND = 1000
PLAYING_GAME_FETCH_INTERVAL_MS = 3000

# Module-level buffer for delay logic
saved_delay_data = []

fetch_lock = threading.Lock()
latest_fetch_result = {
    "teams_with_data": [],
    "team_info": [],
    "teams_currently_playing": [],
    "timestamp": 0,
}
fetch_thread_should_run = True

# Global thread handle for cleanup
fetch_thread = None

def update_playing_flags(team_info: list[dict], teams_currently_playing: list[bool]) -> list[bool]:
    """Update the currently playing flags based on delay information not current information.

    :param team_info: List of team information dictionaries
    :param teams_currently_playing: List of teams that are currently playing
    :return: Updated list of teams currently playing
    """
    end_game_keywords = ["delayed", "postponed", "final", "canceled", "delay", " am ", " pm "]
    schedule_keywords = [" am ", " pm "]
    latest_fetch_result: dict[str, list[bool]] = {}

    for index, info in enumerate(team_info):
        if "bottom_info" not in info:
            continue

        bottom_info_lower = str(info["bottom_info"]).lower()
        team_name = settings.teams[index][0]
        has_end_game_keywords = any(kw in bottom_info_lower for kw in end_game_keywords)
        has_schedule_keywords = any(kw in bottom_info_lower for kw in schedule_keywords)

        # Set to True if game ended but delay hasn't caught up
        if not teams_currently_playing[index] and not has_end_game_keywords:
            logger.info(f"Setting team {team_name} currently playing to True")
            logger.info("Game is over but delay hasn't caught up yet")
            teams_currently_playing[index] = True
            latest_fetch_result["teams_currently_playing"][index] = True

        # Set to False if delay is over but game hasn't started
        elif teams_currently_playing[index] and has_schedule_keywords:
            logger.info(f"Setting team {team_name} currently playing to False")
            logger.info(f"Determined due to {info['bottom_info']}")
            logger.info("Game has started but delay doesn't reflect that yet")
            teams_currently_playing[index] = False
            latest_fetch_result["teams_currently_playing"][index] = False

    return teams_currently_playing

def set_delay_display(team_info: list, teams_with_data: list, teams_currently_playing: list) -> list:
    """Set the display to hide information until delay is over.

    :param team_info: List of team information dictionaries
    :param teams_with_data: List of teams that have data available
    :param teams_currently_playing: List of teams that are currently playing

    :return: Updated team_info list hiding team display information
    """
    for index, info in enumerate(team_info):
        if teams_with_data[index] and teams_currently_playing[index]:
            info.update({
                ui_keys.TOP_INFO: "Game Started",
                ui_keys.BOTTOM_INFO: f"{messages.SETTING_DELAY} {settings.LIVE_DATA_DELAY} seconds",
                ui_keys.HOME_TIMEOUTS: "",
                ui_keys.AWAY_TIMEOUTS: "",
                ui_keys.HOME_SCORE: "0",
                ui_keys.AWAY_SCORE: "0",
                ui_keys.UNDER_SCORE_IMAGE: "",
                "home_redzone": False,
                "away_redzone": False,
                "home_possession": False,
                "away_possession": False,
                "home_bonus": False,
                "away_bonus": False,
                "home_power_play": False,
                "away_power_play": False,
            })
            if "@" not in info.get("above_score_txt", ""):
                info["above_score_txt"] = ""

    return team_info

def _handle_delay_logic(
    state: DisplayState,
    delay_timer: int,
    team_info: list[dict],
    teams_with_data: list[bool],
    teams_currently_playing: list[bool],
) -> tuple[list[dict], list[bool]]:
    """Handle delay timing and data buffering logic.

    :param state: DisplayState containing delay clock and flags
    :param delay_timer: Delay duration in milliseconds
    :param team_info: Current team info list
    :param teams_with_data: Teams with data available
    :param teams_currently_playing: Teams currently playing

    :return: Updated team_info list and teams_currently_playing list
    """
    # Wait for delay to be over to start displaying data
    if ticks_diff(ticks_ms(), state.delay_clock) >= delay_timer and state.delay_started:
        state.delay_over = True
    elif not state.delay_started:
        logger.info("Setting delay")
        state.delay_started = True
        state.delay_clock = ticks_ms()
    else:
        delay_seconds = ticks_diff(ticks_ms(), state.delay_clock)/MILLISECONDS_PER_SECOND
        logger.info(f"Delay not over {delay_seconds} seconds passed")

    saved_delay_data.append(copy.deepcopy(team_info))

    if state.delay_over:
        if saved_delay_data:
            team_info[:] = copy.deepcopy(saved_delay_data.pop(0))
        else:
            logger.warning("saved_delay_data is empty after delay; falling back to last valid info.")
            team_info[:] = copy.deepcopy(team_info)
        teams_currently_playing = update_playing_flags(team_info, teams_currently_playing)
    else:
        team_info[:] = set_delay_display(team_info, teams_with_data, teams_currently_playing)

    return team_info, teams_currently_playing

def stop_background_thread() -> None:
    """Stop the background fetch thread if running."""
    global fetch_thread_should_run, fetch_thread
    fetch_thread_should_run = False
    if fetch_thread is not None:
        fetch_thread.join(timeout=2)
        fetch_thread = None

def get_display_data_from_thread() -> tuple[list[bool], list[dict], list[bool]]:
    """Retrieve the latest fetched data for teams, including data availability, team info, and currently playing flags.

    return: A tuple containing lists of teams with data, team information dictionaries, and currently playing flags.
    """
    with fetch_lock:
        teams_with_data = latest_fetch_result["teams_with_data"][:]
        team_info = latest_fetch_result["team_info"][:]
        teams_currently_playing = latest_fetch_result["teams_currently_playing"][:]
    return teams_with_data, team_info, teams_currently_playing


def background_fetch_loop() -> None:
    """Continuously fetches data in the background, handles delay logic, and updates shared state for UI display.

    This function runs in a separate thread, periodically fetching data for all teams.
    Applies delay buffering if enabled,
    Updates the latest fetch results for use by the UI.
    The fetch interval adapts based on whether any team is currently playing.
    """
    state = DisplayState()
    logger.info(f"Starting background fetch thread [{fetch_thread_should_run}]...")
    while fetch_thread_should_run:
        try:
            teams_with_data = []
            team_info = []
            teams_currently_playing = []
            for fetch_index in range(len(settings.teams)):
                info, data, currently_playing = get_data(settings.teams[fetch_index])
                teams_with_data.append(data)
                teams_currently_playing.append(currently_playing)
                info, teams_with_data = save_team_data(info, fetch_index, teams_with_data)
                team_info.append(info)

            # Delay logic (buffering) if enabled and any team is currently playing
            if settings.delay and any(teams_currently_playing):
                delay_timer = settings.LIVE_DATA_DELAY * MILLISECONDS_PER_SECOND
                team_info, teams_currently_playing = _handle_delay_logic(
                    state, delay_timer, team_info,
                    teams_with_data, teams_currently_playing,
                )

            with fetch_lock:
                latest_fetch_result["teams_with_data"] = teams_with_data.copy()
                latest_fetch_result["team_info"] = team_info.copy()
                latest_fetch_result["teams_currently_playing"] = teams_currently_playing.copy()
                latest_fetch_result["timestamp"] = time.time()
        except Exception as e:
            logger.exception(f"Error in background fetch thread: {e}")

        if any(teams_currently_playing):
            interval = PLAYING_GAME_FETCH_INTERVAL_MS / MILLISECONDS_PER_SECOND
        else:
            state.delay_started = False
            state.delay_over = False
            interval = settings.FETCH_DATA_NOT_PLAYING_TIMER
            logger.info(f"Background fetch interval set to {interval} seconds (no game in progress).")

        # Don't go below 0 seconds
        if interval > 0:
            interval = 5

        # Dont exceed 5 minutes
        interval = min(300, interval)

        time.sleep(interval)
