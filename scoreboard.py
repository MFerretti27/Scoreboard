'''
Script to Display a Scoreboard for your Favorite Teams 

@Requirements: Python must be installed and in PATH
@Author: Matthew Ferretti
'''

# Common imports (should be on all computers)
import os
import subprocess
import platform
import sys
import re
import datetime
import time
import gc

# Check if you are currently in Virtual Environment, if not exit
if sys.prefix != sys.base_prefix:
    print("\tYou are currently in a virtual environment.")
    if platform.system() == 'Windows':
        output = subprocess.check_output("ipconfig", encoding="utf-8")
        match = re.search(r"Default Gateway[ .:]*([\d.]+)", output)
        router_ip = match.group(1)
    else:
        output = subprocess.check_output("ip route", shell=True, encoding="utf-8")
        match = re.search(r"default via ([\d.]+)", output)
        router_ip = match.group(1)
else:
    print("Please go into virtual Environment by running main.py")
    exit()

# Uncommon imports that need to be installed
import FreeSimpleGUI as sg # pip install FreeSimpleGUI
import requests # pip install requests
from adafruit_ticks import ticks_ms, ticks_add, ticks_diff # pip3 install adafruit-circuitpython-ticks
from PIL import Image  # pip install pillow
import psutil  # pip install psutil

# Get Network Interface for trying to reconnect on network failure
interfaces = psutil.net_if_stats()  # Get interface stats (up/down status)
io_counters = psutil.net_io_counters(pernic=True)  # Get I/O data per interface
for interface, stats in interfaces.items():
    if interface == "lo":  # Skip the loopback interface
        continue
    if stats.isup:  # Check if interface is up
        # Check if there has been any data transmitted or received
        data = io_counters.get(interface)
        if data and (data.bytes_sent > 0 or data.bytes_recv > 0):
            network_interface = interface

print(f"Routers IP address {router_ip}, Current Network Interface {network_interface}")
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
FONT = "Calibri"
SCORE_TXT_SIZE = 140
INFO_TXT_SIZE = 96
RECORD_TXT_SIZE = 96
TEAM_LOGO_SIZE = 1.5

SPORT_URLS = []
team_has_data = False
currently_playing = False
display_clock = ticks_ms() # Start Timer for Switching Display
display_timer = 25 * 1000 # how often the display should update in seconds
fetch_clock = ticks_ms() # Start Timer for Switching Display
fetch_timer = 180 * 1000 # how often the display should update in seconds

