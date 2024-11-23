import requests # pip install requests
import gc

def get_data(URL, team, sport, network_logos):
    '''The actual API and display function'''
    team_has_data = False
    index = 0
    team_info = {}
    team_info['sport_specific_info'] = ''
    currently_playing = False

    resp = requests.get(URL)
    response_as_json = resp.json()
    print(f"Looking for:  {team[0]}")
    for e in response_as_json["events"]:
        if team[0] in e["name"]:
            print(f"Found Game: {team[0]}")
            team_has_data = True

            competition = response_as_json["events"][index]["competitions"][0]

            # Data returned
            team_info['home_score'] = (competition["competitors"][0]["score"])
            team_info['away_score'] = (competition["competitors"][1]["score"])
            team_info['away_record'] = (competition["competitors"][1]["records"][0]["summary"])
            team_info['home_record'] = (competition["competitors"][0]["records"][0]["summary"])
            team_info['info'] = (response_as_json["events"][index]["status"]["type"]["shortDetail"])

            # Data only used in this function
            home_name =(competition["competitors"][0]["team"]["abbreviation"])
            away_name = (competition["competitors"][1]["team"]["abbreviation"])
            venue = (competition["venue"]["fullName"])
            broadcast = (competition["broadcast"])
            home_team_id = competition["competitors"][0]["id"]
            away_team_id = competition["competitors"][1]["id"]

            for network, filepath in network_logos.items():
                if network in broadcast: 
                    team_info['network_logo'] = filepath[0] # Index 0 is filepath
                    break
                else:  # If it cant find logo league logo as defaults
                    if team[1] in filepath[0]: team_info['network_logo'] = filepath[0]

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

            # Remove Timezone Characters in info
            if 'EDT' in team_info.get("info"): team_info["info"] = team_info["info"].replace('EDT', '')
            elif 'EST' in team_info["info"]: team_info["info"] = team_info["info"].replace('EST', '')

            # Get Logos Location for Teams
            team_info["away_logo"] = (f"sport_logos/team" + str(sport) + "_logos/" + away_name + ".png")
            team_info["home_logo"] = (f"sport_logos/team" + str(sport) + "_logos/" + home_name + ".png")

            break
        else:
            index += 1

    resp.close()
    gc.collect()
    return team_info, team_has_data, currently_playing