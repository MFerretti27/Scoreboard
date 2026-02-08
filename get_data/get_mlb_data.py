"""Get MLB from MLB specific API."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import requests
import statsapi  # type: ignore[import]

import settings
from constants.file_paths import get_baseball_base_image_path
from helper_functions.api_utils.exceptions import APIError, DataValidationError, NetworkError
from helper_functions.api_utils.retry import BackoffConfig, retry_with_fallback
from helper_functions.api_utils.validators import validate_mlb_game, validate_mlb_schedule_response
from helper_functions.data.data_helpers import check_playing_each_other, get_team_logo
from helper_functions.logging.logger_config import log_context_scope, logger

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


@retry_with_fallback(
    max_attempts=settings.RETRY_MAX_ATTEMPTS,
    backoff=BackoffConfig(
        initial_delay=settings.RETRY_INITIAL_DELAY,
        max_delay=settings.RETRY_MAX_DELAY,
        backoff_multiplier=settings.RETRY_BACKOFF_MULTIPLIER,
    ),
    use_cache_fallback=settings.RETRY_USE_CACHE_FALLBACK,
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

    with log_context_scope(team=team_name, league="MLB", endpoint="mlb_statsapi"):
        # Fetch and validate game data
        data, live, live_feed = _fetch_mlb_data(team_name, double_header)
        has_data = True

        # Get basic game information
        team_info, game_time = _get_mlb_basic_info(live, live_feed)
        home_team_name = live["gameData"]["teams"]["home"]["teamName"]
        away_team_name = live["gameData"]["teams"]["away"]["teamName"]

        # Check if two of your teams are playing each other
        full_home_team_name = live_feed["gameData"]["teams"]["home"]["franchiseName"] + " " + home_team_name
        full_away_team_name = live_feed["gameData"]["teams"]["away"]["franchiseName"] + " " + away_team_name
        if check_playing_each_other(full_home_team_name, full_away_team_name):
            return team_info, False, currently_playing

        # Get logos and game type
        team_info = _get_mlb_logos_and_type(home_team_name, away_team_name, team_name, team_info)

        # Get records if enabled
        if settings.display_records:
            team_info = _get_mlb_records(live, team_info)

        # Handle game status
        game_status = live["gameData"]["status"]["detailedState"]
        if "Progress" in game_status:
            team_info = append_mlb_data(team_info, team_name, double_header)
            currently_playing = True
        elif "Final" in game_status:
            team_info["top_info"] = get_current_series_mlb(team_name)
            team_info["bottom_info"] = game_status.upper()
            team_info, has_data, currently_playing = check_double_header(
                home_team_name, away_team_name, team_info, live_feed, double_header,
            )
            return team_info, has_data, currently_playing
        else:
            # Game not played yet - check if delayed/postponed
            team_info = check_delayed(data, double_header, team_info, game_time)

        return team_info, has_data, currently_playing


def _fetch_mlb_data(team_name: str, double_header: int) -> tuple:
    """Fetch and validate MLB game data."""
    today = datetime.now().strftime("%Y-%m-%d")
    three_days_later = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")
    try:
        try:
            data = statsapi.schedule(
                team=get_mlb_team_id(team_name),
                include_series_status=True,
                start_date=today,
                end_date=three_days_later,
            )
        except Exception as e:
            logger.exception("statsapi.schedule timeout or error for %s", team_name)
            msg = f"MLB schedule API timeout for {team_name}"
            raise APIError(msg, error_code="MLB_SCHEDULE_TIMEOUT") from e

        try:
            validate_mlb_schedule_response(data, team_name)
        except DataValidationError as e:
            msg = f"MLB schedule response invalid for {team_name}"
            raise APIError(msg, error_code="INVALID_SCHEDULE") from e

        try:
            live = statsapi.get("game", {"gamePk": data[double_header]["game_id"], "fields": API_FIELDS})
        except Exception as e:
            logger.exception("statsapi.get game timeout or error for %s", team_name)
            msg = f"MLB game API timeout for {team_name}"
            raise APIError(msg, error_code="MLB_GAME_TIMEOUT") from e

        try:
            validate_mlb_game(live, team_name)
        except DataValidationError as e:
            msg = f"MLB game data invalid for {team_name}"
            raise APIError(msg, error_code="INVALID_GAME_DATA") from e

        try:
            live_feed_resp = requests.get(
                f'https://statsapi.mlb.com/api/v1.1/game/{data[double_header]["game_id"]}/feed/live', timeout=5,
            )
        except (requests.ConnectionError, requests.Timeout, requests.RequestException) as e:
            logger.error(f"Network error while fetching MLB live feed for {team_name}: {e}")
            msg = f"Network error while fetching MLB live feed for {team_name}"
            raise NetworkError(msg, error_code="NETWORK_ERROR") from e
        live_feed = live_feed_resp.json()
    except (APIError, DataValidationError):
        raise
    except Exception as e:
        logger.exception("Could not get MLB data")
        msg = f"Failed to fetch MLB game data for {team_name}"
        raise APIError(msg, error_code="MLB_API_ERROR") from e

    return data, live, live_feed


def _get_mlb_basic_info(live: dict, live_feed: dict) -> tuple[dict, str]:
    """Get basic MLB game information."""
    team_info = {}
    team_info["under_score_image"] = ""

    # Get scores
    team_info["home_score"] = live["liveData"]["linescore"]["teams"]["home"].get("runs", 0)
    team_info["away_score"] = live["liveData"]["linescore"]["teams"]["away"].get("runs", 0)

    # Get date and game time
    utc_time = datetime.strptime(live["gameData"]["datetime"]["dateTime"], "%Y-%m-%dT%H:%M:%S%z")
    game_time = utc_time.replace(tzinfo=UTC).astimezone().strftime("%-m/%-d - %-I:%M %p")

    team_info["bottom_info"] = game_time
    if settings.display_venue:
        venue = live_feed["gameData"]["venue"]["name"]
        team_info["bottom_info"] = f"{game_time} @ {venue}"

    # Get team names
    home_team_name = live["gameData"]["teams"]["home"]["teamName"]
    away_team_name = live["gameData"]["teams"]["away"]["teamName"]
    team_info["above_score_txt"] = f"{away_team_name} @ {home_team_name}"

    return team_info, game_time


def _get_mlb_logos_and_type(home_team_name: str, away_team_name: str, team_name: str, team_info: dict) -> dict:
    """Get team logos and game type."""
    # Handle D-backs name
    home_team_name = home_team_name.replace("D-backs", "ARIZONA DIAMONDBACKS")
    away_team_name = away_team_name.replace("D-backs", "ARIZONA DIAMONDBACKS")

    # Get team logos
    team_info = get_team_logo(home_team_name, away_team_name, "MLB", team_info)

    # Get game type (World Series/Championship)
    team_info["under_score_image"] = get_game_type("MLB", team_name)

    return team_info


def _get_mlb_records(live: dict, team_info: dict) -> dict:
    """Get home and away team records."""
    home_wins = live["gameData"]["teams"]["home"]["record"]["wins"]
    home_losses = live["gameData"]["teams"]["home"]["record"]["losses"]
    team_info["home_record"] = f"{home_wins!s}-{home_losses!s}"

    away_wins = live["gameData"]["teams"]["away"]["record"]["wins"]
    away_losses = live["gameData"]["teams"]["away"]["record"]["losses"]
    team_info["away_record"] = f"{away_wins!s}-{away_losses!s}"

    return team_info


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
        team_info["under_score_image"] = get_baseball_base_image_path(base_image)

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
