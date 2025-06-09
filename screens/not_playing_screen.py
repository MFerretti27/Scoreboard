"""Script to Display a Scoreboard for your Favorite Teams"""

import copy
import json
import platform
import sys
import time
import traceback
from datetime import datetime, timedelta

import FreeSimpleGUI as sg  # type: ignore
from adafruit_ticks import ticks_add, ticks_diff, ticks_ms  # type: ignore

import settings
from get_data.get_espn_data import get_data
from gui_layouts.scoreboard_layout import create_scoreboard_layout
from helper_functions.internet_connection import is_connected, reconnect
from helper_functions.scoreboard_helpers import (
    check_events,
    reset_window_elements,
    resize_text,
    set_spoiler_mode,
    will_text_fit_on_screen,
)
from screens.clock_screen import clock
from screens.currently_playing_screen import team_currently_playing


##################################
#                                #
#        Main Event Loop         #
#                                #
##################################
def main(data_saved: dict) -> None:
    """Main function to run the scoreboard application.

    :param saved_data: Dictionary containing saved data for teams
    """
    # Initialize variables
    team_info: list[dict] = []
    teams_with_data: list[bool] = []
    settings.saved_data = copy.deepcopy(data_saved)  # Load saved data from command line argument
    saved_data: dict[list] = settings.saved_data
    display_index: int = 0
    should_scroll: bool = False
    display_clock = ticks_ms()  # Start Timer for Switching Display
    display_timer = settings.DISPLAY_NOT_PLAYING_TIMER * 1000  # how often the display should update in seconds
    fetch_clock = ticks_ms()  # Start Timer for fetching data
    fetch_timer = settings.FETCH_DATA_NOT_PLAYING_TIMER * 1000  # how often to fetch data
    teams: list[list[str]] = settings.teams
    display_first_time: bool = True
    fetch_first_time: bool = True

    if settings.LIVE_DATA_DELAY > 0:
        settings.delay = True  # Automatically set to true if user entered delay more than 0

    resize_text()  # Resize text to fit screen size

    # Create the window
    window = sg.Window("Scoreboard", create_scoreboard_layout(), no_titlebar=False,
                       resizable=True, return_keyboard_events=True).Finalize()

    # Maximize does not work on MacOS, so we use attributes to set fullscreen
    if platform.system() == 'Darwin':
        window.TKroot.attributes('-fullscreen', True)
    else:
        window.Maximize()
    window.TKroot.config(cursor="none")  # Remove cursor from screen

    while True:
        try:
            # Fetch Data
            if ticks_diff(ticks_ms(), fetch_clock) >= fetch_timer or fetch_first_time:
                fetch_first_time = False
                teams_with_data.clear()
                team_info.clear()
                for fetch_index in range(len(teams)):
                    print(f"\nFetching data for {teams[fetch_index][0]}")
                    info, data, currently_playing = get_data(teams[fetch_index])

                    # If Game in Play call function to display data differently
                    if currently_playing:
                        print(f"{teams[fetch_index][0]} Currently Playing")
                        team_info = team_currently_playing(window, teams)
                        # Reset timers
                        while ticks_diff(ticks_ms(), display_clock) >= display_timer * 2:
                            display_clock = ticks_add(display_clock, display_timer)
                        while ticks_diff(ticks_ms(), fetch_clock) >= fetch_timer * 2:
                            fetch_clock = ticks_add(fetch_clock, fetch_timer)
                        fetch_first_time = True
                        # Remove team from saved data as too not overwrite new data from game with old data
                        if teams[fetch_index][0] in saved_data:
                            del saved_data[teams[fetch_index][0]]

                    # Save data for to display longer than data is available (minimum 3 days)
                    if data is True and "FINAL" in info['bottom_info'] and teams[fetch_index][0] not in saved_data:
                        saved_data[teams[fetch_index][0]] = [info, datetime.now()]
                        if settings.display_date_ended:
                            info['bottom_info'] += "   " + datetime.now().strftime("%-m/%-d/%y")
                        print("Saving Data to display longer that its available")

                    # If team is already saved dont overwrite it with new date
                    elif teams[fetch_index][0] in saved_data and data is True:
                        if "FINAL" in info["bottom_info"]:
                            info['bottom_info'] = saved_data[teams[fetch_index][0]][0]['bottom_info']

                    elif teams[fetch_index][0] in saved_data and data is False:
                        print("Data is no longer available, checking if should display")
                        current_date = datetime.now()
                        saved_date = saved_data[teams[fetch_index][0]][1]
                        if isinstance(saved_date, str):  # check if saved_date is a string, happens if went to main menu
                            saved_datetime = datetime.fromisoformat(saved_date)  # convert string to datetime
                        else:
                            saved_datetime = saved_date  # already a datetime
                        saved_datetime = datetime.fromisoformat(saved_date)
                        date_difference = current_date - saved_datetime
                        # Check if 3 days have passed after data is no longer available
                        if date_difference <= timedelta(days=settings.HOW_LONG_TO_DISPLAY_TEAM):
                            print(f"It will display, time its been: {date_difference}")
                            team_info.append(saved_data[teams[fetch_index][0]][0])
                            teams_with_data.append(True)
                            continue
                        # If greater than days allowed remove
                        else:
                            del saved_data[teams[fetch_index][0]]

                    team_info.append(info)
                    teams_with_data.append(data)

                fetch_clock = ticks_add(fetch_clock, fetch_timer)  # Reset Timer if data fetched

            # Display Team Information
            if ticks_diff(ticks_ms(), display_clock) >= display_timer or display_first_time:
                if teams_with_data[display_index]:
                    display_first_time = False
                    print(f"\nUpdating Display for {teams[display_index][0]}")
                    reset_window_elements(window)

                    if ("@" not in team_info[display_index]['above_score_txt'] and
                        team_info[display_index]['above_score_txt'] != ""):
                        window["above_score_txt"].update(font=(settings.FONT, settings.TOP_TXT_SIZE, "underline")),

                    should_scroll = will_text_fit_on_screen(team_info[display_index]['bottom_info'])

                    for key, value in team_info[display_index].items():
                        if "home_logo" in key or "away_logo" in key or "under_score_image" in key:
                            window[key].update(filename=value)
                        elif "possession" not in key and "redzone" not in key:
                            window[key].update(value=value, text_color='white')

                    if settings.no_spoiler_mode:
                        set_spoiler_mode(window, team_info=team_info[display_index])
                    event = window.read(timeout=2000)

                    # Find next team to display (skip teams with no data)
                    original_index = display_index
                    for x in range(len(teams)):
                        if teams_with_data[(original_index + x) % len(teams)] is False:
                            display_index = (display_index + 1) % len(teams)
                            print(f"skipping displaying {teams[(original_index + x) % len(teams)][0]}, has no data")
                        elif teams_with_data[(original_index + x) % len(teams)] is True and x != 0:
                            print(f"Found next team that has data {teams[(original_index + x) % len(teams)][0]}\n")
                            break

                    display_clock = ticks_add(display_clock, display_timer)  # Reset Timer if display updated
                else:
                    print(f"\nTeam doesn't have data {teams[display_index][0]}")
                display_index = (display_index + 1) % len(teams)

            event = window.read(timeout=1)
            temp_spoiler_mode = settings.no_spoiler_mode  # store to see if button is pressed
            check_events(window, event)  # Check for button presses
            if settings.no_spoiler_mode:
                set_spoiler_mode(window, team_info=team_info[display_index])
            if temp_spoiler_mode is not settings.no_spoiler_mode:  # If turned off get new data instantly
                print("No spoiler mode changed, refreshing data")
                fetch_first_time = True
                display_first_time = True

            # Scroll bottom info if text is too long
            if should_scroll and not settings.no_spoiler_mode:
                text = team_info[original_index]['bottom_info'] + "         "
                for _ in range(2):
                    for _ in range(len(text)):
                        event = window.read(timeout=100)
                        text = text[1:] + text[0]
                        window["bottom_info"].update(value=text)
                    time.sleep(5)

            if True not in teams_with_data:  # No data to display
                print("\nNo Teams with Data Displaying Clock\n")
                teams_with_data = clock(window, message="No Data For Any Teams")

        except Exception as error:
            print(f"Error: {error}")
            traceback.print_exc()  # Prints the full traceback
            time_till_clock = 0
            if is_connected():
                while time_till_clock < 12:
                    event = window.read(timeout=5)
                    check_events(window, event)  # Check for button presses
                    try:
                        for fetch_index in range(len(teams)):
                            get_data(teams[fetch_index])
                        break  # If all data is fetched successfully, break out of loop
                    except Exception as error:
                        print("Could not get data, trying again...")
                        window["top_info"].update(value="Could not get data, trying again...", text_color="red")
                        window["bottom_info"].update(value=f"Error: {error}",
                                                     font=(settings.FONT, settings.NBA_TOP_INFO_SIZE), text_color="red")
                        event = window.read(timeout=2000)
                    time.sleep(30)
                    time_till_clock = time_till_clock + 1
                if time_till_clock >= 12:  # 6 minutes without data, display clock
                    message = 'Failed to Get Data, trying again every 3 minutes'
                    teams_with_data = clock(window, message)
                # Reset timers
                while ticks_diff(ticks_ms(), display_clock) >= display_timer * 2:
                    display_clock = ticks_add(display_clock, display_timer)
                while ticks_diff(ticks_ms(), fetch_clock) >= fetch_timer * 2:
                    fetch_clock = ticks_add(fetch_clock, fetch_timer)
            else:
                print("Internet connection is active")

            while not is_connected():
                event = window.read(timeout=5)
                check_events(window, event)  # Check for button presses
                print("Internet connection is down, trying to reconnect...")
                window["top_info"].update(value="Internet connection is down, trying to reconnect...",
                                          font=(settings.FONT, settings.NBA_TOP_INFO_SIZE), text_color="red")
                event = window.read(timeout=2000)
                reconnect()
                time.sleep(20)  # Check every 20 seconds

                if time_till_clock >= 12:  # If no connection within 4 minutes display clock
                    message = "No Internet Connection"
                    print("\nNo Internet connection Displaying Clock\n")
                    teams_with_data = clock(window, message)
                    # Reset timers
                    while ticks_diff(ticks_ms(), display_clock) >= display_timer * 2:
                        display_clock = ticks_add(display_clock, display_timer)
                    while ticks_diff(ticks_ms(), fetch_clock) >= fetch_timer * 2:
                        fetch_clock = ticks_add(fetch_clock, fetch_timer)

                time_till_clock = time_till_clock + 1
            window.refresh()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        try:
            saved_data = json.loads(sys.argv[1])
        except json.JSONDecodeError as e:
            print("Invalid JSON argument:", e)
            saved_data = {}
    else:
        print("No argument passed. Using default data.")
        saved_data = {}
    main(saved_data)
