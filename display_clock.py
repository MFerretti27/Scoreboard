'''Display a Clock When Internet Connection Goes Out, When Grabbing Data from ESPN API Fails,
   Or When There is No Team Data to Display
'''

import datetime
import time
import FreeSimpleGUI as sg
from get_team_logos import get_random_logo
from get_data.get_espn_data import get_data
from gui_setup import reset_window_elements
from internet_connection import is_connected, reconnect
from adafruit_ticks import ticks_ms, ticks_add, ticks_diff  # pip3 install adafruit-circuitpython-ticks
from constants import *


def clock(window: sg.Window, message: str) -> list:
    '''If no team has any data then display clock

    :param window: Window Element that controls GUI
    :param message: Message to display why script is showing clock

    :return team_info: List of Boolean values representing if team is has data to display
    '''

    fetch_clock = ticks_ms()  # Start timer for switching display
    fetch_timer = 180 * 1000  # How often the display should update in seconds
    fetch_picture = ticks_ms()  # Start timer for switching picture
    fetch_picture_timer = 60 * 1000  # How often the picture should update in seconds
    teams_with_data = []
    first_time = True

    reset_window_elements(window)

    while True not in teams_with_data:
        if ticks_diff(ticks_ms(), fetch_picture) >= fetch_picture_timer or first_time:
            first_time = False
            files = get_random_logo()
            fetch_picture = ticks_add(fetch_picture, fetch_picture_timer)  # Reset Timer if picture updated

        current_time = datetime.datetime.now()
        hour = current_time.hour if current_time.hour < 13 else current_time.hour - 12
        minute = current_time.minute if current_time.minute > 9 else f"0{current_time.minute}"

        date = str(current_time.month) + '/' + str(current_time.day) + '/' + str(current_time.year)
        window["hyphen"].update(value=':', font=(FONT, SCORE_TXT_SIZE))
        window["home_score"].update(value=minute, font=(FONT, CLOCK_TXT_SIZE))
        window["away_score"].update(value=hour, font=(FONT, CLOCK_TXT_SIZE))
        window["away_logo"].update(filename=f"images/sport_logos/{files[0][0]}/{files[0][1]}.png")
        window["home_logo"].update(filename=f"images/sport_logos/{files[1][0]}/{files[1][1]}.png")
        window["bottom_info"].update(value=date, font=(FONT, SCORE_TXT_SIZE))
        window["top_info"].update(value=message, font=(FONT, TIMEOUT_SIZE))

        event = window.read(timeout=5000)
        if event[0] == sg.WIN_CLOSED or 'Escape' in event[0]:
            window.close()
            exit()

        # Fetch to see if any teams have data to return to main loop
        try:
            if ticks_diff(ticks_ms(), fetch_clock) >= fetch_timer:
                teams_with_data.clear()
                for fetch_index in range(len(teams)):
                    print(f"\nFetching data for {teams[fetch_index][0]}")
                    data = get_data(teams[fetch_index])
                    teams_with_data.append(data[1])
                    print(teams_with_data)
                    message = "No Data For Any Teams"

                fetch_clock = ticks_add(fetch_clock, fetch_timer)  # Reset Timer if display updated
        except Exception as error:
            print(f"Failed to Get Data, Error: {error}")
            if is_connected():
                message = f'Failed to Get Info From ESPN, Error:{error}'
            if not is_connected():
                print("Internet connection is down, trying to reconnect...")
                message = "No Internet Connection"
                reconnect()
                time.sleep(20)  # Wait 20 seconds for connection

    # Reset Text Font Size
    reset_window_elements(window)
    return teams_with_data
