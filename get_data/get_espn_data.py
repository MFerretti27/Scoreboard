'''Grab Data for ESPN API'''

import requests  # pip install requests
import gc
from constants import network_logos, teams
from .get_mlb_data import get_all_mlb_data, append_mlb_data
from .get_nhl_data import append_nhl_data, get_all_nhl_data
from .get_nba_data import append_nba_data
from .get_series_data import get_series

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
    # Need to set these to empty string to avoid displaying old info, other texts always get updated below
    # these may not get updated and therefore display old info
    team_info['top_info'] = ''
    team_info['baseball_inning'] = ''
    team_info['network_logo'] = ''

    try:
        resp = requests.get(URL)
        response_as_json = resp.json()
    except Exception:
        if "MLB" in URL.upper():
            team_info, team_has_data, currently_playing = get_all_mlb_data(team_name, team_info)
            return team_info, team_has_data, currently_playing
        elif "NBA" in URL.upper():
            raise Exception("Could Not Get NBA data")
        elif "NHL" in URL.upper():
            team_info, team_has_data, currently_playing = get_all_nhl_data(team_info, team_name)
            return team_info, team_has_data, currently_playing
        # elif "NFL" in URL.upper():
        #     raise Exception("Could Not Get NFL data")
        # else:
        #     raise Exception("Could Not Get ESPN data")

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

            home_short_name = competition["competitors"][0]["team"]["shortDisplayName"]
            away_short_name = competition["competitors"][1]["team"]["shortDisplayName"]

            # Display team names above score
            team_info["baseball_inning"] = f"{away_short_name} vs {home_short_name}"

            # Check if two of your teams are playing each other to not display same data twice
            if check_playing_each_other(home_name, away_name):
                team_has_data = False
                return team_info, team_has_data, currently_playing

            # Get Network game is on and display logo
            for network, filepath in network_logos.items():
                if network.upper() in broadcast.upper():
                    team_info['network_logo'] = filepath
                    break

            # Check if Team is Currently Playing
            if "PM" not in str(team_info['bottom_info']) and "AM" not in str(team_info['bottom_info']):
                currently_playing = True

            # Check if Team is Done Playing
            if any(keyword in str(team_info['bottom_info'])
                   for keyword in ["Delayed", "Postponed", "Final", "Canceled"]):
                currently_playing = False
                team_info['bottom_info'] = str(team_info['bottom_info']).upper()

            # Check if Game hasn't been played yet
            elif not currently_playing:
                team_info['bottom_info'] = str(team_info['bottom_info'] + "@ " + venue)
                overUnder = competition.get('odds', [{}])[0].get('overUnder', 'N/A')
                spread = competition.get('odds', [{}])[0].get('details', 'N/A')
                if "NHL" in URL.upper() or "MLB" in URL.upper():
                    team_info['top_info'] = f"MoneyLine: {spread} \t OverUnder: {overUnder}"
                else:
                    team_info['top_info'] = f"Spread: {spread} \t OverUnder: {overUnder}"

            # Remove Timezone Characters in info
            team_info['bottom_info'] = team_info['bottom_info'].replace('EDT', '').replace('EST', '')

            # Get Logos Location for Teams
            team_info["away_logo"] = (f"sport_logos/{team_sport.upper()}/{away_name.upper()}.png")
            team_info["home_logo"] = (f"sport_logos/{team_sport.upper()}/{home_name.upper()}.png")

            ####################################################################
            # If looking at NFL team, get NFL specific data if currently playing
            ####################################################################
            if "NFL" in URL.upper() and currently_playing:
                down = competition.get('situation', {}).get('shortDownDistanceText')
                red_zone = competition.get('situation', {}).get('isRedZone')
                spot = competition.get('situation', {}).get('possessionText')
                possession = competition.get('situation', {}).get('possession')
                away_timeouts = competition.get('situation', {}).get('awayTimeouts')
                home_timeouts = competition.get('situation', {}).get('homeTimeouts')
                if down is not None and spot is not None:
                    team_info['top_info'] = str(down) + " on " + str(spot)

                team_info.update({
                    'home_possession': possession == home_team_id,
                    'away_possession': possession == away_team_id,
                    'home_redzone': possession == home_team_id and red_zone,
                    'away_redzone': possession == away_team_id and red_zone
                })

                if home_timeouts is not None and away_timeouts is not None:
                    timeout_map = {3: "\u25CF  \u25CF  \u25CF", 2: "\u25CF  \u25CF", 1: "\u25CF", 0: ""}

                    team_info['away_timeouts'] = timeout_map.get(away_timeouts, "")
                    team_info['home_timeouts'] += timeout_map.get(home_timeouts, "")

                # Swap top and bottom info for NFL (I think it looks better displayed this way)
                temp = str(team_info['bottom_info'])
                team_info['bottom_info'] = str(team_info['top_info'])
                team_info['top_info'] = temp

            ####################################################################
            # If looking at NBA team, get NBA specific data if currently playing
            ####################################################################
            if "NBA" in URL.upper() and currently_playing:
                saved_info = team_info
                try:
                    team_info = append_nba_data()
                finally:
                    team_info = saved_info
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

            ####################################################################
            # If looking at MLB team, get MLB specific data if currently playing
            ####################################################################
            if "MLB" in URL.upper() and currently_playing:
                saved_info = team_info
                # Get info from specific MLB API, has more data and updates faster
                try:
                    team_info = append_mlb_data(team_info, team_name)

                # If call to API fails get MLB specific info from ESPN
                except Exception:
                    print("Failed to get data from MLB API")
                    team_info = saved_info  # Try clause might modify dictionary
                    team_info['bottom_info'] = team_info['bottom_info'].replace('Bot', 'Bottom')
                    team_info['bottom_info'] = team_info['bottom_info'].replace('Mid', 'Middle')

                    # Change to display inning above score
                    team_info['baseball_inning'] = team_info['bottom_info']
                    team_info['bottom_info'] = ""

                    # Get who is pitching and batting, if info is available
                    pitcher = (
                        competition.get("situation", {}).get("pitcher", {}).get("athlete", {}).get("shortName", "N/A")
                    )
                    pitcher = ' '.join(pitcher.split()[1:])  # Remove First Name
                    batter = (
                        competition.get("situation", {}).get("batter", {}).get("athlete", {}).get("shortName", "N/A")
                    )
                    batter = ' '.join(batter.split()[1:])  # Remove First Name
                    if pitcher != "N/A":
                        team_info['bottom_info'] += (f"P: {pitcher}   ")
                    if batter != "N/A":
                        team_info['bottom_info'] += (f"AB: {batter}")

                    home_hits = (competition["competitors"][0]["hits"])
                    away_hits = (competition["competitors"][1]["hits"])
                    home_errors = (competition["competitors"][0]["errors"])
                    away_errors = (competition["competitors"][1]["errors"])
                    team_info['away_timeouts'] = (f"Hits: {away_hits} Errors: {away_errors}")
                    team_info['home_timeouts'] = (f"Hits: {home_hits} Errors: {home_errors}")

                    # If inning is changing do not display count and move inning to display below score
                    if "Mid" not in team_info['baseball_inning'] and "End" not in team_info['baseball_inning']:
                        outs = (competition.get("outsText", "0 Outs"))
                        team_info['top_info'] += (f"{outs}")
                    else:
                        team_info['bottom_info'] = ""
                        team_info['top_info'] = team_info['baseball_inning']
                        team_info['baseball_inning'] = ""

                    # Get runners position
                    onFirst = (competition["situation"]["onFirst"])
                    onSecond = (competition["situation"]["onSecond"])
                    onThird = (competition["situation"]["onThird"])
                    base_conditions = {
                        (True, False, False): "on_first.png",
                        (False, True, False): "on_second.png",
                        (False, False, True): "on_third.png",
                        (True, False, True): "on_first_third.png",
                        (True, True, False): "on_first_second.png",
                        (False, True, True): "on_second_third.png",
                        (True, True, True): "on_first_second_third.png",
                        (False, False, False): "empty_bases.png"
                    }

                    # Display runners on base
                    team_info['network_logo'] = f"baseball_base_images/{base_conditions[(onFirst, onSecond, onThird)]}"

            ####################################################################
            # If looking at NHL team, get NHL specific data if currently playing
            ####################################################################
            if "NHL" in URL.upper() and currently_playing:
                saved_info = team_info
                try:
                    team_info = append_nhl_data(team_info, team_name)
                except Exception:
                    print("Could not get info from NHL API")
                    team_info = saved_info  # Try clause might modify dictionary

            # If got here with no top info to display, try displaying series info
            if team_info['top_info'] == "":
                team_info['top_info'] = get_series(URL, team_name)

            break  # Found team in sports events and got data, no need to continue looking
        else:
            index += 1  # Continue looking for team in sports league events

    resp.close()
    gc.collect()
    return team_info, team_has_data, currently_playing
