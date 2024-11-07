'''
Script to Display a Scoreboard for your Favorite Teams 

@Requirements: Python must be installed and in PATH
@Author: Matthew Ferretti
'''


import pkg_resources
import os
import subprocess
import platform
import sys

pip_packages = [p.project_name for p in pkg_resources.working_set]

# Check if the virtual environment directory exists
if not os.path.exists('venv'):
    print("Virtual environment '{venv}' not found. Creating a new one...")
    # Create the virtual environment
    subprocess.check_call([sys.executable, '-m', 'venv', "venv"])
    print("Virtual environment 'venv' created successfully.")

    if platform.system() == 'Windows':
        os.system("venv\\Scripts\\activate")
    else:
        os.system("source venv/bin/activate")
else:
    print("Virtual environment 'venv' already exists.")

# python_installed = os.popen('python3 --version"').read()
# if 'not found' in python_installed:
#     raise ValueError("Python is not installed, please install python")

# try: 
#     if "requests" not in str(pip_packages):
#         print("sudo requests not installed, installing...")
#         os.system('apt install python3-requests"')
#     if "adafruit-circuitpython-ticks" not in str(pip_packages):
#         print("adafruit_ticks not installed, installing...")
#         os.system('sudo apt install python3-adafruit-circuitpython-ticks')
#     if "FreeSimpleGUI" not in str(pip_packages):
#         print("sudo PySimpleGUI not installed, installing...")
#         os.system('sudo apt install python3-FreeSimpleGUI')
# except Exception:
#     print("Could not find and install nessasasry packages")
#     print("please install manually by running commands below in terminal")
#     print("\tpip install PySimpleGUI")
#     print("\tpip install requests")
#     print("\tpip3 install adafruit-circuitpython-ticks")

import FreeSimpleGUI as sg # pip install PySimpleGUI
import requests # pip install requests
import gc
from adafruit_ticks import ticks_ms, ticks_add, ticks_diff # pip3 install adafruit-circuitpython-ticks
from PIL import Image
import datetime
import time

if os.environ.get('DISPLAY','') == '':
    print('no display found. Using :0.0')
    os.environ.__setitem__('DISPLAY', ':0.0')


#######################################
#                                     #
# Edit Here to Change Teams Monitored #
#                                     #
#######################################

# The team names you want to follow, *must match* in order -> [team name, sport league, sport name]
teams = [
    ["Detroit Lions", "nfl", "football"],
    ["Detroit Tigers", "mlb", "baseball"],
    ["Pittsburgh Steelers", "nfl", "football"],
    ["Detroit Red Wings", "nhl", "hockey"],
    ["Detroit Pistons", "nba", "basketball"]
]

############################
#                          #
#          Setup           #
#                          #
############################
SPORT_URLS = []
team_has_data = False
currently_playing = False
display_clock = ticks_ms() # Start Timer for Switching Display
display_timer = 30 * 1000 # how often the display should update in seconds
fetch_clock = ticks_ms() # Start Timer for Switching Display
fetch_timer = 180 * 1000 # how often the display should update in seconds

for i in range(len(teams)):

    sport_league = teams[i][1]
    sport_name = teams[i][2]

    # add API URLs
    URL = (
    f"https://site.api.espn.com/apis/site/v2/sports/{sport_name}/{sport_league}/scoreboard"
    )
    SPORT_URLS.append(URL)


##################################
#                                #
#   Grab all Logos (done once)   #
#                                #
##################################
# Create a base directory to store the logos if it doesn't exist
if not os.path.exists('sport_logos'):
    os.makedirs('sport_logos')
    logo_directories = []

    # Loop through each league to get the teams
    for i in range(len(teams)):
        logo_directories.append(f"team{i}_logos")
        sport_league = teams[i][1]
        sport_name = teams[i][2]

        # Create a directory for the current sport if it doesn't exist
        sport_dir = os.path.join('sport_logos', logo_directories[i])
        if not os.path.exists(sport_dir):
            os.makedirs(sport_dir)

        # Fetch the JSON data
        url = f"https://site.api.espn.com/apis/site/v2/sports/{sport_name}/{sport_league}/teams"
        response = requests.get(url)
        data = response.json()

        # Extract team data
        teams_data = data.get('sports', [{}])[0].get('leagues', [{}])[0].get('teams', [])

        # Download, process, resize, and save each logo
        for team in teams_data:
            abbreviation = team['team']['abbreviation']
            logo_url = team['team']['logos'][0]['href']

            print(f"Downloading logo for {abbreviation} from {teams[i][1]}...")

            img_path_png = os.path.join(sport_dir, f"{abbreviation}.png")
            response = requests.get(logo_url, stream=True)
            with open(img_path_png, 'wb') as file:
                for chunk in response.iter_content(chunk_size=1024):
                    file.write(chunk)

            # Open, resize, and save the image with PIL
            with Image.open(img_path_png) as the_img:
                the_img.save(img_path_png)

    if os.path.exists('sport_logos'):
        print("All logos have been downloaded!")


