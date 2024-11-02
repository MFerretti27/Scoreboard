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
    if "PySimpleGUI" not in str(pip_packages):
        print("PySimpleGUI not installed, installing...")
        os.system('pip install PySimpleGUI')
except:
    print("Could not find and install nessasasry packages")
    print("please install manually by running commands below in terminal")
    print("\tpip install PySimpleGUI")
    print("\tpip install requests")
    print("\tpip3 install adafruit-circuitpython-ticks")

import PySimpleGUI as sg # pip install PySimpleGUI
import requests # pip install requests
import gc
import os
from adafruit_ticks import ticks_ms, ticks_add, ticks_diff # pip3 install adafruit-circuitpython-ticks
from PIL import Image


sport_name = ["football", "baseball", "football", "hockey", "basketball"]  # the name of the sports you want to follow
sport_league = ["nfl", "mlb", "nfl", "nhl", "nba"]  # the name of the corresponding leagues you want to follow
bitmap_directories = ["team0_logos", "team1_logos", "team2_logos", "team3_logos", "team4_logos"] # Folders Logos are stored in

# the team names you want to follow, must match the order of sport/league arrays
# include full name and then abbreviation (usually city/region)
team0 = ["Detroit Lions", "DET"]
team1 = ["Detroit Tigers", "DET"]
team2 = ["Pittsburgh Steelers", "PIT"]
team3 = ["Detroit Red Wings", "DET"]
team4 = ["Detroit Pistons", "DET"]

# add API URLs
SPORT_URLS = []
for i in range(5):
    d = (
    f"https://site.api.espn.com/apis/site/v2/sports/{sport_name[i]}/{sport_league[i]}/scoreboard"
    )
    SPORT_URLS.append(d)

# arrays for teams, logos
teams = [team0, team1, team2, team3, team4]
teams_playing = [True, True, True, True, True] # Set all teams to playing initially
team_has_data = False
currently_playing = False
display_clock = ticks_ms() # Start Timer for Switching Display
display_timer = 30 * 1000 # how often the display should update in seconds
last_displayed = -1


##################################
#                                #
#   Grab all Logos (done once)   #
#                                #
##################################
# Create a base directory to store the logos if it doesn't exist
if not os.path.exists('sport_logos'):
    os.makedirs('sport_logos')

    # Loop through each league to get the teams
    for i in range(len(sport_league)):
        sport = sport_name[i]
        league = sport_league[i]

        # Create a directory for the current sport if it doesn't exist
        sport_dir = os.path.join('sport_logos', bitmap_directories[i])
        if not os.path.exists(sport_dir):
            os.makedirs(sport_dir)

        # Set the URL for the JSON file for the current league
        url = f"https://site.api.espn.com/apis/site/v2/sports/{sport}/{league}/teams"

        # Fetch the JSON data
        response = requests.get(url)
        data = response.json()

        # Extract team data
        teams_data = data.get('sports', [{}])[0].get('leagues', [{}])[0].get('teams', [])

        # Download, process, resize, and save each logo
        for team in teams_data:
            abbreviation = team['team']['abbreviation']
            logo_url = team['team']['logos'][0]['href']

            print(f"Downloading logo for {abbreviation} from {league}...")

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
def get_data(data, team, sport):
    '''The actual API and display function'''
    global info, team_has_data, currently_playing
    team_has_data = False
    away_logo = None
    home_logo = None
    home_record = 0
    away_record = 0
    home_score = 0
    away_score = 0
    index = 0
    names = []
    gc.collect()
    resp = requests.get(data)
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
            home_score = (response_as_json["events"][index]["competitions"]
                            [0]["competitors"][0]["score"])
            away_score = (response_as_json["events"][index]["competitions"]
                            [0]["competitors"][1]["score"])
            info = (response_as_json["events"][index]["status"]["type"]["shortDetail"])
            home_record = (response_as_json["events"][index]["competitions"]
                            [0]["competitors"][0]["records"][0]["summary"])
            away_record = (response_as_json["events"][index]["competitions"]
                            [0]["competitors"][1]["records"][0]["summary"])
            break
        else:
            index += 1
    
    # Check if Team is Currently Playing
    if "PM" not in str(info) and "AM" not in str(info):
            currently_playing = True
    if ("Delayed" in str(info)) or ("Postponed" in str(info)) or ("Final" in str(info)):
            currently_playing = False
    
    if 'Bot' in info: # Replace Bot with Bottom for baseball innings
        info = info.replace('Bot', 'Bottom')
    
    # Remove Timezone Characters in info
    if 'EDT' in info:
        info = info.replace('EDT', '')
    if 'EST' in info:
        info = info.replace('EST', '')

    if team_has_data:
        if team[1] is names[0]: # Your team has a Home Game
            away_logo = (f"sport_logos/team" + str(sport) + "_logos/" + names[0] + ".png")
            home_logo = (f"sport_logos/team" + str(sport) + "_logos/" + names[1] + ".png")
        else:
            away_logo = (f"sport_logos/team" + str(sport) + "_logos/" + names[1] + ".png")
            home_logo = (f"sport_logos/team" + str(sport) + "_logos/" + names[0] + ".png")

    resp.close()
    gc.collect()
    return home_logo, away_logo, home_record, away_record, home_score, away_score

