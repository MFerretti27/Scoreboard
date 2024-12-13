'''Script to Display a Scoreboard for your Favorite Teams'''

# Common imports (should be on all computers)
import os
import sys
import time

# Check if you are currently in Virtual Environment, if not exit
if sys.prefix != sys.base_prefix:
    print("\tYou are currently in a virtual environment.")
    if os.environ.get('DISPLAY','') == '':
        print('no display found. Using :0.0')
        os.environ.__setitem__('DISPLAY', ':0.0')
else:
    print("Please go into virtual Environment by running main.py")
    exit()

import FreeSimpleGUI as sg # pip install FreeSimpleGUI
from datetime import datetime, timedelta
from adafruit_ticks import ticks_ms, ticks_add, ticks_diff # pip3 install adafruit-circuitpython-ticks
from internet_connection import is_connected, reconnect
from get_team_logos import get_team_logos
from gui_setup import gui_setup
from get_data import get_data
from display_clock import clock
from constants import *

SPORT_URLS = []
display_clock = ticks_ms() # Start Timer for Switching Display
display_timer = 25 * 1000 # how often the display should update in seconds
fetch_clock = ticks_ms() # Start Timer for Switching Display
fetch_timer = 180 * 1000 # how often the display should update in seconds

for i in range(len(teams)):
    sport_league = teams[i][1]
    sport_name = teams[i][2]
    SPORT_URLS.append(f"https://site.api.espn.com/apis/site/v2/sports/{sport_name}/{sport_league}/scoreboard")

get_team_logos(teams, TEAM_LOGO_SIZE)
window = gui_setup()

##########################################
#                                        #
#  Display only Teams currently playing  #
#                                        #
##########################################
def team_currently_playing(window, teams):
    '''Display only games that are playing
    
    :param window: Window Element that controls GUI
    :param teams: Array of teams to search data for
    '''

    teams_currently_playing = []
    first_time = True
    team_info = []
    teams_with_data = []
    display_index = 0

    display_clock = ticks_ms() # Start Timer for Switching Display
    fetch_clock = ticks_ms() # Start Timer for Switching Display
    display_timer = 25 * 1000 # how often the display should update in seconds
    fetch_timer = 25 * 1000 # how often the display should update in seconds

    while True in teams_currently_playing or first_time:
        if ticks_diff(ticks_ms(), fetch_clock) >= fetch_timer or first_time:
            first_time = False
            teams_with_data.clear()
            team_info.clear()
            teams_currently_playing.clear()
            for fetch_index in range(len(teams)):
                print(f"\nFetching data for {teams[fetch_index][0]}")
                info, data, currently_playing = get_data(SPORT_URLS[fetch_index], teams[fetch_index], fetch_index)
                team_info.append(info)
                teams_with_data.append(data)
                teams_currently_playing.append(currently_playing)

            fetch_clock = ticks_add(fetch_clock, fetch_timer) # Reset Timer if display updated

        # Display Team Information
        if ticks_diff(ticks_ms(), display_clock) >= display_timer:
            if teams_with_data[display_index] and teams_currently_playing[display_index]:
                print(f"\n{teams[display_index][0]} is currently playing, updating display\n")

                # Reset text color, underline and timeouts, for new display
                window['timeouts'].update(value='', font=(FONT, TIMEOUT_SIZE))
                window['home_score'].update(font=(FONT, SCORE_TXT_SIZE), text_color ='white')
                window['away_score'].update(font=(FONT, SCORE_TXT_SIZE), text_color ='white')
                window['top_info'].update(font=(FONT, PLAYING_TOP_INFO_SIZE), text_color ='white')

                for key, value in team_info[display_index].items():
                    if "home_logo" in key or "away_logo" in key:
                        window[key].update(filename=value)
                    elif "network_logo" in key:
                        window[key].update(filename=value, subsample=NETWORK_LOGOS_SIZE)
                    elif "possession" not in key and "redzone" not in key:
                        window[key].update(value=value, text_color ='white')
    
                    # Football Specific
                    if "nfl" in SPORT_URLS[display_index]:
                        if team_info[display_index]['home_possession'] and key == 'home_score':
                            window['home_score'].update(value=value, font=(FONT, SCORE_TXT_SIZE, "underline"))
                        elif team_info[display_index]['away_possession'] and key == 'away_score':
                            window['away_score'].update(value=value, font=(FONT, SCORE_TXT_SIZE, "underline"))
                        if team_info[display_index]['home_redzone'] and key == 'home_score':
                            window['home_score'].update(value=value, font=(FONT, SCORE_TXT_SIZE, "underline"), text_color ='red')
                        elif team_info[display_index]['away_redzone'] and key == 'away_score':
                            window['away_score'].update(value=value, font=(FONT, SCORE_TXT_SIZE, "underline"), text_color ='red')

                    # NBA Specific
                    if "nba" in SPORT_URLS[display_index] and key == 'top_info':
                        window['top_info'].update(value=value, font=(FONT, NBA_TOP_INFO_SIZE))

                window.read(timeout=5000)

                # Find next team to display (skip teams with no data)
                original_index = display_index
                display_clock = ticks_add(display_clock, display_timer)
                for x in range(len(teams)):
                    if teams_currently_playing[(original_index + x) % len(teams)] == False:
                        display_index = (display_index + 1) % len(teams)
                        print(f"skipping displaying {teams[(original_index + x) % len(teams)][0]}, current display index: {display_index}")
                    elif teams_currently_playing[(original_index + x) % len(teams)] == True and x != 0:
                        print(f"Found next team that is currently playing {teams[(original_index + x) % len(teams)][0]}\n")
                        break
            else:
                print(f"{teams[display_index][0]} is not currently playing and wont Display")
            
            display_index = (display_index + 1) % len(teams)
    
    # Reset font and color to ensure everything is back to normal
    window['home_score'].update(font=(FONT, SCORE_TXT_SIZE), text_color ='white')
    window['away_score'].update(font=(FONT, SCORE_TXT_SIZE), text_color ='white')
    print("\nNo Team Currently Playing\n")
    fetch_timer = 180 * 1000 #  Put back to fetching every 3 minutes if no team playing
    return team_info


