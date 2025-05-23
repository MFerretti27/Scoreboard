"""Get MLB from MLB specific API."""
import os
from datetime import datetime, timedelta, timezone

import requests
import statsapi  # type: ignore

import settings

from .get_series_data import get_current_series_mlb
from .get_team_id import get_mlb_team_id

# What things to get from MLBStats API
API_FIELDS = (
    "gameData,game,datetime,dateTime,officialDate,status,detailedState,abstractGameState,teams,home,away,"
    + "teamName,record,wins,losses,fullName,liveData,plays,currentPlay,result,playEvents,isPitch,runs,"
    + "details,type,code,description,linescore,outs,balls,strikes,inningState,currentInningOrdinal,defense,"
    + "offense,batter,inHole,onDeck,first,second,third,pitcher,wins,hits,errors,pitching,currentInning"
)


def get_all_mlb_data(team_name: str) -> tuple[dict[str, str], bool, bool]:
    """Get all information for MLB team.

    Call this if ESPN fails to get MLB data as backup.

    :param team_name: The team name to get information for

    :return team_info: dictionary containing team information to display
    """
    team_info: dict[str, str] = {}
    has_data = False
    currently_playing = False

    # Try to get first game from now for the next 3 days
    today = datetime.now().strftime("%Y-%m-%d")
    three_days_later = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")
    try:
        data = statsapi.schedule(
            team=get_mlb_team_id(team_name), include_series_status=True, start_date=today, end_date=three_days_later
        )
        live = statsapi.get("game", {"gamePk": data[0]["game_id"], "fields": API_FIELDS})
    except Exception:
        return team_info, has_data, currently_playing  # Could not find game

    has_data = True
    # Cannot Get network so dont display anything, and if game is currently playing it will updated with base images
    team_info['under_score_image'] = ''

    # Set Score to 0, will be updated if team is currently playing
    team_info["home_score"] = "0"
    team_info["away_score"] = "0"

    # Get date and put in local time
    iso_string = live["gameData"]["datetime"]["dateTime"]
    utc_time = datetime.strptime(iso_string, "%Y-%m-%dT%H:%M:%SZ")
    utc_time = utc_time.replace(tzinfo=timezone.utc)
    local_time = utc_time.astimezone()
    game_time = local_time.strftime("%-m/%-d %-I:%M %p")

    # Get venue and set bottom info to display game time and venue
    if settings.display_venue:
        try:
            game_id = data[0]["game_id"]
            url = f"https://statsapi.mlb.com/api/v1.1/game/{game_id}/feed/live"
            response = requests.get(url)
            live_feed = response.json()
            venue = live_feed['gameData']['venue']['name']
            team_info["bottom_info"] = f"{game_time} @ {venue}"
        except Exception:
            team_info["bottom_info"] = game_time

    # Get Home and Away team logos
    home_team = live["gameData"]["teams"]["home"]["teamName"]
    away_team = live["gameData"]["teams"]["away"]["teamName"]
    team_info["above_score_txt"] = f"{away_team} @ {home_team}"
    folder_path = os.getcwd() + '/images/sport_logos/MLB/'
    file_names = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
    for file in file_names:
        if home_team.upper() in file:
            home_team = file
        if away_team.upper() in file:
            away_team = file

    team_info["away_logo"] = (f"{os.getcwd()}/images/sport_logos/MLB/{away_team}")
    team_info["home_logo"] = (f"{os.getcwd()}/images/sport_logos/MLB/{home_team}")

    # Get Home and Away team records
    if settings.display_records:
        home_wins = live["gameData"]["teams"]["home"]["record"]["wins"]
        home_losses = live["gameData"]["teams"]["home"]["record"]["losses"]
        team_info['home_record'] = f"{str(home_wins)}-{str(home_losses)}"

        away_wins = live["gameData"]["teams"]["away"]["record"]["wins"]
        away_losses = live["gameData"]["teams"]["away"]["record"]["losses"]
        team_info['away_record'] = f"{str(away_wins)}-{str(away_losses)}"

    if "Progress" in live["gameData"]["status"]["detailedState"]:
        currently_playing = True
        team_info = append_mlb_data(team_info, team_name)
    elif "Final" in live["gameData"]["status"]["detailedState"]:
        team_info["top_info"] = get_current_series_mlb(team_name)
        team_info["bottom_info"] = "FINAL"

    return team_info, has_data, currently_playing