##################################
#                                #
#      Grab ESPN API Data        #
#                                #
##################################
def get_data(URL, team, sport):
    '''The actual API and display function'''
    global team_has_data, currently_playing, window
    team_has_data = False
    index = 0
    names = []
    team_info = {}
    team_info['sport_specific_info'] = ''
    currently_playing = False

    # Reset font and color if changed from last run
    window['home_score'].update(font=("Calibri", 104), text_color ='white')
    window['away_score'].update(font=("Calibri", 104), text_color ='white')

    # try:
    resp = requests.get(URL)
    response_as_json = resp.json()
    print(f"Looking for:  {team[0]}")
    for e in response_as_json["events"]:
        if team[0] in e["name"]:
            team = e["name"]
            print(f"Found Game: {team}")
            team_has_data = True

            names.append(response_as_json["events"][index]["competitions"]
                            [0]["competitors"][0]["team"]["abbreviation"])
            names.append(response_as_json["events"][index]["competitions"]
                            [0]["competitors"][1]["team"]["abbreviation"])
            team_info['home_score'] = (response_as_json["events"][index]["competitions"]
                                        [0]["competitors"][0]["score"])
            team_info['away_score'] = (response_as_json["events"][index]["competitions"]
                                        [0]["competitors"][1]["score"])
            team_info['away_record'] = (response_as_json["events"][index]["competitions"]
                                        [0]["competitors"][0]["records"][0]["summary"])
            team_info['home_record'] = (response_as_json["events"][index]["competitions"]
                                        [0]["competitors"][1]["records"][0]["summary"])
            team_info['info'] = (response_as_json["events"][index]["status"]["type"]["shortDetail"])
            venue = (response_as_json["events"][index]["competitions"][0]["venue"]["fullName"])
            
            # Check if Team is Currently Playing
            if "PM" not in str(team_info['info']) and "AM" not in str(team_info['info']):
                currently_playing = True

            if "Delayed" in str(team_info['info']) or "Postponed" in str(team_info['info']) or "Final" in str(team_info['info']):
                 currently_playing = False
                 team_info['info'] = str(team_info['info']).upper()

            # if not currently playing and game hasn't been played
            elif not currently_playing:
                team_info['info'] = str(team_info['info'] + "@ " + venue)

            # If looking at NFL team get this data (only if currently playing)
            if "nfl" in URL and currently_playing:
                nfl_data = e['competitions'][0]
                down = nfl_data.get('situation', {}).get('shortDownDistanceText')
                red_zone = nfl_data.get('situation', {}).get('isRedZone')
                spot =  nfl_data.get('situation', {}).get('possessionText')
                possession =  nfl_data.get('situation', {}).get('possession')
                if down is not None and spot is not None:
                    team_info['sport_specific_info'] = str(down) + " on " + str(spot)

                # Find who has possession and update display to represent possession
                if possession.find(names[0]) > possession.find(names[1]) and possession is not None: # Home Team
                    window['home_score'].update(font=("Calibri", 104, "underline"))
                    if red_zone:
                        window['home_score'].update(text_color ='red')
                elif possession.find(names[1]) > possession.find(names[0]) and possession is not None:
                    window['away_score'].update(font=("Calibri", 104, "underline"))
                    if red_zone:
                        window['away_score'].update(text_color ='red')
            

            # If looking at NBA team get this data (only if currently playing)
            if "nba" in URL and currently_playing:
                nba_data = e['competitions']
                home_avg_rebound_pct = ((nba_data[0]["statistics"][1]["displayValue"]))
                home_field_goal_pct = ((nba_data[0]["statistics"][5]["displayValue"]))
                home_3pt_pct = ((nba_data[0]["statistics"][15]["displayValue"]))

                away_rebound_pct = ((nba_data[1]["statistics"][1]["displayValue"]))
                away_field_goal_pct = ((nba_data[1]["statistics"][5]["displayValue"]))
                away_3pt_pct = ((nba_data[1]["statistics"][15]["displayValue"]))

                team_info['sport_specific_info'] = \
                    "RB%:" + home_avg_rebound_pct + " FG%:" + home_field_goal_pct + " 3PT%:" + home_3pt_pct + \
                        "\tRB%:" + away_rebound_pct + " FG%:" + away_field_goal_pct + " 3PT%:" + away_3pt_pct

            # If looking at MLB team get this data (only if currently playing)
            if "mlb" in URL and currently_playing:
                if 'Bot' in str(team_info.get("info")): # Replace Bot with Bottom for baseball innings
                    team_info["info"].replace('bot', 'Bottom')
            break
        else:
            index += 1

    # Makes sport specific info display above clock if playing
    if currently_playing:
        temp = team_info["info"]
        team_info["info"] = team_info['sport_specific_info']
        team_info['sport_specific_info'] = temp

    if team_has_data:
        # Remove Timezone Characters in info
        if 'EDT' in team_info.get("info"): team_info["info"] = team_info["info"].replace('EDT', '')
        elif 'EST' in team_info["info"]: team_info["info"] = team_info["info"].replace('EST', '')

        if team[1] is names[0]: # Your team has a Home Game
            team_info["away_logo"] = (f"sport_logos/team" + str(sport) + "_logos/" + names[0] + ".png")
            team_info["home_logo"] = (f"sport_logos/team" + str(sport) + "_logos/" + names[1] + ".png")
        else:
            team_info["away_logo"] = (f"sport_logos/team" + str(sport) + "_logos/" + names[1] + ".png")
            team_info["home_logo"] = (f"sport_logos/team" + str(sport) + "_logos/" + names[0] + ".png")
    else:
        currently_playing = False

    resp.close()

    # except:
    #     print(f"Failed to get data for {team[0]}")

    gc.collect()
    return team_info

