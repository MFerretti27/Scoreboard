"""Get MLB from MLB specific API."""
from datetime import UTC, datetime, timedelta
from typing import Any

import requests
import statsapi  # type: ignore[import]

import settings
from helper_functions.data_helpers import check_playing_each_other, get_team_logo
from helper_functions.logger_config import logger

from .get_game_type import get_game_type
from .get_series_data import get_current_series_mlb
from .get_team_id import get_mlb_team_id

# What things to get from MLBStats API
API_FIELDS = (
    "gameData,game,datetime,dateTime,officialDate,status,detailedState,abstractGameState,teams,home,away,"
    "teamName,record,wins,losses,fullName,liveData,plays,currentPlay,result,playEvents,isPitch,runs,"
    "details,type,code,description,linescore,outs,balls,strikes,inningState,currentInningOrdinal,defense,"
    "offense,batter,inHole,onDeck,first,second,third,pitcher,wins,hits,errors,pitching,currentInning"
)


def get_all_mlb_data(team_name: str, double_header: int = 0) -> tuple[dict[str, Any], bool, bool]:
    """Get all information for MLB team.

    Call this if ESPN fails to get MLB data as backup.

    :param team_name: The team name to get information for
    :param double_header: If team has double header, defaults to 0 (no)

    :return team_info: dictionary containing team information to display
    """
    team_info: dict[str, Any] = {}
    has_data = False
    currently_playing = False

    # Try to get first game from now for the next 3 days
    today = datetime.now().strftime("%Y-%m-%d")
    three_days_later = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")
    try:
        data = statsapi.schedule(
            team=get_mlb_team_id(team_name), include_series_status=True, start_date=today, end_date=three_days_later,
        )
        
        # Validate data exists and index is valid
        if not data or double_header >= len(data):
            logger.warning("MLB schedule data invalid or doubleheader index out of bounds: %d", double_header)
            double_header = 0
            if not data:
                return team_info, has_data, currently_playing
                
        game_id = data[double_header].get("game_id")
        if not game_id:
            logger.warning("No game_id found in MLB schedule data")
            return team_info, has_data, currently_playing
            
        live = statsapi.get("game", {"gamePk": game_id, "fields": API_FIELDS})

        # Protected request with validation
        response = requests.get(f'https://statsapi.mlb.com/api/v1.1/game/{game_id}/feed/live', timeout=5)
        response.raise_for_status()
        live_feed = response.json()
        
    except (requests.exceptions.RequestException, ValueError, KeyError, IndexError) as e:
        logger.exception("Could not get MLB data: %s", str(e))
        double_header = 0
        return team_info, has_data, currently_playing  # Could not find game

    has_data = True
    # Cannot Get network so dont display anything, and if game is currently playing it will updated with base images
    team_info["under_score_image"] = ""

    # Get Score - safely access nested data
    try:
        live_data = live.get("liveData", {})
        linescore = live_data.get("linescore", {})
        teams = linescore.get("teams", {})
        team_info["home_score"] = teams.get("home", {}).get("runs", 0)
        team_info["away_score"] = teams.get("away", {}).get("runs", 0)
    except (KeyError, TypeError) as e:
        logger.error("Error accessing MLB score data: %s", str(e))
        team_info["home_score"] = "0"
        team_info["away_score"] = "0"

    # Get date and put in local time
    try:
        game_data = live.get("gameData", {})
        datetime_data = game_data.get("datetime", {})
        date_time_str = datetime_data.get("dateTime", "")
        if date_time_str:
            utc_time = datetime.strptime(date_time_str, "%Y-%m-%dT%H:%M:%S%z")
            game_time = utc_time.replace(tzinfo=UTC).astimezone().strftime("%-m/%-d - %-I:%M %p")
        else:
            game_time = "Time TBD"
    except (ValueError, KeyError) as e:
        logger.warning("Could not parse MLB game time: %s", str(e))
        game_time = "Time TBD"

    # Get venue and set bottom info to display game time and venue
    team_info["bottom_info"] = game_time
    if settings.display_venue:
        venue = live_feed.get("gameData", {}).get("venue", {}).get("name", "Venue TBD")
        team_info["bottom_info"] = f"{game_time} @ {venue}"

    # Get Home and Away team logos/names - safely access nested data
    game_data = live.get("gameData", {})
    teams_data = game_data.get("teams", {})
    home_team_data = teams_data.get("home", {})
    away_team_data = teams_data.get("away", {})
    home_team_name = home_team_data.get("teamName", "Home Team")
    away_team_name = away_team_data.get("teamName", "Away Team")
    team_info["above_score_txt"] = f"{away_team_name} @ {home_team_name}"

    # Check if two of your teams are playing each other to not display same data twice
    live_feed_teams = live_feed.get("gameData", {}).get("teams", {})
    full_home_team_name = live_feed_teams.get("home", {}).get("franchiseName", "") + " " + home_team_name
    full_away_team_name = live_feed_teams.get("away", {}).get("franchiseName", "") + " " + away_team_name
    if check_playing_each_other(full_home_team_name, full_away_team_name):
        team_has_data = False
        return team_info, team_has_data, currently_playing

    # If team is D-backs change to "ARIZONA DIAMONDBACKS", there is no logo file called D-backs
    home_team_name = home_team_name.replace("D-backs", "ARIZONA DIAMONDBACKS")
    away_team_name = away_team_name.replace("D-backs", "ARIZONA DIAMONDBACKS")

    # Get team logos
    team_info = get_team_logo(home_team_name, away_team_name, "MLB", team_info)

    # If str returned is not empty, then its world series/conference championship, so display championship png
    team_info["under_score_image"] = get_game_type("MLB", team_name)

    # Get Home and Away team records
    if settings.display_records:
        home_record = home_team_data.get("record", {})
        home_wins = home_record.get("wins", 0)
        home_losses = home_record.get("losses", 0)
        team_info["home_record"] = f"{home_wins!s}-{home_losses!s}"

        away_record = away_team_data.get("record", {})
        away_wins = away_record.get("wins", 0)
        away_losses = away_record.get("losses", 0)
        team_info["away_record"] = f"{away_wins!s}-{away_losses!s}"

    # Check if game is currently playing
    status = game_data.get("status", {})
    detailed_state = status.get("detailedState", "")
    if "Progress" in detailed_state:
        currently_playing = True
        team_info = append_mlb_data(team_info, team_name, double_header)

    # Check if game is over
    elif "Final" in live["gameData"]["status"]["detailedState"]:
        team_info["top_info"] = get_current_series_mlb(team_name)
        team_info["bottom_info"] = live["gameData"]["status"]["detailedState"].upper()

        team_info, has_data, currently_playing = check_double_header(home_team_name, away_team_name,
                                                                    team_info, live_feed, double_header)
        return team_info, has_data, currently_playing

    # Game has not been played yet but scheduled
    else:
        # Check if postponed or delayed
        team_info = check_delayed(data, double_header, team_info, game_time)

    return team_info, has_data, currently_playing


