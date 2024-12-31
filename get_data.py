'''Grab Data for ESPN API'''

import requests  # pip install requests
import gc
from constants import network_logos, teams

should_skip = False


def check_playing_each_other(home_team: str, away_team: str) -> bool:
    '''Check if the two teams are playing each other

    :param home_team: Name of home team
    :param away_team: Name of away team

    :return: Boolean value representing if the two teams are playing each other
    '''
    global should_skip
    for x in teams:
        for y in teams:
            if home_team.upper() in [y[0].upper(), x[0].upper()] and away_team.upper() in [x[0].upper(), y[0].upper()]:
                if should_skip:  # Only skip one team, the one further down teams list
                    print(f"{home_team} is playing {away_team}, skipping to not display twice")
                    should_skip = not should_skip
                    return True
                should_skip = not should_skip
                return False  # Found teams playing each other, but should not skip first instance
    return False


def get_data(URL: str, team: str) -> list:
    '''Retrieve Data from ESPN API

    :param URL: URL link to ESPN to get API data
    :param team: Index of teams array to get data for

    :return team_info: List of Boolean values representing if team is has data to display
    '''
    team_has_data = False
    currently_playing = False

    index = 0
    team_info = {}
    team_name = team[0]
    team_sport = team[1]
    # Need to set this to empty string to avoid displaying old info
    # If team_info does not have top_info then display will not update
    team_info['top_info'] = ''

    resp = requests.get(URL)
    response_as_json = resp.json()
    for event in response_as_json["events"]:
        if team_name.upper() in event["name"].upper():
            print(f"Found Game: {team_name}")
            team_has_data = True

            competition = response_as_json["events"][index]["competitions"][0]

            # Data returned
            team_info['home_score'] = (competition["competitors"][0]["score"])
            team_info['away_score'] = (competition["competitors"][1]["score"])
            team_info['away_record'] = (competition["competitors"][1]["records"][0]["summary"])
            team_info['home_record'] = (competition["competitors"][0]["records"][0]["summary"])
            team_info['bottom_info'] = (response_as_json["events"][index]["status"]["type"]["shortDetail"])

            # Data only used in this function
            home_name = (competition["competitors"][0]["team"]["displayName"])
            away_name = (competition["competitors"][1]["team"]["displayName"])
            venue = (competition["venue"]["fullName"])
            broadcast = (competition["broadcast"])
            home_team_id = competition["competitors"][0]["id"]
            away_team_id = competition["competitors"][1]["id"]

            if check_playing_each_other(home_name, away_name):
                team_has_data = False
                return team_info, team_has_data, currently_playing

            for network, filepath in network_logos.items():
                if network.upper() in broadcast.upper():
                    team_info['network_logo'] = filepath
                    break
                else:  # If it cant find logo use league logo as defaults
                    if team[1].upper() in filepath:
                        team_info['network_logo'] = filepath

            # Check if Team is Currently Playing
            if "PM" not in str(team_info['bottom_info']) and "AM" not in str(team_info['bottom_info']):
                currently_playing = True

            # Check if Team is Done Playing
            if any(keyword in str(team_info['bottom_info']) for keyword in ["Delayed", "Postponed", "Final"]):
                currently_playing = False
                team_info['bottom_info'] = str(team_info['bottom_info']).upper()

            # Check if Game hasn't been played yet
            elif not currently_playing:
                team_info['bottom_info'] = str(team_info['bottom_info'] + "@ " + venue)
                overUnder = competition.get('odds', [{}])[0].get('overUnder', 'N/A')
                spread = competition.get('odds', [{}])[0].get('details', 'N/A')
                if "NHL" in URL.upper():
                    team_info['top_info'] = f"MoneyLine: {spread} \t OverUnder: {overUnder}"
                else:
                    team_info['top_info'] = f"Spread: {spread} \t OverUnder: {overUnder}"

            # If looking at NFL team get this data (only if currently playing)
            if "NFL" in URL.upper() and currently_playing:
                down = competition.get('situation', {}).get('shortDownDistanceText')
                red_zone = competition.get('situation', {}).get('isRedZone')
                spot = competition.get('situation', {}).get('possessionText')
                possession = competition.get('situation', {}).get('possession')
                away_timeouts = competition.get('situation', {}).get('awayTimeouts')
                home_timeouts = competition.get('situation', {}).get('homeTimeouts')
                if down is not None and spot is not None:
                    team_info['top_info'] = str(down) + " on " + str(spot)

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
                    team_info['away_possession'] = True
                    if red_zone:
                        team_info['away_redzone'] = True

                timeouts = ''
                if home_timeouts is not None and away_timeouts is not None:
                    timeout_map = {3: "\u25CF  \u25CF  \u25CF", 2: "\u25CF  \u25CF", 1: "\u25CF", 0: ""}

                    timeouts += timeout_map.get(away_timeouts, "")
                    timeouts += "\t\t"
                    timeouts += timeout_map.get(home_timeouts, "")
                    team_info['timeouts'] = timeouts

                # Swap top and bottom info for NFL (I think it looks better displayed this way)
                temp = str(team_info['bottom_info'])
                team_info['bottom_info'] = str(team_info['top_info'])
                team_info['top_info'] = temp

            # If looking at NBA team get this data (only if currently playing)
            if "NBA" in URL.upper() and currently_playing:
                home_field_goal_attempt = ((competition["competitors"][0]["statistics"][3]["displayValue"]))
                home_field_goal_made = ((competition["competitors"][0]["statistics"][4]["displayValue"]))

                home_3pt_attempt = ((competition["competitors"][0]["statistics"][11]["displayValue"]))
                home_3pt_made = ((competition["competitors"][0]["statistics"][12]["displayValue"]))

                away_field_goal_attempt = ((competition["competitors"][1]["statistics"][3]["displayValue"]))
                away_field_goal_made = ((competition["competitors"][1]["statistics"][4]["displayValue"]))

                away_3pt_attempt = ((competition["competitors"][1]["statistics"][11]["displayValue"]))
                away_3pt_made = ((competition["competitors"][1]["statistics"][12]["displayValue"]))

                away_stats = \
                    f"FG: {away_field_goal_made}/{away_field_goal_attempt} 3PT: {away_3pt_made}/{away_3pt_attempt}"
                home_stats = \
                    f"FG: {home_field_goal_made}/{home_field_goal_attempt} 3PT: {home_3pt_made}/{home_3pt_attempt}"

                team_info['top_info'] = away_stats + "\t\t " + home_stats

            # If looking at MLB team get this data (only if currently playing)
            if "MLB" in URL.upper() and currently_playing:
                # outs = (response_as_json["events"][index]["competitions"][0]["outsText"])
                if 'Bot' in str(team_info.get('bottom_info')):  # Replace Bot with Bottom for baseball innings
                    team_info['bottom_info'].replace('bot', 'Bottom')

            # Remove Timezone Characters in info
            if 'EDT' in team_info.get('bottom_info'):
                team_info['bottom_info'] = team_info['bottom_info'].replace('EDT', '')
            elif 'EST' in team_info['bottom_info']:
                team_info['bottom_info'] = team_info['bottom_info'].replace('EST', '')

            # Get Logos Location for Teams
            team_info["away_logo"] = (f"sport_logos/{team_sport.upper()}/{away_name.upper()}.png")
            team_info["home_logo"] = (f"sport_logos/{team_sport.upper()}/{home_name.upper()}.png")

            break
        else:
            index += 1

    resp.close()
    gc.collect()
    return team_info, team_has_data, currently_playing
