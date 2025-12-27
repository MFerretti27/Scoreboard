"""Script to Display a Scoreboard for your Favorite Teams."""

import copy
import importlib
import json
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import FreeSimpleGUI as Sg  # type: ignore[import]
from adafruit_ticks import ticks_add, ticks_diff, ticks_ms  # type: ignore[import]

import settings
from get_data.get_espn_data import get_data
from gui_layouts.scoreboard_layout import create_scoreboard_layout
from helper_functions.internet_connection import is_connected, reconnect
from helper_functions.logger_config import logger
from helper_functions.main_menu_helpers import write_settings_to_py
from helper_functions.scoreboard_helpers import (
    auto_update,
    check_events,
    increase_text_size,
    maximize_screen,
    reset_window_elements,
    scroll,
    set_spoiler_mode,
    wait,
    will_text_fit_on_screen,
)
from screens.clock_screen import clock
from screens.currently_playing_screen import team_currently_playing

logging.getLogger("httpx").setLevel(logging.WARNING)  # Ignore httpx logging in terminal

# Track which player stats to show on small screens (alternates between home and away)
show_home_stats_next = True


def save_team_data(info: dict[str, Any], fetch_index: int,
                   teams_with_data: list[bool]) -> tuple[dict[str, Any], list[bool]]:
    """Save data for to display longer than data is available (minimum 3 days).

    :param info: The information to save.
    :param fetch_index: The index of the team being fetched.
    :param teams_with_data: A list indicating which teams have data available.

    :return: A tuple containing the updated team_info and teams_with_data lists.
    """
    if (teams_with_data[fetch_index] is True and "FINAL" in info.get("bottom_info", "") and
        settings.teams[fetch_index][0] not in settings.saved_data):

        if settings.display_date_ended:
            info["bottom_info"] += "   " + datetime.now().strftime("%-m/%-d/%y")

        settings.saved_data[settings.teams[fetch_index][0]] = [info, datetime.now()]
        logger.info("Saving Data to display longer that its available")

    # If team is already saved dont overwrite it with new date
    elif settings.teams[fetch_index][0] in settings.saved_data and teams_with_data[fetch_index] is True:
        if "FINAL" in info.get("bottom_info", ""):
            info["bottom_info"] = settings.saved_data[settings.teams[fetch_index][0]][0]["bottom_info"]

    elif settings.teams[fetch_index][0] in settings.saved_data and teams_with_data[fetch_index] is False:
        logger.info("Data is no longer available, checking if should display")
        current_date = datetime.now()
        saved_date = settings.saved_data[settings.teams[fetch_index][0]][1]
        saved_datetime = datetime.fromisoformat(saved_date) if isinstance(saved_date, str) else saved_date

        date_difference = current_date - saved_datetime
        # Check if enough days have passed after data is no longer available
        if date_difference <= timedelta(days=settings.HOW_LONG_TO_DISPLAY_TEAM):
            logger.info(f"It will display, time its been: {date_difference}")
            info = settings.saved_data[settings.teams[fetch_index][0]][0]
            teams_with_data[fetch_index] = True
            return info, teams_with_data
        # If greater than days allowed remove
        del settings.saved_data[settings.teams[fetch_index][0]]

    return info, teams_with_data

def display_team_info(window: Sg.Window, team_info: dict[str, Any], display_index: int) -> None:
    """Update the display for a specific team.

    :param window: The window to update.
    :param team_info: The information about the team.
    :param display_index: The index of the team to display.

    :return: None
    """
    logger.info(f"\nUpdating Display for {settings.teams[display_index][0]}")
    reset_window_elements(window)

    for key, value in team_info.items():
        if "home_logo" in key or "away_logo" in key:
            window[key].update(filename=value)

        elif key == "under_score_image":
            window[key].update(filename=value)
            window["player_stats_content"].update(visible=False)
            window["under_score_image_column"].update(visible=True)

        elif key in ["home_player_stats", "away_player_stats"]:
            if Sg.Window.get_screen_size()[0] < 1000:  # If screen height is small, alternate between home and away
                    if show_home_stats_next and key == "home_player_stats":
                        home_stats = team_info["home_player_stats"]
                        window["away_player_stats"].update(value=home_stats)
                        window["home_player_stats"].update(value="")
                        window["home_player_stats"].update(visible=False)

                    elif (not show_home_stats_next and key == "away_player_stats"
                          and settings.teams[display_index][1] != "NFL"):
                        window["away_player_stats"].update(value=value)
                        window["home_player_stats"].update(value="")
                        window["home_player_stats"].update(visible=False)

                    # NFL just have game stats not player so display on one column
                    else:
                        window["away_player_stats"].update(value=team_info.get("home_player_stats", ""))
            else:
                window[key].update(value=value)

            window["under_score_image_column"].update(visible=False)
            window["player_stats_content"].update(visible=True)

        elif key == "signature":
            window[key].update(value=value, text_color="red")
        else:
            window[key].update(value=value)

    increase_text_size(window, team_info)

    if settings.no_spoiler_mode:
        set_spoiler_mode(window, team_info)