def append_mlb_data(team_info: dict, team_name: str, double_header: int = 0) -> dict:
    """Get information for MLB team if playing.

    :param team_info: Dictionary where data is stored to display
    :param team_name: The team name to get information for

    :return team_info: dictionary containing team information to display
    """
    data = statsapi.schedule(team=get_mlb_team_id(team=team_name), include_series_status=True)
    live = statsapi.get("game", {"gamePk": data[double_header]["game_id"], "fields": API_FIELDS})

    # Get Scores
    team_info["home_score"] = str(live["liveData"]["linescore"]["teams"]["home"]["runs"])
    team_info["away_score"] = str(live["liveData"]["linescore"]["teams"]["away"]["runs"])

    # Get hits and error to display under score
    if settings.display_hits_errors:
        home_hits = live["liveData"]["linescore"]["teams"]["home"].get("hits", 0)
        away_hits = live["liveData"]["linescore"]["teams"]["away"].get("hits", 0)
        home_errors = live["liveData"]["linescore"]["teams"]["home"].get("errors", 0)
        away_errors = live["liveData"]["linescore"]["teams"]["away"].get("errors", 0)
        team_info["away_timeouts"] = (f"Hits: {away_hits} Errors: {away_errors}")
        team_info["home_timeouts"] = (f"Hits: {home_hits} Errors: {home_errors}")

    # Get inning
    if settings.display_inning:
        inning_state = live["liveData"]["linescore"].get("inningState", "Top")
        inning_number = live["liveData"]["linescore"].get("currentInningOrdinal", 0)
        team_info["above_score_txt"] = inning_state + " " + str(inning_number)

    # Get pitcher and batter for bottom info
    if settings.display_pitcher_batter:
        batter_full_name = live["liveData"]["linescore"]["offense"].get("batter", {}).get("fullName", "")
        batter_last_name = " ".join(batter_full_name.split()[1:])  # Remove First Name
        pitcher_full_name = live["liveData"]["linescore"]["defense"].get("pitcher", {}).get("fullName", "")
        pitcher_last_name = " ".join(pitcher_full_name.split()[1:])  # Remove First Name

        team_info["bottom_info"] = (f"P: {pitcher_last_name}   AB: {batter_last_name}")

    team_info["top_info"] = ""
    team_info = get_data_based_on_inning_state(live, batter_full_name, team_info)

    if settings.display_bases:
        bases = {"first": False, "second": False, "third": False}  # Dictionary to store info of occupied bases

        offense = live.get("liveData", {}).get("linescore", {}).get("offense", {})
        for key in bases:
            bases[key] = bool(offense.get(key, {}).get("fullName"))

        # Get which image to display based on what base is occupied
        base_conditions = {
            (True, False, False): "on_first.png",
            (False, True, False): "on_second.png",
            (False, False, True): "on_third.png",
            (True, False, True): "on_first_third.png",
            (True, True, False): "on_first_second.png",
            (False, True, True): "on_second_third.png",
            (True, True, True): "on_first_second_third.png",
            (False, False, False): "empty_bases.png",
        }

        # Get image location for representing runners on base
        base_image = base_conditions[(bases["first"], bases["second"], bases["third"])]
        team_info["under_score_image"] = f"images/baseball_base_images/{base_image}"

    return team_info

