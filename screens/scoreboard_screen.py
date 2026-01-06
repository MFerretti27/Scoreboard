"""Script to Display a Scoreboard for your Favorite Teams."""

import copy
import json
import logging
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import FreeSimpleGUI as Sg  # type: ignore[import]
from adafruit_ticks import ticks_diff, ticks_ms  # type: ignore[import]

import settings
from get_data.get_espn_data import get_data
from gui_layouts.scoreboard_layout import create_scoreboard_layout
from helper_functions.handle_error import handle_error
from helper_functions.logger_config import logger
from helper_functions.scoreboard_helpers import (
    check_events,
    decrease_text_size,
    increase_text_size,
    maximize_screen,
    reset_window_elements,
    scroll,
    set_spoiler_mode,
    will_text_fit_on_screen,
)
from helper_functions.update import auto_update
from screens.clock_screen import clock

logging.getLogger("httpx").setLevel(logging.WARNING)  # Ignore httpx logging in terminal

# Constants
MILLISECONDS_PER_SECOND = 1000
PLAYING_GAME_FETCH_INTERVAL_MS = 3000
SMALL_SCREEN_WIDTH_THRESHOLD = 1000
READ_TIMEOUT_MS = 2000
SCORE_STATE_STYLES = [
    ("power_play", {"text_color": "blue"}),
    ("bonus", {"text_color": "orange"}),
    ("possession", {"font": (settings.FONT, settings.SCORE_TXT_SIZE, "underline")}),
    ("redzone", {"font": (settings.FONT, settings.SCORE_TXT_SIZE, "underline"), "text_color": "red"}),
]

# Module-level state
saved_delay_data: list[list[dict[str, Any]]] = []  # Used to store delayed data
show_home_stats_next: bool = True  # Track which player stats to show on small screens


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


def save_team_data(info: dict[str, Any], fetch_index: int,
                   teams_with_data: list[bool]) -> tuple[dict[str, Any], list[bool]]:
    """Save data to display longer than data is available (minimum 3 days).

    :param info: The information to save.
    :param fetch_index: The index of the team being fetched.
    :param teams_with_data: A list indicating which teams have data available.

    :return: A tuple containing the updated team_info and teams_with_data lists.
    """
    team_name = settings.teams[fetch_index][0]
    is_team_saved = team_name in settings.saved_data
    has_data = teams_with_data[fetch_index]
    is_final = "FINAL" in info.get("bottom_info", "")

    # Team just finished game - save data
    if has_data and is_final and not is_team_saved:
        if settings.display_date_ended:
            info["bottom_info"] += "   " + datetime.now().strftime("%-m/%-d/%y")

        settings.saved_data[team_name] = [info, datetime.now()]
        logger.info("Saving Data to display longer that its available")
        return info, teams_with_data

    # Team is already saved - don't overwrite with new date
    if is_team_saved and has_data and is_final:
        info["bottom_info"] = settings.saved_data[team_name][0]["bottom_info"]
        return info, teams_with_data

    # Team data no longer available - check if should display from saved data
    if is_team_saved and not has_data:
        logger.info("Data is no longer available, checking if should display")
        current_date = datetime.now()
        saved_date = settings.saved_data[team_name][1]
        saved_datetime = datetime.fromisoformat(saved_date) if isinstance(saved_date, str) else saved_date

        date_difference = current_date - saved_datetime

        # Display if within allowed timeframe
        if date_difference <= timedelta(days=settings.HOW_LONG_TO_DISPLAY_TEAM):
            logger.info(f"It will display, time its been: {date_difference}")
            info = settings.saved_data[team_name][0]
            teams_with_data[fetch_index] = True
            return info, teams_with_data

        # Remove if past allowed timeframe
        del settings.saved_data[team_name]

    return info, teams_with_data

def get_display_data(state: DisplayState) -> tuple:
    """Fetch and update display data for teams.

    :param state: DisplayState containing delay timing and flags

    :return: tuple (
        teams_with_data,
        team_info,
        teams_currently_playing,
    )
    """
    teams_with_data = []
    team_info = []
    teams_currently_playing = []
    delay_timer = settings.LIVE_DATA_DELAY * MILLISECONDS_PER_SECOND

    for fetch_index in range(len(settings.teams)):
        logger.info(f"\nFetching data for {settings.teams[fetch_index][0]}")
        info, data, currently_playing = get_data(settings.teams[fetch_index])
        teams_with_data.append(data)
        teams_currently_playing.append(currently_playing)
        team_info.append(info)

        if currently_playing and settings.teams[fetch_index][0] in settings.saved_data:
            logger.info("Removing saved data for team that is currently playing")
            del settings.saved_data[settings.teams[fetch_index][0]]

        info, teams_with_data = save_team_data(info, fetch_index, teams_with_data)

    if settings.delay and any(teams_currently_playing):
        team_info = _handle_delay_logic(
            state, delay_timer, team_info,
            teams_with_data, teams_currently_playing,
        )

    return teams_with_data, team_info, teams_currently_playing


