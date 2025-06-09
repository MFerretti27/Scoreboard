"""Display a Clock When Internet Connection Goes Out, When Grabbing Data from ESPN API Fails,
   Or When There is No Team Data to Display.
"""

import datetime
import gc
import subprocess
import sys
import time

import FreeSimpleGUI as sg  # type: ignore
import orjson
from adafruit_ticks import ticks_add, ticks_diff, ticks_ms  # type: ignore

import settings
from get_data.get_espn_data import get_data
from get_data.get_team_logos import get_random_logo
from helper_functions.internet_connection import is_connected, reconnect
from helper_functions.scoreboard_helpers import reset_window_elements


def clock(window: sg.Window, message: str) -> list:
    """If no team has any data then display clock.

    :param window: Window Element that controls GUI
    :param message: Message to display why script is showing clock

    :return team_info: List of Boolean values representing if team is has data to display
    """

    fetch_clock = ticks_ms()  # Start timer for switching display
    fetch_timer = 180 * 1000  # How often the display should update in seconds
    fetch_picture = ticks_ms()  # Start timer for switching picture
    fetch_picture_timer = 60 * 1000  # How often the picture should update in seconds
    teams_with_data: list[bool] = []
    first_time = True

    reset_window_elements(window)

    while True not in teams_with_data:

        # Every minute randomly select one of the users team logos to display
        if ticks_diff(ticks_ms(), fetch_picture) >= fetch_picture_timer or first_time:
            first_time = False
            files = get_random_logo()
            fetch_picture = ticks_add(fetch_picture, fetch_picture_timer)  # Reset Timer if picture updated

        # Get the current time and display it
        current_time = datetime.datetime.now()
        hour = current_time.hour if current_time.hour < 13 else current_time.hour - 12
        minute = current_time.minute if current_time.minute > 9 else f"0{current_time.minute}"

        date = str(current_time.month) + '/' + str(current_time.day) + '/' + str(current_time.year)
        window["hyphen"].update(value=':', font=(settings.FONT, settings.SCORE_TXT_SIZE))
        window["home_score"].update(value=minute, font=(settings.FONT, settings.CLOCK_TXT_SIZE))
        window["away_score"].update(value=hour, font=(settings.FONT, settings.CLOCK_TXT_SIZE))
        window["away_logo"].update(filename=f"images/sport_logos/{files[0][0]}/{files[0][1]}.png")
        window["home_logo"].update(filename=f"images/sport_logos/{files[1][0]}/{files[1][1]}.png")
        window["bottom_info"].update(value=date, font=(settings.FONT, settings.RECORD_TXT_SIZE))
        window["top_info"].update(value=message, font=(settings.FONT, settings.TIMEOUT_SIZE))

        event = window.read(timeout=5000)
        if event[0] == sg.WIN_CLOSED or 'Escape' in event[0]:
            window.close()
            gc.collect()  # Clean up memory
            time.sleep(0.5)  # Give OS time to destroy the window
            json_saved_data = orjson.dumps(settings.saved_data)
            subprocess.Popen([sys.executable, "-m", "screens.main_screen", json_saved_data])
            sys.exit()

        # Fetch to see if any teams have data and return to main loop displaying team info
        try:
            if ticks_diff(ticks_ms(), fetch_clock) >= fetch_timer:
                teams_with_data.clear()
                for fetch_index in range(len(settings.teams)):
                    print(f"\nFetching data for {settings.teams[fetch_index][0]}")
                    data = get_data(settings.teams[fetch_index])
                    teams_with_data.append(data[1])
                    message = "No Data For Any Teams"

                fetch_clock = ticks_add(fetch_clock, fetch_timer)  # Reset Timer if fetch attempted

        # If fetched failed find out why and display message
        except Exception as error:
            print(f"Failed to Get Data, Error: {error}")
            if is_connected():
                message = f'Failed to Get Info From ESPN, Error:{error}'
            if not is_connected():
                print("Internet connection is down, trying to reconnect...")
                message = "No Internet Connection"
                reconnect()
                time.sleep(20)  # Wait 20 seconds for connection

    # Reset Text Font Size before returning to main loop
    reset_window_elements(window)
    return teams_with_data
