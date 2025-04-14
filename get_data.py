'''Grab Data for ESPN API'''

import statsapi
from nba_api.live.nba.endpoints import scoreboard
import requests  # pip install requests
import gc
from constants import network_logos, teams

should_skip = False
home_team_bonus = False
away_team_bonus = False


def get_mlb_team_id(team: str) -> int:
    '''Get MLB Team ID from team name

    :param team: Name of MLB team to get ID for

    :return: Team ID
    '''
    teams = statsapi.get('teams', {'sportIds': 1})['teams']
    id_list = {t["clubName"]: t["id"] for t in teams}
    for key, value in id_list.items():
        if key.upper() in team.upper():
            return value

    raise ValueError(f"Unknown MLB team name: {team}")


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
    global home_team_bonus, away_team_bonus
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

            # Check if two of your teams are playing each other to not display same data twice
            if check_playing_each_other(home_name, away_name):
                team_has_data = False
                return team_info, team_has_data, currently_playing

            # Get Network game is on and display logo
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

                # Get timeouts and if team is in bonus from nba_api.live.nba.endpoints
                games = scoreboard.ScoreBoard()
                data = games.get_dict()
                for game in data["scoreboard"]["games"]:
                    if game["homeTeam"]["teamName"].upper() in team_name.upper() or \
                            game["awayTeam"]["teamName"].upper() in team_name.upper():

                        if game["homeTeam"]["inBonus"] == "1":
                            team_info['home_bonus'] = True
                            home_team_bonus = True
                        elif game["homeTeam"]["inBonus"] == "0":
                            team_info['home_bonus'] = False
                            home_team_bonus = False
                        elif game["homeTeam"]["inBonus"] is None:
                            team_info['home_bonus'] = home_team_bonus
                        else:
                            team_info['home_bonus'] = False

                        if game["awayTeam"]["inBonus"] == "1":
                            team_info['away_bonus'] = True
                            away_team_bonus = True
                        elif game["awayTeam"]["inBonus"] == "0":
                            team_info['away_bonus'] = False
                            away_team_bonus = False
                        elif game["awayTeam"]["inBonus"] is None:
                            team_info['away_bonus'] = away_team_bonus
                        else:
                            team_info['away_bonus'] = False

                        home_timeouts = game["homeTeam"]["timeoutsRemaining"]
                        away_timeouts = game["awayTeam"]["timeoutsRemaining"]

                        if game["homeTeam"]["inBonus"] is None and game["awayTeam"]["inBonus"] is None:
                            home_timeouts = home_timeouts + 1
                            away_timeouts = away_timeouts + 1

                        timeout_map = {7: "\u25CF  \u25CF  \u25CF  \u25CF  \u25CF  \u25CF  \u25CF",
                                       6: "\u25CF  \u25CF  \u25CF  \u25CF  \u25CF  \u25CF",
                                       5: "\u25CF  \u25CF  \u25CF  \u25CF  \u25CF",
                                       4: "\u25CF  \u25CF  \u25CF  \u25CF",
                                       3: "\u25CF  \u25CF  \u25CF",
                                       2: "\u25CF  \u25CF",
                                       1: "\u25CF",
                                       0: ""}
                        team_info['away_timeouts'] = timeout_map.get(away_timeouts, "")
                        team_info['home_timeouts'] = timeout_map.get(home_timeouts, "")

                        break  # Found team and got data needed

            ####################################################################
            # If looking at MLB team, get MLB specific data if currently playing
            ####################################################################
            if "MLB" in URL.upper() and currently_playing:
                fields = ("linescore,batter,inHole,onDeck,liveData,balls,strikes,plays,offense,onDeck," +
                          "fullName,result,description,eventType,details,type,description,currentPlay," +
                          "playEvents,isPitch")
                data = statsapi.schedule(team=get_mlb_team_id(team=team_name))
                live = statsapi.get("game", {"gamePk": data[0]["game_id"], "fields": fields})
                team_info['bottom_info'] = team_info['bottom_info'].replace('Bot', 'Bottom')

                # Change to display inning above score
                team_info['baseball_inning'] = team_info['bottom_info']
                team_info['bottom_info'] = ""

                # Get who is pitching and batting, if info is available
                pitcher = competition.get("situation", {}).get("pitcher", {}).get("athlete", {}).get("shortName", "N/A")
                batter = competition.get("situation", {}).get("batter", {}).get("athlete", {}).get("shortName", "N/A")
                due_up = live["liveData"]["linescore"]["offense"]["onDeck"]["fullName"]

                if pitcher != "N/A":
                    team_info['bottom_info'] += (f"P: {pitcher.split()[-1]}   ")
                if batter != "N/A":
                    team_info['bottom_info'] += (f"AB: {batter.split()[-1]}")

                # If inning is changing do not display count and move inning to display below score
                if "Mid" not in team_info['baseball_inning'] and "End" not in team_info['baseball_inning']:
                    outs = (competition.get("outsText", "0 Outs"))
                    balls = live["liveData"]["linescore"].get("balls", "0")
                    strikes = live["liveData"]["linescore"].get("strikes", "0")
                    try:
                        play = live["liveData"]["plays"].get("currentPlay", {}).get("result", {}).get("description", "")
                        pitch = live["liveData"]["plays"].get("currentPlay", {}).get("playEvents", [{}])[-1]
                        if pitch.get("isPitch", True):
                            team_info['top_info'] += pitch["details"]["type"]["description"] + "  "
                        if play:
                            team_info['bottom_info'] = play
                    except KeyError:
                        continue
                    home_hits = (competition["competitors"][0]["hits"])
                    away_hits = (competition["competitors"][1]["hits"])
                    home_errors = (competition["competitors"][0]["errors"])
                    away_errors = (competition["competitors"][1]["errors"])
                    team_info['away_timeouts'] = (f"Hits: {away_hits} Errors: {away_errors}")
                    team_info['home_timeouts'] = (f"Hits: {home_hits} Errors: {home_errors}")
                    team_info['top_info'] += (f"{balls}-{strikes}, {outs}")
                else:
                    team_info['bottom_info'] += (f"DueUp: {due_up}")
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
                if base_conditions.get((onFirst, onSecond, onThird)) is None:
                    team_info['network_logo'] = "baseball_base_images/empty_bases.png"
                else:
                    team_info['network_logo'] = f"baseball_base_images/{base_conditions[(onFirst, onSecond, onThird)]}"

            break  # Found team in sports events and got data, no need to continue looking
        else:
            index += 1  # Continue looking for team in sports league events

    resp.close()
    gc.collect()
    return team_info, team_has_data, currently_playing