def priority_game(team):
    '''Display one game that is playing, first team in team array has higher priority'''
    display_clock = ticks_ms() # Start Timer for Switching Display
    display_timer = 30 * 1000 # how often the display should update in seconds
    while currently_playing:
        if ticks_diff(ticks_ms(), display_clock) >= display_timer:
            print(f"\nFetching data for {teams[team]}")
            home_logo, away_logo, home_record, away_record, home_score, away_score = \
            get_data(SPORT_URLS[team], teams[team], team)

            print(f"\nIs {teams[team]} currently playing: {currently_playing}")

            print("Updating Display")
            window["home_score"].update(value=home_score)
            window["away_score"].update(value=away_score)
            window["home_record"].update(value=home_record)
            window["away_record"].update(value=away_record)
            window["home_image"].update(filename=home_logo)
            window["away_image"].update(filename=away_logo)
            window["info"].update(value=info)

            display_clock = ticks_add(display_clock, display_timer)

    teams_playing[team] = False
    return


##################################
#                                #
#          Set Up GUI            #
#                                #
##################################
sg.theme("black")

home_record_layout =[
    [sg.Image("sport_logos/team0_logos/DET.png", subsample=1, key='home_image')],
    [sg.Text("Home Record",font=("Calibri", 72), key='home_record')]
    ]

away_record_layout =[
    [sg.Image("sport_logos/team0_logos/PIT.png", subsample=1, key='away_image')],
    [sg.Text("Away Record",font=("Calibri", 72), key='away_record')]
    ]

score_layout =[
    [sg.Text("24",font=("Calibri", 104), key='away_score'),
     sg.Text("-",font=("Calibri", 72), key='hyphen'),
     sg.Text("24",font=("Calibri", 104), key='home_score')],
    ]

info_layout = [[sg.Text("Status of game",font=("Calibri", 72), key='info')],]

layout = [[
    sg.Push(),
    sg.Column(away_record_layout, element_justification='center'),
    sg.Column(score_layout, element_justification='center'),
    sg.Column(home_record_layout, element_justification='center'),
    sg.Push()
    ],
    [sg.VPush()], [sg.Push(), sg.Text("Status of game",font=("Calibri", 72), key='info'), sg.Push()],[sg.VPush()]
    ]

# Create the window
window = sg.Window("Scoreboard", layout, grab_anywhere=True, resizable=True).Finalize() # , no_titlebar=True
window.Maximize()


##################################
#                                #
#          Event Loop            #
#                                #
##################################
while True:
    event, values = window.read(timeout=0)

    if ticks_diff(ticks_ms(), display_clock) >= display_timer:
        for fetch_index in range(len(teams)):
            print(f"\nFetching data for {teams[fetch_index]}")
            home_logo, away_logo, home_record, away_record, home_score, away_score = \
                get_data(SPORT_URLS[fetch_index], teams[fetch_index], fetch_index)

            if not team_has_data:
                teams_playing[fetch_index] = False

            elif currently_playing:
                priority_game(fetch_index)

            else:
                teams_playing[fetch_index] = True
                print(f"\n{teams[fetch_index]} has data index: {teams_playing[fetch_index]}")

                if fetch_index is not last_displayed:
                    print("Updating Display")
                    window["home_score"].update(value=home_score)
                    window["away_score"].update(value=away_score)
                    window["home_record"].update(value=home_record)
                    window["away_record"].update(value=away_record)
                    window["home_image"].update(filename=home_logo)
                    window["away_image"].update(filename=away_logo)
                    window["info"].update(value=info)

                    last_displayed = fetch_index
                    display_clock = ticks_add(display_clock, display_timer) # Reset Timer
                    break

    if event == sg.WIN_CLOSED:
        break

window.close()