def update_display_index(original_index: int, teams_with_data: list[bool]) -> int:
    """Find the next team with available data to display.

    :param original_index: The index of the original team.
    :param teams_with_data: A list indicating which teams have data available.

    :return: The index of the next team with data available.
    """
    display_index = original_index
    for x in range(len(settings.teams)):
        if teams_with_data[(original_index + x) % len(settings.teams)] is False:
            display_index = (display_index + 1) % len(settings.teams)
            logger.info(
                f"skipping displaying {settings.teams[(original_index + x) % len(settings.teams)][0]}, has no data")
        elif teams_with_data[(original_index + x) % len(settings.teams)] is True and x != 0:
            logger.info(
                f"Found next team that has data {settings.teams[(original_index + x) % len(settings.teams)][0]}\n")
            break

    return display_index

def get_team_info(window: Sg.Window) -> tuple[list[bool], list[dict[str, Any]], bool]:
    """Fetch data for each team and update the team information list.

    :param window: The window to update.

    :return: A tuple containing the updated list of teams with data and the team information list.
    """
    fetch_first_time = False
    team_info: list[dict[str, Any]] = []
    teams_with_data: list[bool] = [False] * len(settings.teams)
    for fetch_index in range(len(settings.teams)):
        logger.info(f"\nFetching data for {settings.teams[fetch_index][0]}")
        info, data, currently_playing = get_data(settings.teams[fetch_index])

        # If Game in Play call function to display data differently
        if currently_playing:
            logger.info(f"{settings.teams[fetch_index][0]} Currently Playing")
            team_info, teams_that_played = team_currently_playing(window, settings.teams)
            fetch_first_time = True # To force data to be fetched again when game ends
            # Remove team from saved data as too not overwrite new data from game with old data
            for team in teams_that_played:
                if team in settings.saved_data:
                    del settings.saved_data[team]

        teams_with_data[fetch_index] = data
        # Save data for to display longer than data is available
        info, teams_with_data = save_team_data(info, fetch_index, teams_with_data)
        team_info.append(info)


    return teams_with_data, team_info, fetch_first_time

def handle_error(window: Sg.Window, *, error: Exception | None = None,
                 team_info: list[dict[str, Any]] | None = None) -> None:
    """Handle errors that occur during data fetching."""

    def _snapshot_settings() -> dict[str, str]:
        snapshot: dict[str, str] = {}
        for key, value in vars(settings).items():
            if key.startswith("__"):
                continue
            try:
                snapshot[key] = repr(value)
            except Exception:
                snapshot[key] = "<unserializable>"
        return snapshot

    if error is not None:
        try:
            separator = "\n" + "=" * 80 + "\n"
            logger.error(
                "%sERROR DETAILS:%s\nError: %s\n\nTeam Info:\n%s\n\nSettings:\n%s\n%s",
                separator,
                separator,
                error,
                json.dumps(team_info, indent=2, default=str),
                json.dumps(_snapshot_settings(), indent=2, default=str),
                "=" * 80,
                exc_info=(type(error), error, error.__traceback__),
            )
        except Exception:
            logger.exception("Failed to log handle_error details")

    time_till_clock = 0
    if is_connected():
        while time_till_clock < 12:
            try:
                event = window.read(timeout=5)
                check_events(window, event)  # Check for button presses
                for fetch_index in range(len(settings.teams)):
                    get_data(settings.teams[fetch_index])
                    logger.info("Successfully got data after error")
                    return
            except Exception as e:
                logger.info("Could not get data, trying again...")
                window["top_info"].update(value="Could not get data, trying again...", text_color="red")
                window["bottom_info"].update(value=f"Error: {e}",
                                                font=(settings.FONT, settings.NBA_TOP_INFO_SIZE), text_color="red")
                event = window.read(timeout=2000)
            wait(window, 30) # Wait 30 seconds before trying again
            time_till_clock = time_till_clock + 1

        message = "Failed to Get Data, trying again..."
        clock(window, message)
        return

    while not is_connected():
        event = window.read(timeout=5)
        check_events(window, event)  # Check for button presses
        logger.info("Internet connection is down, trying to reconnect...")
        window["top_info"].update(value="Internet connection is down, trying to reconnect...",
                                    font=(settings.FONT, settings.NBA_TOP_INFO_SIZE), text_color="red")
        window["bottom_info"].update(value="")
        event = window.read(timeout=2000)
        reconnect()
        wait(window, 20) # Wait 20 seconds for connection

        if time_till_clock >= 12:  # If no connection within 4 minutes display clock
            message = "No Internet Connection"
            logger.info("\nNo Internet connection Displaying Clock\n")
            clock(window, message)
            return

        time_till_clock = time_till_clock + 1
    window.refresh()