def priority_game():
    '''Display only games that are playing'''
    global teams, display_timer, display_clock, fetch_clock, fetch_timer, window

    teams_currently_playing = []
    first_time = True
    team_info = []
    teams_with_data = []
    display_index = 0

    while True in teams_currently_playing or first_time:
        first_time = False
        event, values = window.refresh()
        if ticks_diff(ticks_ms(), fetch_clock) >= fetch_timer:
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
                print(f"{teams[display_index][0]} is currently playing, updating display")
                for key, value in team_info[display_index].items():
                    if "logo" in key:
                        window[key].update(filename=value)
                    else:
                        window[key].update(value=value)

                # Find next team to display (skip teams with no data)
                original_index = display_index
                for x in range(len(teams)):
                    if teams_currently_playing[(original_index + x) % len(teams)] == False:
                        display_index = (display_index + 1) % len(teams)
                        print(f"\nskipping displaying {teams[(original_index + x) % len(teams)][0]}, current display index: {display_index}")
                    elif teams_currently_playing[(original_index + x) % len(teams)] == True and x != 0:
                        print(f"Found next team that is currently playing {teams[(original_index + x) % len(teams)][0]}\n")
                        display_index = (display_index + x) % len(teams)
                        break
                    else:
                        display_index = display_index
                        break
            else:
                print(f"{teams[display_index][0]} has no Data and wont Display")

            display_index = (display_index + 1) % len(teams)
            display_clock = ticks_add(display_clock, display_timer)
    return


##################################
#                                #
#          Set Up GUI            #
#                                #
##################################
sg.theme("black")

home_record_layout =[
    [sg.Image("sport_logos/team0_logos/DET.png", key='home_logo')],
    [sg.Text("0-0",font=("Calibri", 84), key='home_record')]
    ]

away_record_layout =[
    [sg.Image("sport_logos/team0_logos/PIT.png", key='away_logo'), sg.Push()],
    [sg.Text("0-0",font=("Calibri", 84), key='away_record')]
    ]

score_layout =[
    [sg.Text("24",font=("Calibri", 120), key='away_score', pad=(0,0)),
     sg.Text("-",font=("Calibri", 84), key='hyphen'),
     sg.Text("24",font=("Calibri", 120), key='home_score', pad=(0,0))],
    ]