def append_mlb_data(team_info: dict, team_name: str) -> dict:
    """Get information for MLB team if playing.

    :param team_info: Dictionary where data is stored to display
    :param team_name: The team name to get information for

    :return team_info: dictionary containing team information to display
    """
    data = statsapi.schedule(team=get_mlb_team_id(team=team_name), include_series_status=True)
    live = statsapi.get("game", {"gamePk": data[0]["game_id"], "fields": API_FIELDS})

    # Get Scores
    team_info["home_score"] = str(live["liveData"]["linescore"]["teams"]["home"]["runs"])
    team_info["away_score"] = str(live["liveData"]["linescore"]["teams"]["away"]["runs"])

    # Get hits and error to display under score
    if settings.display_hits_errors:
        home_hits = live["liveData"]["linescore"]["teams"]["home"].get("hits", 0)
        away_hits = live["liveData"]["linescore"]["teams"]["away"].get("hits", 0)
        home_errors = live["liveData"]["linescore"]["teams"]["home"].get("errors", 0)
        away_errors = live["liveData"]["linescore"]["teams"]["away"].get("errors", 0)
        team_info['away_timeouts'] = (f"Hits: {away_hits} Errors: {away_errors}")
        team_info['home_timeouts'] = (f"Hits: {home_hits} Errors: {home_errors}")

    # Get inning
    if settings.display_inning:
        inning_state = live["liveData"]["linescore"].get("inningState", "Top")
        inning_number = live["liveData"]["linescore"].get("currentInningOrdinal", 0)
        team_info['above_score_txt'] = inning_state + " " + str(inning_number)
    else:
        team_info['bottom_info'] = ""

    # Get pitcher and batter for bottom info
    if settings.display_pitcher_batter:
        batter_full_name = live["liveData"]["linescore"]["offense"]["batter"]["fullName"]
        batter = ' '.join(batter_full_name.split()[1:])  # Remove First Name
        pitcher = live["liveData"]["linescore"]["defense"]["pitcher"]["fullName"]
        pitcher = ' '.join(pitcher.split()[1:])  # Remove First Name

        team_info['bottom_info'] = ''
        if pitcher != '':
            team_info['bottom_info'] += (f"P: {pitcher}   ")
        if batter != '':
            team_info['bottom_info'] += (f"AB: {batter}")

    # If inning is changing do not display count and move inning to display below score
    if "Mid" not in team_info['above_score_txt'] and "End" not in team_info['above_score_txt']:
        try:
            pitch = live["liveData"]["plays"].get("currentPlay", {}).get("playEvents", [{}])[-1]
            if pitch.get("isPitch", True) and settings.display_last_pitch:
                team_info['top_info'] += pitch["details"]["type"]["description"].replace('Four-Seam', '') + "  "

            play = live["liveData"]["plays"].get("currentPlay", {}).get("result", {}).get("description", "")
            if play and settings.display_play_description:
                team_info['bottom_info'] = play
        except Exception:
            print("couldn't get Pitch or play")

        if settings.display_balls_strikes:
            balls = live["liveData"]["linescore"].get("balls", 0)
            strikes = live["liveData"]["linescore"].get("strikes", 0)
            outs = live["liveData"]["linescore"].get("outs", 0)
            team_info['top_info'] += (f"{balls}-{strikes}, {outs} Outs")
    else:
        # If it is the Middle or End of inning show who is leading off batting
        if settings.display_pitcher_batter:
            team_info['bottom_info'] = (f"DueUp: {batter_full_name}")
        team_info['top_info'] = ""

    if settings.display_bases:
        bases = {"first": False, "second": False, "third": False}  # Dictionary to store info of occupied bases

        for key, _ in bases.items():
            try:
                # Dont need to store name of whose on just has to ensure call is successful
                _ = live["liveData"]["linescore"]["offense"][key]["fullName"]
                bases[key] = True  # If call is successful someone is on that base
            except KeyError:
                bases[key] = False  # If call fails no one is on that base

        # Get which image to display based on what base is occupied
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
        base_image = base_conditions[(bases["first"], bases["second"], bases["third"])]
        team_info['under_score_image'] = f"images/baseball_base_images/{base_image}"

    return team_info