##################################
#                                #
#    Get Data for First Time     #
#                                #
##################################
team_info = []
teams_with_data = []
saved_data = {}
display_index = 0
try:
    for fetch_index in range(len(teams)):
        print(f"\nFetching data for {teams[fetch_index][0]}")
        info, data, currently_playing = get_data(SPORT_URLS[fetch_index], teams[fetch_index], fetch_index)
        team_info.append(info)
        teams_with_data.append(data)
        if currently_playing:
                returned_data = team_currently_playing(window, teams)
                team_info = returned_data
except:
    if is_connected():
        message = 'Failed to Get Info From ESPN, ESPN Changed API EndPoints, Update Script'
        teams_with_data = clock(window, SPORT_URLS, message)
    while not is_connected():
        print("Internet connection is down, trying to reconnect...")
        reconnect()
        time.sleep(20)  # Check every 20 seconds
        message = "No Internet Connection"
        print("\nNo Internet connection Displaying Clock\n")
        teams_with_data = clock(window, SPORT_URLS, message)

event, values = window.read(timeout=5000)

##################################
#                                #
#          Event Loop            #
#                                #
##################################
while True:
    try:
        # Fetch Data
        if ticks_diff(ticks_ms(), fetch_clock) >= fetch_timer:
            teams_with_data.clear()
            team_info.clear()
            for fetch_index in range(len(teams)):
                print(f"\nFetching data for {teams[fetch_index][0]}")
                info, data, currently_playing = get_data(SPORT_URLS[fetch_index], teams[fetch_index], fetch_index)
                if currently_playing:
                    returned_data = team_currently_playing(window, teams)
                    team_info = returned_data
                
                # Save data for NBA, NHL, MLB data to display longer than data is available
                if data == True and "FINAL" in info['bottom_info'] and "nfl" not in teams[fetch_index][1]:
                    saved_data[teams[fetch_index][0]] = [info, datetime.now()]
                    print("Saving Data to display longer that its available")
                elif teams[fetch_index][0] in saved_data and data == False:
                    print("Data is no longer available, checking if should display")
                    current_date = datetime.now()
                    date_difference = current_date - saved_data[teams[fetch_index][1]][1]
                    print(date_difference)
                    # Check if 2 days have passed after data is no longer available
                    if date_difference <= timedelta(days=2):
                        print("Yes it should display")
                        team_info.append(saved_data[teams[fetch_index][1]][0])
                        teams_with_data.append(True)
                        continue
                
                team_info.append(info)
                teams_with_data.append(data)

            fetch_clock = ticks_add(fetch_clock, fetch_timer) # Reset Timer if display updated

        # Display Team Information
        if ticks_diff(ticks_ms(), display_clock) >= display_timer:
            if teams_with_data[display_index]:
                print(f"\nUpdating Display for {teams[display_index][0]}")
                window['top_info'].update(font=(FONT, NOT_PLAYING_TOP_INFO_SIZE))
                window['timeouts'].update(value='', font=(FONT, TIMEOUT_SIZE))

                # Change Size of game info if length is too long
                if len(team_info[display_index]['bottom_info']) > CHARACTERS_FIT_ON_SCREEN:
                    characters_over = len(team_info[display_index]['bottom_info']) - CHARACTERS_FIT_ON_SCREEN
                    window['bottom_info'].update(font=(FONT, INFO_TXT_SIZE - (SPACE_ONE_CHARACTER_TAKES_UP * characters_over)))
                else:
                    window['bottom_info'].update(font=(FONT, INFO_TXT_SIZE))

                for key, value in team_info[display_index].items():
                    if "home_logo" in key or "away_logo" in key:
                        window[key].update(filename=value)
                    elif "network_logo" in key:
                        window[key].update(filename=value, subsample=NETWORK_LOGOS_SIZE)
                    elif "possession" not in key and "redzone" not in key:
                        window[key].update(value=value, text_color ='white')

                event, values = window.read(timeout=5000)

                # Find next team to display (skip teams with no data)
                original_index = display_index
                for x in range(len(teams)):
                    if teams_with_data[(original_index + x) % len(teams)] == False:
                        display_index = (display_index + 1) % len(teams)
                        print(f"skipping displaying {teams[(original_index + x) % len(teams)][0]}, has no data")
                    elif teams_with_data[(original_index + x) % len(teams)] == True and x != 0:
                        print(f"Found next team that has data {teams[(original_index + x) % len(teams)][0]}\n")
                        break
                    
                display_clock = ticks_add(display_clock, display_timer)
            else:
                print(f"{teams[display_index][0]} has no Data and wont Display")

            display_index = (display_index + 1) % len(teams)

        if event == sg.WIN_CLOSED:
            window.close()

        if True not in teams_with_data:
            message = "No Data For Any Teams"
            print("\nNo Teams with Displaying Clock\n")
            teams_with_data = clock(window, teams_with_data, SPORT_URLS, message)

    except:
        time_till_clock = 0
        if is_connected():
            message = 'Failed to Get Info From ESPN, ESPN Changed API EndPoints, Update Script'
            teams_with_data = clock(window, SPORT_URLS, message)
        while not is_connected():
            print("Internet connection is down, trying to reconnect...")
            reconnect()
            time.sleep(20)  # Check every 20 seconds

            if time_till_clock >= 12: # If no connection within 4 minutes display clock
                message = "No Internet Connection"
                print("\nNo Internet connection Displaying Clock\n")
                teams_with_data = clock(window, SPORT_URLS, message)

            time_till_clock = time_till_clock + 1

        time.sleep(2)
        print("Internet connection is active")