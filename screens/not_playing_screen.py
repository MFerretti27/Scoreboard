"""Script to Display a Scoreboard for your Favorite Teams."""

import copy
import json
import logging
import sys
import time
from datetime import datetime, timedelta
from typing import Any

import FreeSimpleGUI as Sg  # type: ignore[import]
from adafruit_ticks import ticks_add, ticks_diff, ticks_ms  # type: ignore[import]

import settings
from get_data.get_espn_data import get_data
from gui_layouts.scoreboard_layout import create_scoreboard_layout
from helper_functions.internet_connection import is_connected, reconnect
from helper_functions.logger_config import logger
from helper_functions.scoreboard_helpers import (
    check_events,
    maximize_screen,
    reset_window_elements,
    scroll,
    set_spoiler_mode,
    will_text_fit_on_screen,
)
from screens.clock_screen import clock
from screens.currently_playing_screen import team_currently_playing

logging.getLogger("httpx").setLevel(logging.WARNING)  # Ignore httpx logging in terminal


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
            print(info)
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
    print(team_info)
    logger.info(f"\nUpdating Display for {settings.teams[display_index][0]}")
    reset_window_elements(window)

    for key, value in team_info.items():
        if "home_logo" in key or "away_logo" in key or "under_score_image" in key:
            window[key].update(filename=value)
        elif key == "signature":
            window[key].update(value=value, text_color="red")
        else:
            window[key].update(value=value)

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

def get_team_info(window: Sg.Window, team_info: list[dict[str, Any]]) -> tuple[list[bool], list[dict[str, Any]], bool]:
    """Fetch data for each team and update the team information list.

    :param window: The window to update.
    :param team_info: The information about the teams.

    :return: A tuple containing the updated list of teams with data and the team information list.
    """
    fetch_first_time = False
    teams_with_data: list[bool] = [False] * len(settings.teams)
    for fetch_index in range(len(settings.teams)):
        logger.info(f"\nFetching data for {settings.teams[fetch_index][0]}")
        info, data, currently_playing = get_data(settings.teams[fetch_index])

        # If Game in Play call function to display data differently
        if currently_playing:
            logger.info(f"{settings.teams[fetch_index][0]} Currently Playing")
            team_info = team_currently_playing(window, settings.teams)
            fetch_first_time = True # To force data to be fetched again when game ends
            # Remove team from saved data as too not overwrite new data from game with old data
            if settings.teams[fetch_index][0] in settings.saved_data:
                del settings.saved_data[settings.teams[fetch_index][0]]

        teams_with_data[fetch_index] = data
        # Save data for to display longer than data is available
        info, teams_with_data = save_team_data(info, fetch_index, teams_with_data)
        team_info.append(info)

    return teams_with_data, team_info, fetch_first_time

def handle_error(window: Sg.Window) -> None:
    """Handle errors that occur during data fetching."""
    time_till_clock = 0
    if is_connected():
        while time_till_clock < 12:
            event = window.read(timeout=5)
            check_events(window, event)  # Check for button presses
            try:
                for fetch_index in range(len(settings.teams)):
                    get_data(settings.teams[fetch_index])
                    return
            except Exception as error:
                logger.info("Could not get data, trying again...")
                window["top_info"].update(value="Could not get data, trying again...", text_color="red")
                window["bottom_info"].update(value=f"Error: {error}",
                                                font=(settings.FONT, settings.NBA_TOP_INFO_SIZE), text_color="red")
                event = window.read(timeout=2000)
            time.sleep(30)
            time_till_clock = time_till_clock + 1
        if time_till_clock >= 12:  # 6 minutes without data, display clock
            message = "Failed to Get Data, trying again..."
            clock(window, message)
            return
    else:
        logger.info("Internet connection is active")

    while not is_connected():
        event = window.read(timeout=5)
        check_events(window, event)  # Check for button presses
        logger.info("Internet connection is down, trying to reconnect...")
        window["top_info"].update(value="Internet connection is down, trying to reconnect...",
                                    font=(settings.FONT, settings.NBA_TOP_INFO_SIZE), text_color="red")
        window["bottom_info"].update(value="")
        event = window.read(timeout=2000)
        reconnect()
        time.sleep(20)  # Check every 20 seconds

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
    display_timer: int = settings.DISPLAY_NOT_PLAYING_TIMER * 1000  # how often the display should update in seconds
    fetch_clock = ticks_ms()  # Start Timer for fetching data
    fetch_timer: int = settings.FETCH_DATA_NOT_PLAYING_TIMER * 1000  # how often to fetch data
    display_first_time: bool = True
    fetch_first_time: bool = True

    if settings.LIVE_DATA_DELAY > 0:
        settings.delay = True

    # Create the window
    window = Sg.Window("Scoreboard", create_scoreboard_layout(), no_titlebar=False,
                       resizable=True, return_keyboard_events=True).Finalize()

    # window.set_cursor("none")  # Hide the mouse cursor
    maximize_screen(window)

    while True:
        try:
            event = window.read(timeout=100)

            # Fetch Data
            if ticks_diff(ticks_ms(), fetch_clock) >= fetch_timer or fetch_first_time:
                teams_with_data, team_info, fetch_first_time = get_team_info(window, team_info)
                # Reset timers
                display_clock = ticks_ms()
                fetch_clock = ticks_ms()

            # Display Team Information
            if ticks_diff(ticks_ms(), display_clock) >= display_timer or display_first_time:
                if teams_with_data[display_index]:
                    display_first_time = False
                    display_team_info(window, team_info[display_index], display_index)
                    should_scroll = will_text_fit_on_screen(team_info[display_index].get("bottom_info", ""))

                    if should_scroll and not settings.no_spoiler_mode:
                        scroll(window, team_info[display_index]["bottom_info"])

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

        except Exception as error:
            logger.exception(f"Error: {error}")
            handle_error(window)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        try:
            saved_data = json.loads(sys.argv[1])
        except json.JSONDecodeError as e:
            logger.info("Invalid JSON argument:", e)
            saved_data = {}
    else:
        logger.info("No argument passed. Using default data.")
        saved_data = {}
    main(saved_data)