info_layout = [[sg.Text("Created by: Matthew Ferretti",font=("Calibri", 72), key='info')],]

layout = [[
    sg.Push(),
    sg.Column(away_record_layout, element_justification='center', pad=(75,60)),
    sg.Column(score_layout, element_justification='center'),
    sg.Column(home_record_layout, element_justification='center', pad=(75,60)),
    sg.Push()
    ],
    [sg.VPush()],[sg.Push(), sg.Text("Created by:",font=("Calibri", 72), key='sport_specific_info'), sg.Push()],
    [sg.VPush()],[sg.Push(), sg.Text("Matthew Ferretti",font=("Calibri", 72), key='info'), sg.Push()],[sg.VPush()],[sg.Push()],
    [sg.Push(), sg.Text("Created by: Matthew Ferretti",font=("Calibri", 10), key='personal')]
    ]

# Create the window
window = sg.Window("Scoreboard", layout, no_titlebar=True).Finalize()
window.Maximize()


##################################
#                                #
#          Event Loop            #
#                                #
##################################
team_info = []
teams_with_data = []
display_index = 0
clock_displayed = False
for fetch_index in range(len(teams)):
    print(f"\nFetching data for {teams[fetch_index][0]}")
    team_info.append(get_data(SPORT_URLS[fetch_index], teams[fetch_index], fetch_index))
    teams_with_data.append(team_has_data)

while True:
    event, values = window.read(timeout=50000)

    # Fetch Data
    if ticks_diff(ticks_ms(), fetch_clock) >= fetch_timer:
        teams_with_data.clear()
        team_info.clear()
        for fetch_index in range(len(teams)):
            print(f"\nFetching data for {teams[fetch_index][0]}")
            team_info.append(get_data(SPORT_URLS[fetch_index], teams[fetch_index], fetch_index))
            teams_with_data.append(team_has_data)
            if currently_playing:
                priority_game()

        fetch_clock = ticks_add(fetch_clock, fetch_timer) # Reset Timer if display updated

    # Display Team Information
    if ticks_diff(ticks_ms(), display_clock) >= display_timer:
        if teams_with_data[display_index]:
            print(f"\nUpdating Display for {teams[display_index][0]}")
            for key, value in team_info[display_index].items():
                if "logo" in key:
                    window[key].update(filename=value)
                else:
                    window[key].update(value=value)

            # Find next team to display (skip teams with no data)
            original_index = display_index
            for x in range(len(teams)):
                if teams_with_data[(original_index + x) % len(teams)] == False:
                    display_index = (display_index + 1) % len(teams)
                    print(f"skipping displaying {teams[(original_index + x) % len(teams)][0]}, has no data")
                elif teams_with_data[(original_index + x) % len(teams)] == True and x != 0:
                    print(f"Found next team that has data {teams[(original_index + x) % len(teams)][0]}\n")
                    break
        else:
            print(f"{teams[display_index][0]} has no Data and wont Display")

        display_index = (display_index + 1) % len(teams)
        display_clock = ticks_add(display_clock, display_timer)

    # If there is no data for any team display clock
    if True not in teams_with_data:
        clock_displayed = True
        current_time = datetime.datetime.now()
        if current_time.hour > 12:
            hour = current_time.hour - 12
        date = str(current_time.month) + '/' + str(current_time.day) + '/' + str(current_time.year)
        window["hyphen"].update(value=':', font=("Calibri", 104))
        window["home_score"].update(value=current_time.minute, font=("Calibri", 204))
        window["away_score"].update(value=hour, font=("Calibri", 204))
        window["home_record"].update(value='')
        window["away_record"].update(value='')
        window["away_logo"].update(filename='')
        window["home_logo"].update(filename="sport_logos/team0_logos/DET.png")
        window["info"].update(value=date,font=("Calibri", 104))
        window["sport_specific_info"].update(value=' ')

    elif clock_displayed: # Reset Font if theres data to display
        window["hyphen"].update(value='-',font=("Calibri", 72))
        window["home_score"].update(font=("Calibri", 104))
        window["away_score"].update(font=("Calibri", 104))
        window["info"].update(font=("Calibri", 72))

    if event == sg.WIN_CLOSED:
        break

window.close()