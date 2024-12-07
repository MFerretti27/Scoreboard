
import datetime
import time
from get_data import get_data
from internet_connection import get_network_interface, is_connected, reconnect
from adafruit_ticks import ticks_ms, ticks_add, ticks_diff # pip3 install adafruit-circuitpython-ticks
from hardware_setup import teams, INFO_TXT_SIZE, CLOCK_TXT_SIZE, SCORE_TXT_SIZE, HYPHEN_SIZE, FONT, TIMEOUT_SIZE, NOT_PLAYING_TOP_INFO_SIZE

def clock(window, teams_with_data, SPORT_URLS, network_logos, message) -> None:
    '''If no team has any data then display clock
    :param window: Window Element that controls GUI
    :param teams: Array tha contains all teams being monitored 
    :param teams_with_data: Array of booleans that tell if a team has data
    :param SPORT_URLS: URL links to grab data to see if situation has changed
    '''

    fetch_clock = ticks_ms() # Start Timer for Switching Display
    fetch_timer = 180 * 1000 # how often the display should update in seconds
    # If there is no data for any team display clock
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

        # Fetch Data
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
            while not is_connected():
                network_interface = get_network_interface()
                print("Internet connection is down, trying to reconnect...")
                reconnect(network_interface)
                time.sleep(20)  # Check every 20 seconds

    # Reset Text Font Size
    window["hyphen"].update(value='-',font=(FONT, HYPHEN_SIZE))
    window["home_score"].update(font=(FONT, SCORE_TXT_SIZE))
    window["away_score"].update(font=(FONT, SCORE_TXT_SIZE))
    window['bottom_info'].update(font=(FONT, INFO_TXT_SIZE))
    window['top_info'].update(font=(FONT, NOT_PLAYING_TOP_INFO_SIZE))