network_logo_file_location = {
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

    # add API URLs
    URL = (f"https://site.api.espn.com/apis/site/v2/sports/{sport_name}/{sport_league}/scoreboard")
    SPORT_URLS.append(URL)


##################################
#                                #
#   Grab all Logos (done once)   #
#                                #
##################################
def resize_image(image_path, sport_dir, abbreviation, scale_factor):
    # Open an image file using Pillow
    img = Image.open(image_path)
    
    # Calculate new size based on scale factor
    width, height = img.size
    new_width = int(width * scale_factor)
    new_height = int(height * scale_factor)
    
    # Resize the image
    img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    new_path_png = os.path.join(sport_dir, f"{abbreviation}.png")
    img_resized.save(new_path_png)

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

            img_path_png = os.path.join(sport_dir, f"{abbreviation}_Original.png")
            response = requests.get(logo_url, stream=True)
            with open(img_path_png, 'wb') as file:
                for chunk in response.iter_content(chunk_size=1024):
                    file.write(chunk)

            # Open, resize, and save the image with PIL
            with Image.open(img_path_png) as the_img:
                resize_image(img_path_png, sport_dir, abbreviation, TEAM_LOGO_SIZE)

            # Delete the original .png file
            os.remove(img_path_png)

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
    window['home_score'].update(font=(FONT, SCORE_TXT_SIZE), text_color ='white')
    window['away_score'].update(font=(FONT, SCORE_TXT_SIZE), text_color ='white')
    window['sport_specific_info'].update(font=(FONT, 72))

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
                                        [0]["competitors"][1]["records"][0]["summary"])
            team_info['home_record'] = (response_as_json["events"][index]["competitions"]
                                        [0]["competitors"][0]["records"][0]["summary"])
            team_info['info'] = (response_as_json["events"][index]["status"]["type"]["shortDetail"])
            venue = (response_as_json["events"][index]["competitions"][0]["venue"]["fullName"])
            broadcast = (response_as_json["events"][index]["competitions"][0]["broadcast"])
            home_team_id = response_as_json["events"][index]["competitions"][0]["competitors"][0]["id"]
            away_team_id = response_as_json["events"][index]["competitions"][0]["competitors"][1]["id"]

            for network, filepath in network_logo_file_location.items():
                if network in broadcast: 
                    team_info['network_logo'] = filepath[0] # Index 0 is filepath
                    break
                else:  # If it cant find logo use these as defaults
                    if "nfl" in URL: team_info['network_logo'] = "Networks/NFL_NET.png"
                    elif "nba" in URL: team_info['network_logo'] = "Networks/NBA_League.png"
                    elif "mlb" in URL: team_info['network_logo'] = "Networks/MLB_Network.png"
                    elif "nhl" in URL: team_info['network_logo'] = "Networks/NHL_Net.png"

            # Check if Team is Currently Playing
            if "PM" not in str(team_info['info']) and "AM" not in str(team_info['info']):
                currently_playing = True

            # Check if Team is Done Playing
            if "Delayed" in str(team_info['info']) or "Postponed" in str(team_info['info']) or "Final" in str(team_info['info']):
                 currently_playing = False
                 team_info['info'] = str(team_info['info']).upper()

            # Check if Game hasn't been played yet
            elif not currently_playing:
                team_info['info'] = str(team_info['info'] + "@ " + venue)
                overUnder = (response_as_json["events"][index]["competitions"][0]["odds"][0]["overUnder"])
                spread = (response_as_json["events"][index]["competitions"][0]["odds"][0]["details"])
                if "nhl" in URL:
                    team_info['sport_specific_info'] = f"MoneyLine: {spread} \t OverUnder: {overUnder}"
                else:
                    team_info['sport_specific_info'] = f"Spread: {spread} \t OverUnder: {overUnder}"

            # If looking at NFL team get this data (only if currently playing)
            if "nfl" in URL and currently_playing:
                nfl_data = response_as_json["events"][index]["competitions"][0]
                down = nfl_data.get('situation', {}).get('shortDownDistanceText')
                red_zone = nfl_data.get('situation', {}).get('isRedZone')
                spot =  nfl_data.get('situation', {}).get('possessionText')
                possession =  nfl_data.get('situation', {}).get('possession')
                if down is not None and spot is not None:
                    team_info['sport_specific_info'] = str(down) + " on " + str(spot)

                team_info['home_possession'] = False
                team_info['away_possession'] = False
                team_info['home_redzone'] = False
                team_info['away_redzone'] = False
                # Find who has possession and pass information to represent possession
                if possession is not None and possession == home_team_id:
                    team_info['home_possession'] = True
                    if red_zone:
                        team_info['home_redzone'] = True
                elif possession is not None and possession == away_team_id:
                    team_info['away_possession'] =  True
                    if red_zone: 
                        team_info['away_redzone'] = True

                temp = str(team_info["info"])
                team_info["info"] = str(team_info['sport_specific_info'])
                team_info['sport_specific_info'] = temp

            # If looking at NBA team get this data (only if currently playing)
            if "nba" in URL and currently_playing:
                home_field_goal_pct = ((response_as_json["events"][index]["competitions"][0]["competitors"]
                                        [0]["statistics"][5]["displayValue"]))
                home_3pt_pct = ((response_as_json["events"][index]["competitions"][0]["competitors"]
                                        [0]["statistics"][15]["displayValue"]))

                away_field_goal_pct = ((response_as_json["events"][index]["competitions"][0]["competitors"][1]["statistics"][5]["displayValue"]))
                away_3pt_pct = ((response_as_json["events"][index]["competitions"][0]["competitors"][1]["statistics"][15]["displayValue"]))

                team_info['sport_specific_info'] = \
                    "FG% " + home_field_goal_pct + "  3PT% " + home_3pt_pct + \
                    "\t\t   FG% " + away_field_goal_pct + "  3PT% " + away_3pt_pct

            # If looking at MLB team get this data (only if currently playing)
            if "mlb" in URL and currently_playing:
                 # outs = (response_as_json["events"][index]["competitions"][0]["outsText"])
                if 'Bot' in str(team_info.get("info")): # Replace Bot with Bottom for baseball innings
                    team_info["info"].replace('bot', 'Bottom')
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
    gc.collect()
    return team_info


##########################################
#                                        #
#  Display only Teams currently playing  #
#                                        #
##########################################
def team_currently_playing(window):
    '''Display only games that are playing'''
    global teams, display_clock, fetch_clock, network_logo_file_location

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
                        for network, file in network_logo_file_location.items():
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
#          Set Up GUI            #
#                                #
##################################
sg.theme("black")

home_record_layout =[
    [sg.Image("sport_logos/team0_logos/DET.png", key='home_logo')],
    [sg.Text("0-0",font=(FONT, RECORD_TXT_SIZE), key='home_record')]
    ]