def get_data_based_on_inning_state(live: dict, batter_full_name: str, team_info: dict) -> dict:
    """Get data based on inning state.

    If inning is changing do not display count/play etc. display batter due up.

    :param live: The live data from MLBStats API
    :param batter_full_name: The full name of the batter to display
    :param team_info: The team information dictionary to update

    :return team_info: Updated team information dictionary
    """
    # If inning is changing do not display count and move inning to display below score
    if "Mid" not in team_info["above_score_txt"] and "End" not in team_info["above_score_txt"]:
        try:
            pitch = live["liveData"]["plays"].get("currentPlay", {}).get("playEvents", [{}])[-1]
            if pitch.get("isPitch", True) and settings.display_last_pitch:
                team_info["top_info"] += pitch["details"]["type"]["description"].replace("Four-Seam", "") + "  "

            play = live["liveData"]["plays"].get("currentPlay", {}).get("result", {}).get("description", "")
            if play and settings.display_play_description:
                team_info["bottom_info"] = play
        except Exception:
            logger.exception("couldn't get Pitch or play")

        if settings.display_balls_strikes:
            balls = live["liveData"]["linescore"].get("balls", 0)
            strikes = live["liveData"]["linescore"].get("strikes", 0)
            outs = live["liveData"]["linescore"].get("outs", 0)
            team_info["top_info"] += (f"{balls}-{strikes}, {outs} Outs")
    else:
        # If it is the Middle or End of inning show who is leading off batting
        if settings.display_pitcher_batter:
            team_info["bottom_info"] = (f"DueUp: {batter_full_name}")
        team_info["top_info"] = ""

    return team_info


def check_double_header(home_team_name: str, away_team_name: str, team_info: dict,
                        live_feed: dict, double_header: int) -> tuple[dict[str, Any], bool, bool]:
    """Check if there is a double header and get data for second game.

    :param home_team_name: Full name of home team
    :param away_team_name: Full name of away team
    :param team_info: Dictionary where data is stored to display
    :param live_feed: The live data from MLBStats API
    :param double_header: If team has double header, defaults to 0 (no)
    """
    # Once game is over check if its a double header but ensure second game doesn't call this
    if live_feed["gameData"]["game"]["doubleHeader"] != "N" and double_header !=1:
        temp_first_game_score = (f'{team_info["away_score"]}-{team_info["home_score"]}'
                                    if int(team_info["away_score"]) > int(team_info["home_score"]) else
                                    f'{team_info["home_score"]}-{team_info["away_score"]}'
                                    )
        winning_team = (home_team_name
                        if team_info["home_score"] > team_info["away_score"] else away_team_name)
        team_info, has_data, currently_playing = get_all_mlb_data(home_team_name, double_header=1)
        if not currently_playing:
            team_info["top_info"] = f"Doubleheader: {winning_team} Won {temp_first_game_score} First Game"

        return team_info, has_data, currently_playing

    return team_info, True, False # No double header

def check_delayed(data: dict, double_header: int, team_info: dict, game_time: str) -> dict[str, Any]:
    """Check if game is delayed/postponed/canceled and update team_info accordingly.

    :param data: The schedule data from MLBStats API
    :param double_header: If team has double header, defaults to 0 (no)
    :param team_info: Dictionary where data is stored to display
    :param game_time: The scheduled game time in local time

    :return team_info: Updated team information dictionary
    """
    scheduled = statsapi.get(
            "schedule", {"gamePk": data[double_header]["game_id"],
                         "sportId": 1,
                         "fields": "dates,date,games,status,detailedState,abstractGameState,reason"},
            )
    if scheduled["dates"][0]["games"][0]["status"]["detailedState"] in ["Postponed", "Delayed", "Canceled"]:
        state_of_game = scheduled["dates"][0]["games"][0]["status"]["detailedState"]
        reason_for_state = scheduled["dates"][0]["games"][0]["status"]["reason"]
        team_info["bottom_info"] = state_of_game + " due to " + reason_for_state
        team_info["top_info"] = f"New game set for {game_time}"

    return team_info
