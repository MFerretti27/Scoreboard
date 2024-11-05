'''
Script to Display a Scoreboard for your Favorite Teams 

@Requirements: Python must be installed and in PATH
@Author: Matthew Ferretti
'''


import pkg_resources
pip_packages = [p.project_name for p in pkg_resources.working_set]

try: 
    if "requests" not in str(pip_packages):
        print("requests not installed, installing...")
        os.system('pip install requests"')
    if "adafruit-circuitpython-ticks" not in str(pip_packages):
        print("adafruit_ticks not installed, installing...")
        os.system('pip3 install adafruit-circuitpython-ticks')
    if "FreeSimpleGUI" not in str(pip_packages):
        print("PySimpleGUI not installed, installing...")
        os.system('pip install FreeSimpleGUI')
except:
    print("Could not find and install nessasasry packages")
    print("please install manually by running commands below in terminal")
    print("\tpip install PySimpleGUI")
    print("\tpip install requests")
    print("\tpip3 install adafruit-circuitpython-ticks")

import FreeSimpleGUI as sg # pip install PySimpleGUI
import requests # pip install requests
import gc
import os
from adafruit_ticks import ticks_ms, ticks_add, ticks_diff # pip3 install adafruit-circuitpython-ticks
from PIL import Image


#######################################
#                                     #
# Edit Here to Change Teams Monitored #
#                                     #
#######################################

# The team names you want to follow, *must match* in order -> [team name, sport league, sport name]
teams = [
    ["Detroit Lions", "nfl", "football"],
    ["Detroit Tigers", "mlb", "baseball"],
    ["Kansas City Chiefs", "nfl", "football"],
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
last_displayed = -1 # Keeps track of what team was last displayed

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

    # Reset font and color if changed from last run
    window['home_score'].update(font=("Calibri", 104), text_color ='white')
    window['away_score'].update(font=("Calibri", 104), text_color ='white')

    # try:
    resp = requests.get(URL)
    response_as_json = resp.json()
    print(f"Looking for:  {team[0]}")
    for e in response_as_json["events"]:
        if team[0] in e["name"]:
            print(f"Found Game: {e["name"]}")
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
            venue = (response_as_json["events"][index]["competitions"][0]["venue"]["address"]["city"])
            
            # Check if Team is Currently Playing
            if "PM" not in str(team_info.get("info")) and "AM" not in str(team_info.get("info")):
                currently_playing = True

            if "Delayed" in str(team_info.get("info")) or "Postponed" in str(team_info.get("info")) or "Final" in str(team_info.get("info")):
                 currently_playing = False

            # if not currently playing and game hasn't been played
            else:
                team_info['info'].append(" @ " + venue)

            # # If looking at NFL team get this data (only if currently playing)
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
            
            if "mlb" in URL and currently_playing:
                if 'Bot' in str(team_info.get("info")): # Replace Bot with Bottom for baseball innings
                    team_info["info"] = 'Bottom'
            break
        else:
            index += 1

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
    '''Display one game that is playing, first team in team array has higher priority'''
    global teams, display_timer, display_clock, team_has_data, window

    last_displayed = -1 # Keeps track of what team was last displayed
    how_many_playing = []
    first_time = True
    for _ in range(len(teams)):
        how_many_playing.append(False)

    while True in how_many_playing or first_time:
        first_time = False
        if ticks_diff(ticks_ms(), display_clock) >= display_timer:
            for fetch_index in range(len(teams)):
                print(f"\nFetching data for {teams[fetch_index][0]}")
                team_info = get_data(SPORT_URLS[fetch_index], teams[fetch_index], fetch_index)

                if currently_playing and team_has_data:
                    how_many_playing[fetch_index] = True
                    print(f"\nIs {teams[fetch_index][0]} currently playing: {currently_playing}")

                    print("Updating Display")
                    if last_displayed is not fetch_index:
                        for key, value in team_info.items():
                            if "logo" in key:
                                window[key].update(filename=value)
                            else:
                                window[key].update(value=value)

                        last_displayed = fetch_index
                    display_clock = ticks_add(display_clock, display_timer)
                    window.read(timeout=0)
                    break
    return


##################################
#                                #
#          Set Up GUI            #
#                                #
##################################
sg.theme("black")

home_record_layout =[
    [sg.Image("sport_logos/team0_logos/DET.png", subsample=1, key='home_logo')],
    [sg.Text("Home Record",font=("Calibri", 72), key='home_record')]
    ]

away_record_layout =[
    [sg.Image("sport_logos/team0_logos/PIT.png", subsample=1, key='away_logo')],
    [sg.Text("Away Record",font=("Calibri", 72), key='away_record')]
    ]

score_layout =[
    [sg.Text("24",font=("Calibri", 104), key='away_score'),
     sg.Text("-",font=("Calibri", 72), key='hyphen'),
     sg.Text("24",font=("Calibri", 104), key='home_score')],
    ]

info_layout = [[sg.Text("Created by: Matthew Ferretti",font=("Calibri", 72), key='info')],]

layout = [[
    sg.Push(),
    sg.Column(away_record_layout, element_justification='center'),
    sg.Column(score_layout, element_justification='center'),
    sg.Column(home_record_layout, element_justification='center'),
    sg.Push()
    ],
    [sg.Push(), sg.Text("Created by:",font=("Calibri", 72), key='sport_specific_info'), sg.Push()],[sg.VPush()],
    [sg.VPush()], [sg.Push(), sg.Text("Matthew Ferretti",font=("Calibri", 72), key='info'), sg.Push()],[sg.VPush()]
    ]

# Create the window
window = sg.Window("Scoreboard", layout, grab_anywhere=True, resizable=True).Finalize() # , no_titlebar=True
window.Maximize()


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
    team_info.append(get_data(SPORT_URLS[fetch_index], teams[fetch_index], fetch_index))
    teams_with_data.append(team_has_data)

while True:
    event, values = window.read(timeout=0)

    # Fetch Data
    if ticks_diff(ticks_ms(), fetch_clock) >= fetch_timer:
        teams_with_data.clear()
        team_info.clear()
        for fetch_index in range(len(teams)):
            print(f"\nFetching data for {teams[fetch_index][0]}")
            team_info.append(get_data(SPORT_URLS[fetch_index], teams[fetch_index], fetch_index))
            teams_with_data.append(team_has_data)
            # if currently_playing:
            #     priority_game()

        fetch_clock = ticks_add(fetch_clock, fetch_timer) # Reset Timer if display updated

    # Display Team Information
    if ticks_diff(ticks_ms(), display_clock) >= display_timer:
        if teams_with_data[display_index]:
            print(f"Updating Display for {teams[display_index][0]}")
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
                    print(f"\nskipping displaying {teams[(original_index + x) % len(teams)][0]}, current display index: {display_index}")
                elif teams_with_data[(original_index + x) % len(teams)] == True and x != 0:
                    print(f"Found next team that has data {teams[(original_index + x) % len(teams)][0]}\n")
                    break
        else:
            print(f"{teams[display_index][0]} has no Data and wont Display")

        display_index = (display_index + 1) % len(teams)
        display_clock = ticks_add(display_clock, display_timer)

    if event == sg.WIN_CLOSED:
        break

window.close()