away_record_layout =[
    [sg.Image("sport_logos/team0_logos/PIT.png", key='away_logo'), sg.Push()],
    [sg.Text("0-0",font=(FONT, RECORD_TXT_SIZE), key='away_record')]
    ]

score_layout =[[sg.Text(" ",font=(FONT, 50), key='blank_space', pad=(0,100))],
    [sg.Text("24",font=(FONT, SCORE_TXT_SIZE), key='away_score'),
     sg.Text("-",font=(FONT, 84), key='hyphen'),
     sg.Text("24",font=(FONT, SCORE_TXT_SIZE), key='home_score')],
     [sg.Image("Networks/ESPN.png", subsample=5, key='network_logo', pad=(0,100))]
    ]

layout = [[
    sg.Push(),
    sg.Column(away_record_layout, element_justification='center', pad=(45,30)),
    sg.Column(score_layout, element_justification='center'),
    sg.Column(home_record_layout, element_justification='center', pad=(45,30)),
    sg.Push()
    ],
    [sg.VPush()],[sg.Push(), sg.Text("Created by:",font=(FONT, 72), key='sport_specific_info'), sg.Push()],
    [sg.VPush()],[sg.Push(), sg.Text("Matthew Ferretti",font=(FONT, INFO_TXT_SIZE), auto_size_text= True, size=(None,None), key='info'), sg.Push()],[sg.VPush()],[sg.Push()],
    [sg.Push(), sg.Text("Created by: Matthew Ferretti",font=(FONT, 10), key='personal')]
    ]

# Create the window
window = sg.Window("Scoreboard", layout, no_titlebar=True, resizable=True).Finalize()
window.Maximize()
window.TKroot.config(cursor="none")


##################################
#                                #
#   Check internet connection    #
#                                #
##################################
def is_connected(router_ip):
    """Check if there's an internet connection by pinging a router."""
    try:
        # Ping host with one packet and timeout of 2 seconds
        subprocess.check_call(["ping", "-c", "1", "-W", "2", router_ip], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError:
        return False

def reconnect(network_interface):
    """Attempt to reconnect by restarting the network interface."""
    print("No internet connection. Attempting to reconnect...")
    os.system(f"sudo ifconfig {network_interface} down")
    time.sleep(1)
    os.system(f"sudo ifconfig {network_interface} up")
    time.sleep(5)  # Wait for the network interface to come back up


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

event, values = window.read(timeout=5000)

while True:
    try:
        # Fetch Data
        if ticks_diff(ticks_ms(), fetch_clock) >= fetch_timer:
            teams_with_data.clear()
            team_info.clear()
            for fetch_index in range(len(teams)):
                print(f"\nFetching data for {teams[fetch_index][0]}")
                team_info.append(get_data(SPORT_URLS[fetch_index], teams[fetch_index], fetch_index))
                teams_with_data.append(team_has_data)
                if currently_playing:
                    returned_data = team_currently_playing(window)
                    team_info = returned_data

            fetch_clock = ticks_add(fetch_clock, fetch_timer) # Reset Timer if display updated

        # Display Team Information
        if ticks_diff(ticks_ms(), display_clock) >= display_timer:
            if teams_with_data[display_index]:
                print(f"\nUpdating Display for {teams[display_index][0]}")
                window['sport_specific_info'].update(font=(FONT, 42))
                if len(team_info['sport_specific_info']) > 37:
                    window['sport_specific_info'].update(font=(FONT, 36))

                for key, value in team_info[display_index].items():

                    if "network_logo" in key:
                        for network, file in network_logo_file_location.items():
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
            window["hyphen"].update(value=':', font=(FONT, SCORE_TXT_SIZE))
            window["home_score"].update(value=current_time.minute, font=(FONT, 204))
            window["away_score"].update(value=hour, font=(FONT, 204))
            window["home_record"].update(value='')
            window["away_record"].update(value='')
            window["away_logo"].update(filename='')
            window["home_logo"].update(filename="sport_logos/team0_logos/DET.png")
            window["info"].update(value=date,font=(FONT, SCORE_TXT_SIZE))
            window["sport_specific_info"].update(value=' ')
            window.read(timeout=5000)

        elif clock_displayed: # Reset Font if theres data to display
            window["hyphen"].update(value='-',font=(FONT, 72))
            window["home_score"].update(font=(FONT, SCORE_TXT_SIZE))
            window["away_score"].update(font=(FONT, SCORE_TXT_SIZE))
            window["info"].update(font=(FONT, INFO_TXT_SIZE))

        if event == sg.WIN_CLOSED: # Quit if any key pressed
            window.close()
            exit()

    except:
        while not is_connected(router_ip):
            print("Internet connection is down, trying to reconnect...")
            reconnect(network_interface)
            time.sleep(20)  # Check every 20 seconds
        print("Internet connection is active")