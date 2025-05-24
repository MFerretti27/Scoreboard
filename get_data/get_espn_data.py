"""Grab Data for ESPN API."""

import copy
import gc
import os
from datetime import datetime, timedelta, timezone
from typing import Any

import requests  # type: ignore

import settings

from .get_mlb_data import append_mlb_data, get_all_mlb_data
from .get_nba_data import append_nba_data, get_all_nba_data
from .get_nhl_data import append_nhl_data, get_all_nhl_data
from .get_series_data import get_series

should_skip = False


def check_playing_each_other(home_team: str, away_team: str) -> bool:
    """Check if the two teams are playing each other.

    :param home_team: Name of home team
    :param away_team: Name of away team
    :return: Boolean indicating whether to skip displaying the matchup (already shown once)
    """
    global should_skip

    # Create a set of uppercase team names for faster lookups
    team_names = {team[0].upper() for team in settings.teams}

    if home_team.upper() in team_names and away_team.upper() in team_names:
        if should_skip:
            print(f"{home_team} is playing {away_team}, skipping to not display twice")
            should_skip = False

            # Remove the skipped team data to prevent stale display
            settings.saved_data.pop(home_team, None)
            settings.saved_data.pop(away_team, None)

            return True

        should_skip = True
        return False

    return False


def get_data(team: list[str]) -> tuple:
    """Retrieve Data from ESPN API.

    :param team: Index of teams array to get data for

    :return team_info: List of Boolean values representing if team is has data to display
    """
    team_has_data: bool = False
    currently_playing: bool = False

    index: int = 0
    team_info: dict[str, Any] = {}
    team_name: str = team[0]
    team_league: str = team[1].lower()
    team_sport: str = team[2].lower()
    url: str = (f"https://site.api.espn.com/apis/site/v2/sports/{team_sport}/{team_league}/scoreboard")

    # Need to set these to empty string to avoid displaying old info, other texts always get updated below
    # these may not get updated and therefore display old info
    team_info['top_info'] = ''
    team_info['above_score_txt'] = ''
    team_info['under_score_image'] = ''

    try:
        resp = requests.get(url)
        response_as_json = resp.json()

        for event in response_as_json["events"]:
            if team_name.upper() in event["name"].upper():
                print(f"Found Game: {team_name}")
                team_has_data = True

                competition = response_as_json["events"][index]["competitions"][0]

                # Check if game is within the next month, if not then its too far out to display
                date = competition["date"]
                target_date = datetime.strptime(date, "%Y-%m-%dT%H:%MZ").replace(tzinfo=timezone.utc)
                now = datetime.now(timezone.utc)  # Current UTC date
                one_month_later = now + timedelta(days=30)  # Set range to be a month
                if now <= target_date >= one_month_later:
                    print("Game is more than a month away skipping")
                    return team_info, False, False

                # Get Score
                team_info['home_score'] = (competition["competitors"][0]["score"])
                team_info['away_score'] = (competition["competitors"][1]["score"])

                if settings.display_records:
                    try:
                        team_info['away_record'] = (competition["competitors"][1]["records"][0]["summary"])
                        team_info['home_record'] = (competition["competitors"][0]["records"][0]["summary"])
                    except Exception:
                        team_info['away_record'] = "N/A"
                        team_info['home_record'] = "N/A"

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
                team_info["above_score_txt"] = f"{away_short_name} @ {home_short_name}"

                # Check if two of your teams are playing each other to not display same data twice
                if check_playing_each_other(home_name, away_name):
                    team_has_data = False
                    return team_info, team_has_data, currently_playing

                # Get Network and display logo if possible
                if settings.display_network:
                    folder_path = os.getcwd() + '/images/Networks/'
                    file_names = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
                    for file in file_names:
                        file_no_png = file.replace(".png", "")
                        if file_no_png in broadcast.upper() and broadcast != "":
                            team_info["under_score_image"] = (f"{os.getcwd()}/images/Networks/{file}")
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
                    if settings.display_venue:
                        team_info['bottom_info'] = str(team_info['bottom_info'] + "@ " + venue)
                    else:
                        team_info['bottom_info'] = str(team_info['bottom_info'])

                    if settings.display_odds:
                        over_under = competition.get('odds', [{}])[0].get('overUnder', 'N/A')
                        spread = competition.get('odds', [{}])[0].get('details', 'N/A')
                        if "NHL" in team_league.upper() or "MLB" in team_league.upper():
                            team_info['top_info'] = f"MoneyLine: {spread} \t OverUnder: {over_under}"
                        else:
                            team_info['top_info'] = f"Spread: {spread} \t OverUnder: {over_under}"

                # Remove Timezone Characters in info
                team_info['bottom_info'] = team_info['bottom_info'].replace('EDT', '').replace('EST', '')

                # Get Logos Location for Teams
                team_info["away_logo"] = (f"images/sport_logos/{team_league.upper()}/{away_name.upper()}.png")
                team_info["home_logo"] = (f"images/sport_logos/{team_league.upper()}/{home_name.upper()}.png")

                ####################################################################
                # If looking at NFL team, get NFL specific data if currently playing
                ####################################################################
                if "NFL" in team_league.upper() and currently_playing:
                    down = competition.get('situation', {}).get('shortDownDistanceText')
                    red_zone = competition.get('situation', {}).get('isRedZone')
                    spot = competition.get('situation', {}).get('possessionText')
                    possession = competition.get('situation', {}).get('possession')
                    away_timeouts = competition.get('situation', {}).get('awayTimeouts')
                    home_timeouts = competition.get('situation', {}).get('homeTimeouts')

                    if not settings.display_nfl_clock:
                        team_info['bottom_info'] = ""

                    if down is not None and spot is not None and settings.display_nfl_down:
                        team_info['top_info'] = str(down) + " on " + str(spot)

                    if settings.display_nfl_redzone:
                        team_info.update({
                            'home_redzone': possession == home_team_id and red_zone,
                            'away_redzone': possession == away_team_id and red_zone
                        })
                    if settings.display_nfl_possession:
                        team_info.update({
                            'home_possession': possession == home_team_id,
                            'away_possession': possession == away_team_id,
                        })

                    if settings.display_nfl_timeouts and home_timeouts is not None and away_timeouts is not None:
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
                if "NBA" in team_league.upper() and currently_playing:
                    if settings.display_nba_shooting:
                        home_field_goal_attempt = (competition["competitors"][0]["statistics"][3]["displayValue"])
                        home_field_goal_made = (competition["competitors"][0]["statistics"][4]["displayValue"])

                        home_3pt_attempt = (competition["competitors"][0]["statistics"][11]["displayValue"])
                        home_3pt_made = (competition["competitors"][0]["statistics"][12]["displayValue"])

                        away_field_goal_attempt = (competition["competitors"][1]["statistics"][3]["displayValue"])
                        away_field_goal_made = (competition["competitors"][1]["statistics"][4]["displayValue"])

                        away_3pt_attempt = (competition["competitors"][1]["statistics"][11]["displayValue"])
                        away_3pt_made = (competition["competitors"][1]["statistics"][12]["displayValue"])

                        away_stats = \
                            (f"FG: {away_field_goal_made}/{away_field_goal_attempt} " +
                                f"3PT: {away_3pt_made}/{away_3pt_attempt}")
                        home_stats = \
                            (f"FG: {home_field_goal_made}/{home_field_goal_attempt} " +
                                f"3PT: {home_3pt_made}/{home_3pt_attempt}")

                        team_info['top_info'] = away_stats + "\t\t " + home_stats
                    # If currently playing, must have bonus information, set here in case api call fails
                    team_info['away_bonus'] = False
                    team_info['home_bonus'] = False
                    saved_info = copy.deepcopy(team_info)
                    try:
                        team_info = append_nba_data(team_info, team_name)
                    except Exception:
                        team_info = copy.deepcopy(saved_info)  # Try clause might modify dictionary

                    if not settings.display_nba_clock:
                        team_info["bottom_info"] = ""

                ####################################################################
                # If looking at MLB team, get MLB specific data if currently playing
                ####################################################################
                if "MLB" in team_league.upper() and currently_playing:
                    saved_info = copy.deepcopy(team_info)
                    # Get info from specific MLB API, has more data and updates faster
                    try:
                        team_info = append_mlb_data(team_info, team_name)

                    # If call to API fails get MLB specific info just from ESPN
                    except Exception:
                        print("Failed to get data from MLB API")
                        team_info = copy.deepcopy(saved_info)  # Try clause might modify dictionary
                        team_info['bottom_info'] = team_info['bottom_info'].replace('Bot', 'Bottom')
                        team_info['bottom_info'] = team_info['bottom_info'].replace('Mid', 'Middle')

                        # Change to display inning above score
                        if settings.display_inning:
                            team_info['above_score_txt'] = team_info['bottom_info']
                            team_info['bottom_info'] = ""
                        else:
                            team_info['bottom_info'] = ""

                        # Get who is pitching and batting, if info is available
                        if settings.display_pitcher_batter:
                            pitcher = (
                                competition.get("situation", {}).get("pitcher", {}).get("athlete", {})
                                           .get("shortName", "N/A")
                            )
                            pitcher = ' '.join(pitcher.split()[1:])  # Remove First Name
                            batter = (
                                competition.get("situation", {}).get("batter", {}).get("athlete", {})
                                           .get("shortName", "N/A")
                            )
                            batter = ' '.join(batter.split()[1:])  # Remove First Name
                            if pitcher != "N/A":
                                team_info['bottom_info'] += (f"P: {pitcher}   ")
                            if batter != "N/A":
                                team_info['bottom_info'] += (f"AB: {batter}")

                        # Get Hits and Errors
                        if settings.display_hits_errors:
                            home_hits = (competition["competitors"][0]["hits"])
                            away_hits = (competition["competitors"][1]["hits"])
                            home_errors = (competition["competitors"][0]["errors"])
                            away_errors = (competition["competitors"][1]["errors"])
                            team_info['away_timeouts'] = (f"Hits: {away_hits} Errors: {away_errors}")
                            team_info['home_timeouts'] = (f"Hits: {home_hits} Errors: {home_errors}")

                        # If inning is changing do not display count and move inning to display below score
                        if "Mid" not in team_info['above_score_txt'] and "End" not in team_info['above_score_txt']:
                            if settings.display_outs:
                                outs = (competition.get("outsText", "0 Outs"))
                                team_info['top_info'] += (f"{outs}")
                        else:
                            team_info['bottom_info'] = ""

                        if settings.display_bases:
                            # Get runners position
                            on_first = (competition["situation"]["onFirst"])
                            on_second = (competition["situation"]["onSecond"])
                            on_third = (competition["situation"]["onThird"])
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

                            # Get image location for representing runners on base
                            team_info['under_score_image'] = (
                                f"images/baseball_base_images/{base_conditions[(on_first, on_second, on_third)]}"
                            )

                ####################################################################
                # If looking at NHL team, get NHL specific data if currently playing
                ####################################################################
                if "NHL" in team_league.upper() and currently_playing:
                    saved_info = copy.deepcopy(team_info)
                    try:
                        team_info = append_nhl_data(team_info, team_name)
                    except Exception:
                        print("Could not get info from NHL API")
                        team_info = copy.deepcopy(saved_info)  # Try clause might modify dictionary

                # If game is over try displaying series information if available
                if team_info['top_info'] == "" and "FINAL" in team_info['bottom_info'] and settings.display_series:
                    team_info['top_info'] = get_series(team_league, team_name)

                break  # Found team in sports events and got data, no need to continue looking
            else:
                index += 1  # Continue looking for team in sports league events

        resp.close()
        gc.collect()
        return team_info, team_has_data, currently_playing

    # If call to ESPN fails use another API corresponding to the sport
    except Exception as e:
        print(f"Error fetching data from ESPN API: {e}")
        if "MLB" in team_league.upper():
            team_info, team_has_data, currently_playing = get_all_mlb_data(team_name)
        elif "NBA" in team_league.upper():
            team_info, team_has_data, currently_playing = get_all_nba_data(team_name)
        elif "NHL" in team_league.upper():
            team_info, team_has_data, currently_playing = get_all_nhl_data(team_name)
        elif "NFL" in team_league.upper():
            raise RuntimeError(f"Could Not Get {team_name} data") from e
        else:
            raise RuntimeError(f"Could Not Get {team_name} data") from e
        return team_info, team_has_data, currently_playing