##################################
#                                #
#        Main Event Loop         #
#                                #
##################################
def main(data_saved: dict) -> None:
    """Create Main function to run the scoreboard application.

    :param saved_data: Dictionary containing saved data for teams
    """
    # Initialize variables
    team_info: list[dict] = []
    settings.saved_data = copy.deepcopy(data_saved)  # Load saved data from command line argument
    display_index: int = 0
    should_scroll: bool = False
    display_clock = ticks_ms()  # Start Timer for Switching Display
    update_clock = ticks_ms() # Start Timer for updating display
    display_timer: int = settings.DISPLAY_NOT_PLAYING_TIMER * 1000  # how often the display should update in seconds
    fetch_clock = ticks_ms()  # Start Timer for fetching data
    fetch_timer: int = settings.FETCH_DATA_NOT_PLAYING_TIMER * 1000  # how often to fetch data
    display_first_time: bool = True
    fetch_first_time: bool = True
    global show_home_stats_next

    if settings.LIVE_DATA_DELAY > 0:
        settings.delay = True

    # Create the window
    window = Sg.Window("Scoreboard", create_scoreboard_layout(), no_titlebar=False,
                       resizable=True, return_keyboard_events=True).Finalize()

    maximize_screen(window)

    while True:
        try:
            event = window.read(timeout=2000)

            # Fetch Data
            if ticks_diff(ticks_ms(), fetch_clock) >= fetch_timer or fetch_first_time:
                teams_with_data, team_info, fetch_first_time = get_team_info(window)
                # Reset timers
                display_clock = ticks_ms()
                fetch_clock = ticks_ms()

            # Display Team Information
            if ticks_diff(ticks_ms(), update_clock) >= int(display_timer/2) or display_first_time:
                if teams_with_data[display_index]:
                    display_first_time = False
                    display_team_info(window, team_info[display_index], display_index)
                    should_scroll = will_text_fit_on_screen(team_info[display_index].get("bottom_info", ""))

                    if should_scroll and not settings.no_spoiler_mode:
                        scroll(window, team_info[display_index]["bottom_info"])

                show_home_stats_next = not show_home_stats_next
                update_clock = ticks_ms()

            # Find next team to display
            if ticks_diff(ticks_ms(), display_clock) >= display_timer or display_first_time:
                if teams_with_data[display_index]:
                    # Find next team to display (skip teams with no data)
                    display_index = update_display_index(display_index, teams_with_data)
                    display_clock = ticks_add(display_clock, display_timer)  # Reset Timer if display updated
                else:
                    logger.info(f"\nTeam doesn't have data {settings.teams[display_index][0]}")
                display_index = (display_index + 1) % len(settings.teams)

            temp_spoiler_mode = settings.no_spoiler_mode  # store to see if button is pressed
            check_events(window, event)  # Check for button presses
            if temp_spoiler_mode is not settings.no_spoiler_mode:  # If turned off get new data instantly
                logger.info("No spoiler mode changed, refreshing data")
                fetch_first_time = True
                display_first_time = True

            if True not in teams_with_data and not fetch_first_time:  # No data to display
                logger.info("\nNo Teams with Data Displaying Clock\n")
                teams_with_data = clock(window, message="No Data For Any Teams")

            if settings.auto_update:
                auto_update(window, settings.saved_data)  # Check if need to auto update

        except Exception as error:
            logger.exception(f"Error: {error}")
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
                    write_settings_to_py(settings_saved)

                    importlib.reload(settings)
                    logger.info("Settings.py updated and reloaded from JSON: %s", settings_path)
                else:
                    logger.warning("Settings file not found: %s", settings_path)

        if "--saved-data" in args:
            idx = args.index("--saved-data")
            if idx + 1 < len(args):
                raw_data = args[idx + 1]
                if raw_data.strip():  # Make sure it's not empty
                    try:
                        saved_data = json.loads(raw_data)
                    except json.JSONDecodeError as e:
                        logger.warning("Invalid JSON for --saved-data: %s", e)
                        saved_data = {}
                else:
                    logger.warning("--saved-data argument provided but empty")

    except Exception as e:
        logger.exception("Error parsing startup arguments: %s", e)
        saved_data = {}

    logger.info("Launching main_screen with saved_data=%s", bool(saved_data))
    main(saved_data)
