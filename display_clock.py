'''Display a Clock When Internet Connection Goes Out, When Grabbing Data from ESPN API Fails,
   Or When There is No Team Data to Display
'''

import datetime
import time
from get_data import get_data
from internet_connection import is_connected, reconnect
from adafruit_ticks import ticks_ms, ticks_add, ticks_diff # pip3 install adafruit-circuitpython-ticks
from constants import *

def clock(window, SPORT_URLS, message) -> None:
    '''If no team has any data then display clock

    :param window: Window Element that controls GUI
    :param SPORT_URLS: URL links to grab data to see if situation has changed
    :param message: Message to display why script is showing clock
    '''

    fetch_clock = ticks_ms() # Start Timer for Switching Display
    fetch_timer = 180 * 1000 # how often the display should update in seconds
    teams_with_data = []

    while True not in teams_with_data:
        current_time = datetime.datetime.now()
        if current_time.hour > 12: hour = current_time.hour - 12
        else: hour = current_time.hour
        if current_time.minute < 10: minute = "0" + str(current_time.minute)
        else: minute = current_time.minute
        date = str(current_time.month) + '/' + str(current_time.day) + '/' + str(current_time.year)
        window["hyphen"].update(value=':', font=(FONT, SCORE_TXT_SIZE))
        window["home_score"].update(value=minute, font=(FONT, CLOCK_TXT_SIZE))
        window["away_score"].update(value=hour, font=(FONT, CLOCK_TXT_SIZE))
        window["home_record"].update(value='')
        window["away_record"].update(value='')
        window["away_logo"].update(filename="sport_logos/team0_logos/DET.png")
        window["network_logo"].update(filename='')
        window["home_logo"].update(filename="sport_logos/team0_logos/DET.png")
        window["bottom_info"].update(value=date,font=(FONT, SCORE_TXT_SIZE))
        window["top_info"].update(value=message,font=(FONT, TIMEOUT_SIZE))
        window.read(timeout=5000)

        # Fetch to see if any teams have data now
        try:
            if ticks_diff(ticks_ms(), fetch_clock) >= fetch_timer:
                teams_with_data.clear()
                for fetch_index in range(len(teams)):
                    print(f"\nFetching data for {teams[fetch_index][0]}")
                    info, data, currently_playing = get_data(SPORT_URLS[fetch_index], teams[fetch_index], fetch_index, network_logos)
                    teams_with_data.append(data)

                fetch_clock = ticks_add(fetch_clock, fetch_timer) # Reset Timer if display updated
        except:
            print("Failed to Get Data")
            if is_connected():
                message = 'Failed to Get Info From ESPN, ESPN Changed API EndPoints, Update Script'
            if not is_connected():
                print("Internet connection is down, trying to reconnect...")
                reconnect()
                time.sleep(20)  # Wait 20 seconds for connection

    # Reset Text Font Size
    window["hyphen"].update(value='-',font=(FONT, HYPHEN_SIZE))
    window["home_score"].update(font=(FONT, SCORE_TXT_SIZE))
    window["away_score"].update(font=(FONT, SCORE_TXT_SIZE))
    window['bottom_info'].update(font=(FONT, INFO_TXT_SIZE))
    window['top_info'].update(font=(FONT, NOT_PLAYING_TOP_INFO_SIZE))
    return teams_with_data