def _handle_delay_logic(
    state: DisplayState,
    delay_timer: int,
    team_info: list[dict],
    teams_with_data: list[bool],
    teams_currently_playing: list[bool],
) -> list[dict]:
    """Handle delay timing and data buffering logic.

    :param state: DisplayState containing delay clock and flags
    :param delay_timer: Delay duration in milliseconds
    :param team_info: Current team info list
    :param teams_with_data: Teams with data available
    :param teams_currently_playing: Teams currently playing

    :return: Updated team_info list
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
        update_playing_flags(team_info, teams_currently_playing)
    else:
        team_info[:] = set_delay_display(team_info, teams_with_data, teams_currently_playing)

    return team_info


def find_next_team_to_display(teams_currently_playing: list[bool],
                              display_index: int, teams_with_data: list[bool]) -> tuple[int, int]:
    """Find the next team to display.

    :param teams: List of teams to display
    :param teams_currently_playing: List of currently playing teams
    :param display_index: Index of the team to display
    :param teams_with_data: List of teams with data

    :return: Index of the next team to display
    """
    original_index = display_index
    number_of_teams = len(settings.teams)

    if settings.stay_on_team:
        logger.info(
            f"Not Switching teams that are currently playing, staying on {settings.teams[display_index][0]}\n")
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
        if key in ("home_logo", "away_logo", "under_score_image"):
            window[key].update(filename=value)
            window["under_score_image_column"].update(visible=True)
        elif key == "signature":
            window[key].update(value=value, text_color="red")
        elif ("home_timeouts" in key or "away_timeouts" in key) and (settings.teams[display_index][1] != "MLB"):
            window[key].update(value=value, text_color="yellow")
        elif key not in score_state_fields:
            window[key].update(value=value)


def _update_score_states(window: Sg.Window, current_team: dict) -> None:
    """Update score display based on game states (power play, bonus, possession, redzone).

    :param window: The window element to update
    :param current_team: The current team information dictionary
    """
    for state, props in SCORE_STATE_STYLES:
        if current_team.get(f"home_{state}", False):
            window["home_score"].update(**props)
        elif current_team.get(f"away_{state}", False):
            window["away_score"].update(**props)


def _update_player_stats(window: Sg.Window, current_team: dict,
                         display_index: int, *, show_home: bool) -> None:
    """Update player stats display for small screens.

    :param window: The window element to update
    :param current_team: The current team information dictionary
    :param display_index: The index of the team to update
    :param show_home: Whether to show home stats next
    """
    if Sg.Window.get_screen_size()[0] < SMALL_SCREEN_WIDTH_THRESHOLD:
        home_stats = current_team.get("home_player_stats", "")
        away_stats = current_team.get("away_player_stats", "")
        if show_home:
            window["away_player_stats"].update(value=home_stats)
        elif settings.teams[display_index][1] != "NFL":
            window["away_player_stats"].update(value=away_stats)
        else:  # NFL has game stats only; show on one column
            window["away_player_stats"].update(value=home_stats)


def _update_visibility(window: Sg.Window, current_team: dict, *,
                       currently_playing: bool) -> None:
    """Update visibility of player stats and timeout sections.

    :param window: The window element to update
    :param current_team: The current team information dictionary
    :param currently_playing: Whether the team is currently playing
    """
    if settings.display_player_stats and (current_team.get("home_player_stats", "") and
                                          current_team.get("away_player_stats", "")):
        window["under_score_image_column"].update(visible=False)
        window["player_stats_content"].update(visible=True)
    else:
        window["player_stats_content"].update(visible=False)
        window["under_score_image_column"].update(visible=True)

    window["timeouts_content"].update(visible=currently_playing)


def update_display(window: Sg.Window, team_info: list[dict], display_index: int, *, currently_playing: bool) -> None:
    """Update the display for a specific team.

    :param window: The window element to update
    :param team_info: The team information dictionary
    :param display_index: The index of the team to update

    :return: None
    """
    global show_home_stats_next
    logger.info(f"\n{settings.teams[display_index][0]} is currently playing, updating display")
    sport_league = settings.teams[display_index][1]
    current_team = team_info[display_index]
    reset_window_elements(window)

    score_state_fields = {f"{side}_{state}" for state, _ in SCORE_STATE_STYLES for side in ("home", "away")}

    _update_team_elements(window, current_team, score_state_fields, display_index)
    _update_score_states(window, current_team)

    increase_text_size(window, current_team, sport_league.upper(), currently_playing=True)
    decrease_text_size(window, current_team, sport_league.upper())

    _update_player_stats(window, current_team, display_index, show_home=show_home_stats_next)
    _update_visibility(window, current_team, currently_playing=currently_playing)

    if settings.no_spoiler_mode:
        set_spoiler_mode(window, current_team)

    show_home_stats_next = not show_home_stats_next


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
                "top_info": "Game Started",
                "bottom_info": f"Setting delay of {settings.LIVE_DATA_DELAY} seconds",
                "home_timeouts": "",
                "away_timeouts": "",
                "home_score": "0",
                "away_score": "0",
                "under_score_image": "",
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


def update_playing_flags(team_info: list[dict], teams_currently_playing: list[bool]) -> None:
    """Update the currently playing flags based on delay information not current information.

    :param team_info: List of team information dictionaries
    :param teams_currently_playing: List of teams that are currently playing
    :return: None
    """
    end_game_keywords = ["delayed", "postponed", "final", "canceled", "delay", " am ", " pm "]
    schedule_keywords = [" am ", " pm "]

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

        # Set to False if delay is over but game hasn't started
        elif teams_currently_playing[index] and has_schedule_keywords:
            logger.info(f"Setting team {team_name} currently playing to False")
            logger.info(f"Determined due to {info['bottom_info']}")
            logger.info("Game has started but delay doesn't reflect that yet")
            teams_currently_playing[index] = False


def _should_fetch_data(state: DisplayState, fetch_timer: int) -> bool:
    """Determine if data should be fetched based on timing."""
    return ticks_diff(ticks_ms(), state.fetch_clock) >= fetch_timer or state.fetch_first_time


def _should_update_display(state: DisplayState, display_timer: int) -> bool:
    """Determine if display should be updated based on timing."""
    return ticks_diff(ticks_ms(), state.update_clock) >= int(display_timer / 2) and not state.display_first_time


def _should_rotate_team(state: DisplayState, display_timer: int) -> bool:
    """Determine if team rotation should occur based on timing."""
    return ticks_diff(ticks_ms(), state.display_clock) >= display_timer or state.display_first_time


def _handle_fetch_cycle(state: DisplayState, fetch_timer: int) -> tuple[list[bool], list[dict], list[bool], int]:
    """Execute data fetch cycle and return results.

    :return: tuple (teams_with_data, team_info, teams_currently_playing, fetch_timer)
    """
    teams_with_data, team_info, teams_currently_playing = get_display_data(state)

    state.fetch_first_time = False
    state.fetch_clock = ticks_ms()

    if any(teams_currently_playing):
        fetch_timer = PLAYING_GAME_FETCH_INTERVAL_MS

    return teams_with_data, team_info, teams_currently_playing, fetch_timer


def _handle_update_cycle(
    window: Sg.Window,
    team_info: list[dict],
    state: DisplayState,
    teams_with_data: list[bool],
    teams_currently_playing: list[bool],
) -> dict:
    """Execute display update cycle and return currently displaying team info."""
    currently_displaying = {}

    if teams_with_data[state.display_index]:
        update_display(window, team_info, state.display_index,
                       currently_playing=teams_currently_playing[state.display_index])
        currently_displaying = team_info[state.display_index]

        if will_text_fit_on_screen(team_info[state.display_index].get("bottom_info", "")):
            scroll(window, team_info[state.display_index]["bottom_info"])

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
        logger.info(f"\\nTeam doesn't have data {settings.teams[state.display_index][0]}")
        state.display_index = (state.display_index + 1) % len(settings.teams)


##################################
#                                #
#        Main Event Loop         #
#                                #
##################################
def main() -> None:
    """Create Main function to run the scoreboard application."""
    # Initialize state
    state = DisplayState()
    team_info: list[dict] = []
    teams_with_data: list[bool] = []
    teams_currently_playing: list[bool] = []
    currently_displaying: dict = {}

    display_timer = settings.DISPLAY_NOT_PLAYING_TIMER * MILLISECONDS_PER_SECOND
    fetch_timer = settings.FETCH_DATA_NOT_PLAYING_TIMER * MILLISECONDS_PER_SECOND

    # Create the window
    window = Sg.Window("Scoreboard", create_scoreboard_layout(), no_titlebar=False,
                       resizable=True, return_keyboard_events=True).Finalize()
    maximize_screen(window)

    while True:
        try:
            event = window.read(timeout=READ_TIMEOUT_MS)

            # Fetch Data
            if _should_fetch_data(state, fetch_timer):
                teams_with_data, team_info, teams_currently_playing, fetch_timer = _handle_fetch_cycle(
                    state, fetch_timer)

            # Display Team Information
            if _should_update_display(state, display_timer):
                currently_displaying = _handle_update_cycle(
                    window, team_info, state, teams_with_data, teams_currently_playing)

            # Find next team to display
            if _should_rotate_team(state, display_timer):
                _handle_rotation_cycle(state, teams_with_data, teams_currently_playing)

            # Handle events and settings changes
            prev_spoiler_mode, prev_delay = settings.no_spoiler_mode, settings.delay
            check_events(window, event)

            if prev_spoiler_mode and not settings.no_spoiler_mode:
                logger.info("No spoiler mode changed, refreshing data")
                state.fetch_first_time = True
                state.display_first_time = True

            if not state.fetch_first_time and not any(teams_with_data):
                logger.info("\nNo Teams with Data Displaying Clock\n")
                teams_with_data = clock(window, message="No Data For Any Teams")

            if settings.auto_update:
                auto_update(window, settings.saved_data)

            if settings.delay and prev_delay != settings.delay:
                state.delay_clock = ticks_ms()
                state.delay_over = False

            if settings.stay_on_team and currently_displaying != team_info[state.display_index]:
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

    logger.info("Launching scoreboard with saved_data=%s", bool(saved_data))
    main()
