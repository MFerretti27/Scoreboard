'''
Script to Display a Scoreboard for your Favorite Teams 

@Requirements: Python must be installed and in PATH
@Author: Matthew Ferretti
'''

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
from adafruit_ticks import ticks_ms, ticks_add, ticks_diff # pip3 install adafruit-circuitpython-ticks
from internet_connection import get_network_interface, get_router_ip, is_connected, reconnect
from grab_team_logos import grab_team_logos
from gui_setup import setup_gui
from get_data import get_data
from hardware_setup import teams, TEAM_LOGO_SIZE, INFO_TXT_SIZE, SCORE_TXT_SIZE, FONT

SPORT_URLS = []
team_has_data = False
currently_playing = False
display_clock = ticks_ms() # Start Timer for Switching Display
display_timer = 25 * 1000 # how often the display should update in seconds
fetch_clock = ticks_ms() # Start Timer for Switching Display
fetch_timer = 180 * 1000 # how often the display should update in seconds

network_logos = {
    "ABC": ["Networks/ABC.png", 5],
    "CBS": ["Networks/CBS.png", 1],
    "ESPN": ["Networks/ESPN.png", 5],
    "FOX": ["Networks/FOX.png", 2],
    "MLB": ["Networks/MLB_Network.png", 3],
    "NBC": ["Networks/NBC.png", 8],
    "Prime": ["Networks/Prime.png", 10],
    "TNT": ["Networks/TNT.png", 7],
    # "NBA TV": ["Networks/NBA_TV.png", 5],
    "NBA": ["Networks/NBA_League.png", 1],
    "NFL": ["Networks/NFL_NET.png", 2],
}

for i in range(len(teams)):
    sport_league = teams[i][1]
    sport_name = teams[i][2]
    SPORT_URLS.append(f"https://site.api.espn.com/apis/site/v2/sports/{sport_name}/{sport_league}/scoreboard")


router_ip = get_router_ip()
network_interface = get_network_interface()
grab_team_logos(teams, TEAM_LOGO_SIZE)
window = setup_gui()

##########################################
#                                        #
#  Display only Teams currently playing  #
#                                        #
##########################################
def team_currently_playing(window):
    '''Display only games that are playing'''
    global teams, display_clock, fetch_clock, network_logos

    teams_currently_playing = []
    first_time = True
    team_info = []
    teams_with_data = []
    display_index = 0
    display_timer = 25 * 1000 # how often the display should update in seconds
    fetch_timer = 25 * 1000 # how often the display should update in seconds

    while True in teams_currently_playing or first_time:
        first_time = False
        if ticks_diff(ticks_ms(), fetch_clock) >= fetch_timer or first_time:
            teams_with_data.clear()
            team_info.clear()
            teams_currently_playing.clear()
            for fetch_index in range(len(teams)):
                print(f"\nFetching data for {teams[fetch_index][0]}")
                team_info.append(get_data(SPORT_URLS[fetch_index], teams[fetch_index], fetch_index))
                teams_with_data.append(team_has_data)
                teams_currently_playing.append(currently_playing)

            fetch_clock = ticks_add(fetch_clock, fetch_timer) # Reset Timer if display updated

        # Display Team Information
        if ticks_diff(ticks_ms(), display_clock) >= display_timer:
            if teams_with_data[display_index] and teams_currently_playing[display_index]:
                print(f"\n{teams[display_index][0]} is currently playing, updating display\n")

                for key, value in team_info[display_index].items():

                    if "network_logo" in key:
                        for network, file in network_logos.items():
                            if network in value: size = file[1]  # Index 1 is how much to decrease logo size

                    if "home_logo" in key or "away_logo" in key:
                        window[key].update(filename=value)
                    elif "network_logo" in key:
                        window[key].update(filename=value, subsample=size)
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

                    if "nba" in SPORT_URLS[display_index] and key == 'sport_specific_info':
                        window['sport_specific_info'].update(value=value, font=(FONT, 56))

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
    
    print("No Team Playing")
    fetch_timer = 180 * 1000 #  Put back to fetching every 3 minutes if no team playing
    return team_info

##################################
#                                #
#          Event Loop            #
#                                #
##################################
team_info = []
teams_with_data = []
display_index = 0
for fetch_index in range(len(teams)):
    print(f"\nFetching data for {teams[fetch_index][0]}")
    info, data, currently_playing = get_data(SPORT_URLS[fetch_index], teams[fetch_index], fetch_index, network_logos)
    team_info.append(info)
    teams_with_data.append(data)

event, values = window.read(timeout=5000)

while True:
    try:
        # Fetch Data
        if ticks_diff(ticks_ms(), fetch_clock) >= fetch_timer:
            teams_with_data.clear()
            team_info.clear()
            for fetch_index in range(len(teams)):
                print(f"\nFetching data for {teams[fetch_index][0]}")
                info, data, currently_playing = get_data(SPORT_URLS[fetch_index], teams[fetch_index], fetch_index, network_logos)
                team_info.append(info)
                teams_with_data.append(data)
                if currently_playing:
                    returned_data = team_currently_playing(window)
                    team_info = returned_data

            fetch_clock = ticks_add(fetch_clock, fetch_timer) # Reset Timer if display updated

        # Display Team Information
        if ticks_diff(ticks_ms(), display_clock) >= display_timer:
            if teams_with_data[display_index]:
                print(f"\nUpdating Display for {teams[display_index][0]}")
                window['sport_specific_info'].update(font=(FONT, 42))

                # Change Size of game info if length is too long
                if len(team_info[display_index]['info']) > 38:
                    window['info'].update(font=(FONT, 86))
                else:
                    window['info'].update(font=(FONT, INFO_TXT_SIZE))

                for key, value in team_info[display_index].items():

                    if "network_logo" in key:
                        for network, file in network_logos.items():
                            if network in value: size = file[1]  # Index 1 is how much to decrease logo size

                    if "home_logo" in key or "away_logo" in key:
                        window[key].update(filename=value)
                    elif "network_logo" in key:
                        window[key].update(filename=value, subsample=size)
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

        if event == sg.WIN_CLOSED: # TODO: Quit if any key pressed
            window.close()

    except:
        while not is_connected(router_ip):
            print("Internet connection is down, trying to reconnect...")
            reconnect(network_interface)
            time.sleep(20)  # Check every 20 seconds
        time.sleep(2)
        print("Internet connection is active")