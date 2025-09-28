"""Grab Data for ESPN API."""

import copy
import gc
from datetime import UTC, datetime, timedelta
from typing import Any

import requests  # type: ignore[import]
from dateutil.parser import isoparse  # type: ignore[import]

import settings
from helper_functions.data_helpers import check_for_doubleheader, check_playing_each_other, get_network_logos
from helper_functions.logger_config import logger

from .get_game_type import get_game_type
from .get_mlb_data import append_mlb_data, get_all_mlb_data
from .get_nba_data import append_nba_data, get_all_nba_data
from .get_nhl_data import append_nhl_data, get_all_nhl_data
from .get_series_data import get_series

doubleheader = 0


def get_espn_data(team: list[str], team_info: dict) -> tuple:
    """Get data from ESPN API for a specific team.

    :param team: Index of teams array to get data for
    :param team_info: Dictionary to store team information

    """
    team_name, team_league, team_sport = team[0], team[1].lower(), team[2].lower()
    url: str = (f"https://site.api.espn.com/apis/site/v2/sports/{team_sport}/{team_league}/scoreboard")
    index = 0
    currently_playing: bool = False
    team_has_data: bool = False

    # Need to set these to empty string to avoid errors and they might not get set but will keys will be looked for
    team_info.update({
        "top_info": "",
        "above_score_txt": "",
        "under_score_image": "",
    })

    resp = requests.get(url, timeout=5)
    response_as_json = resp.json()

    for event in response_as_json["events"]:
        if team_name.upper() not in event["name"].upper():
            index += 1  # Continue looking for team in sports league events
            continue

        logger.info("Found Game: %s", team_name)
        team_has_data = True
        competition = response_as_json["events"][index]["competitions"][0]

        # Check if game is within the next month, if not then its too far out to display
        if not is_valid_game_date(competition["date"]):
            logger.info("Game is too far in the future or too old, skipping")
            return team_info, False, False

        # Get Score
        team_info["home_score"] = competition["competitors"][0]["score"]
        team_info["away_score"] = competition["competitors"][1]["score"]

        if settings.display_records:
            team_info["away_record"] = competition["competitors"][1].get("records", "N/A")[0].get("summary", "N/A")
            team_info["home_record"] = competition["competitors"][0].get("records", "N/A")[0].get("summary", "N/A")

        team_info["bottom_info"] = response_as_json["events"][index]["status"]["type"]["shortDetail"]

        # Data only used in this function
        home_name = competition["competitors"][0]["team"]["displayName"]
        away_name = competition["competitors"][1]["team"]["displayName"]
        broadcast = competition["broadcast"]
        home_short_name = competition["competitors"][0]["team"]["shortDisplayName"]
        away_short_name = competition["competitors"][1]["team"]["shortDisplayName"]

        # Display team names above score
        team_info["above_score_txt"] = f"{away_short_name} @ {home_short_name}"

        # Check if two of your teams are playing each other to not display same data twice
        if check_playing_each_other(home_name, away_name):
            return team_info, False, currently_playing

        # Get Network and display logo if possible
        team_info["under_score_image"] = get_network_logos(broadcast)

        # Check if Team is Currently Playing
        currently_playing = not any(t in team_info["bottom_info"] for t in ["AM", "PM"])
        team_info, currently_playing = get_not_playing_data(team_info, competition, team_league,
                                                            team_name, currently_playing=currently_playing)

        # Remove Timezone Characters in info
        team_info["bottom_info"] = team_info["bottom_info"].replace("EDT", "").replace("EST", "")

        # Get Logos Location for Teams
        team_info["away_logo"] = (f"images/sport_logos/{team_league.upper()}/{away_name.upper()}.png")
        team_info["home_logo"] = (f"images/sport_logos/{team_league.upper()}/{home_name.upper()}.png")

        # Get data if team is either playing or not playing
        if currently_playing:
            team_info = get_live_game_data(team_league, team_name, team_info, competition)

        # Check if game is a championship game, if so display its championship game
        if get_game_type(team_league, team_name) != "":
            # If str returned is not empty, then it Finals/Stanley Cup/World Series, so display championship png
            try:
                team_info["under_score_image"] = get_game_type(team_league, team_name)
            except Exception:
                logger.exception(f"Could not get {team_league} game type")

        # Check for MLB doubleheader
        if handle_doubleheader(team_info, team_league, team_name, response_as_json["events"], competition):
            return team_info, True, False

        break  # Found team in sports events and got data, no need to continue looking

    resp.close()
    gc.collect()
    return team_info, team_has_data, currently_playing

def get_currently_playing_nfl_data(team_info: dict[str, Any], competition: dict[str, Any],
                                   home_team_id: str, away_team_id: str) -> dict[str, Any]:
    """Get NFL Data for currently playing teams.

    :param team_info: Dictionary containing team information
    :param competition: Dictionary containing competition information
    :param home_team_id: ID of the home team
    :param away_team_id: ID of the away team

    :return: Updated team_info with NFL specific data
    """
    down = competition.get("situation", {}).get("shortDownDistanceText")
    red_zone = competition.get("situation", {}).get("isRedZone")
    spot = competition.get("situation", {}).get("possessionText")
    possession = competition.get("situation", {}).get("possession")
    away_timeouts = competition.get("situation", {}).get("awayTimeouts")
    home_timeouts = competition.get("situation", {}).get("homeTimeouts")

    if not settings.display_nfl_clock:
        team_info["bottom_info"] = ""

    if down is not None and spot is not None and settings.display_nfl_down:
        team_info["top_info"] = str(down) + " on " + str(spot)

    if settings.display_nfl_redzone:
        team_info.update({
            "home_redzone": possession == home_team_id and red_zone,
            "away_redzone": possession == away_team_id and red_zone,
        })
    if settings.display_nfl_possession:
        team_info.update({
            "home_possession": possession == home_team_id,
            "away_possession": possession == away_team_id,
        })

    if settings.display_nfl_timeouts and home_timeouts is not None and away_timeouts is not None:
        timeout_map = {3: "\u25CF  \u25CF  \u25CF", 2: "\u25CF  \u25CF", 1: "\u25CF", 0: ""}

        team_info["away_timeouts"] = timeout_map.get(away_timeouts, "")
        team_info["home_timeouts"] = timeout_map.get(home_timeouts, "")

    # Swap top and bottom info for NFL (I think it looks better displayed this way)
    temp = str(team_info["bottom_info"])
    team_info["bottom_info"] = str(team_info["top_info"])
    team_info["top_info"] = temp

    if ("1st" in team_info["top_info"] or "2nd" in team_info["top_info"]
        or "3rd" in team_info["top_info"]or "4th" in team_info["top_info"]):
        team_info["top_info"] = team_info["top_info"] + " Quarter"

    return team_info


def get_currently_playing_nba_data(team_name: str, team_info: dict[str, Any],
                                   competition: dict[str, Any]) -> dict[str, Any]:
    """Get NBA Data for currently playing teams.

    Uses the NBA API to get more detailed information about the game and
    will fall back on ESPN data if the API call fails. Play-by-Play, bonus, and timeouts
    are only available from the NBA API, so if the API call fails, these will not be displayed.

    :param team_name: Name of the team
    :param team_info: Dictionary containing team information
    :param competition: Dictionary containing competition information

    :return: Updated team_info with NBA specific data
    """
    if settings.display_nba_shooting:
        home_field_goal_attempt = (competition["competitors"][0]["statistics"][3]["displayValue"])
        home_field_goal_made = (competition["competitors"][0]["statistics"][4]["displayValue"])

        home_3pt_attempt = (competition["competitors"][0]["statistics"][11]["displayValue"])
        home_3pt_made = (competition["competitors"][0]["statistics"][12]["displayValue"])

        away_field_goal_attempt = (competition["competitors"][1]["statistics"][3]["displayValue"])
        away_field_goal_made = (competition["competitors"][1]["statistics"][4]["displayValue"])

        away_3pt_attempt = (competition["competitors"][1]["statistics"][11]["displayValue"])
        away_3pt_made = (competition["competitors"][1]["statistics"][12]["displayValue"])

        away_stats = (
            f"FG: {away_field_goal_made}/{away_field_goal_attempt} "
            f"3PT: {away_3pt_made}/{away_3pt_attempt}"
        )

        home_stats = (
            f"FG: {home_field_goal_made}/{home_field_goal_attempt} "
            f"3PT: {home_3pt_made}/{home_3pt_attempt}"
        )

        team_info["top_info"] = away_stats + "\t\t " + home_stats
    # If currently playing, must have bonus information, set here in case api call fails
    team_info["away_bonus"] = False
    team_info["home_bonus"] = False
    saved_info = copy.deepcopy(team_info)
    try:
        team_info = append_nba_data(team_info, team_name)
    except Exception:
        logger.exception("Failed to get data from NBA API")
        team_info = copy.deepcopy(saved_info)  # Try clause might modify dictionary
        team_info["signature"] = "Failed to get data from NBA API"

    if not settings.display_nba_clock:
        team_info["bottom_info"] = ""

    return team_info

def get_currently_playing_mlb_data(team_name: str, team_info: dict[str, Any],
                                   competition: dict[str, Any]) -> dict[str, Any]:
    """Get MLB Data for currently playing teams.

    Uses the MLB API to get more detailed information about the game and
    will fall back on ESPN data if the API call fails. Last Pitch, play description, and count
    are only available from the MLB API, so if the API call fails, these will not be displayed.

    :param team_name: Name of the team
    :param team_info: Dictionary containing team information
    :param competition: Dictionary containing competition information

    :return: Updated team_info with MLB specific data
    """
    saved_info = copy.deepcopy(team_info)
    # Get info from specific MLB API, has more data and updates faster
    try:
        team_info = append_mlb_data(team_info, team_name, doubleheader)

    # If call to API fails get MLB specific info just from ESPN
    except Exception:
        logger.exception("Failed to get data from MLB API")
        team_info = copy.deepcopy(saved_info)  # Try clause might modify dictionary
        team_info["signature"] = "Failed to get data from MLB API"

        team_info["bottom_info"] = team_info["bottom_info"].replace("Bot", "Bottom")
        team_info["bottom_info"] = team_info["bottom_info"].replace("Mid", "Middle")

        # Change to display inning above score
        if settings.display_inning:
            team_info["above_score_txt"] = team_info["bottom_info"]
            team_info["bottom_info"] = ""
        else:
            team_info["bottom_info"] = ""

        # Get who is pitching and batting, if info is available
        if settings.display_pitcher_batter:
            pitcher = (
                competition.get("situation", {}).get("pitcher", {}).get("athlete", {})
                            .get("shortName", "N/A")
            )
            pitcher = " ".join(pitcher.split()[1:])  # Remove First Name
            batter = (
                competition.get("situation", {}).get("batter", {}).get("athlete", {})
                            .get("shortName", "N/A")
            )
            batter = " ".join(batter.split()[1:])  # Remove First Name
            if pitcher != "N/A":
                team_info["bottom_info"] += (f"P: {pitcher}   ")
            if batter != "N/A":
                team_info["bottom_info"] += (f"AB: {batter}")

        # Get Hits and Errors
        if settings.display_hits_errors:
            home_hits = (competition["competitors"][0]["hits"])
            away_hits = (competition["competitors"][1]["hits"])
            home_errors = (competition["competitors"][0]["errors"])
            away_errors = (competition["competitors"][1]["errors"])
            team_info["away_timeouts"] = (f"Hits: {away_hits} Errors: {away_errors}")
            team_info["home_timeouts"] = (f"Hits: {home_hits} Errors: {home_errors}")

        # If inning is changing do not display count and move inning to display below score
        if "Mid" not in team_info["above_score_txt"] and "End" not in team_info["above_score_txt"]:
            if settings.display_outs:
                outs = (competition.get("outsText", "0 Outs"))
                team_info["top_info"] += (f"{outs}")
        else:
            team_info["bottom_info"] = ""

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
                (False, False, False): "empty_bases.png",
            }

            # Get image location for representing runners on base
            team_info["under_score_image"] = (
                f"images/baseball_base_images/{base_conditions[(on_first, on_second, on_third)]}"
            )
    return team_info

def get_currently_playing_nhl_data(team_name: str, team_info: dict[str, Any]) -> dict[str, Any]:
    """Use NHL API to get more Data for currently playing teams.

    :param team_name: Name of the team
    :param team_info: Dictionary containing team information

    :return: Updated team_info with NHL specific data
    """
    saved_info = copy.deepcopy(team_info)
    try:
        team_info = append_nhl_data(team_info, team_name)
    except Exception:
        logger.exception("Could not get info from NHL API")
        team_info = copy.deepcopy(saved_info)  # Try clause might modify dictionary
        team_info["signature"] = "Failed to get data from NHL API"

    return team_info


def is_valid_game_date(date_str: str) -> bool:
    """Check if the game date is within the valid range.

    param date_str: Date string in ISO format (e.g., "2023-10-01T00:00:00Z")

    return: True if the date is within the valid range, False otherwise
    """
    target_date = isoparse(date_str)
    now = datetime.now(UTC)
    return now - timedelta(days=settings.HOW_LONG_TO_DISPLAY_TEAM) <= target_date <= now + timedelta(days=30)


def handle_doubleheader(info: dict, league: str, name: str, events: list, comp: dict) -> bool:
    """Handle doubleheader for MLB games.

    param info: Dictionary containing team information
    param league: Name of the league (e.g., "MLB")
    param name: Name of the team
    param events: List of events from the ESPN API
    param comp: Dictionary containing competition information

    return: True if the game is a doubleheader, False otherwise
    """
    global doubleheader
    if ("FINAL" not in info["bottom_info"] or league != "mlb" or
        not check_for_doubleheader({"events": events}, name) or doubleheader != 0):
        return False

    doubleheader = 1
    score = f"{info['away_score']}-{info['home_score']}" if int(info["away_score"]) > int(info["home_score"]) \
        else f"{info['home_score']}-{info['away_score']}"
    winner = comp["competitors"][0]["team"]["displayName"] if int(info["home_score"]) > int(info["away_score"]) \
        else comp["competitors"][1]["team"]["displayName"]

    updated_info, _, still_playing = get_data([name, league, comp["competitors"][0]["team"]["sport"]["name"]])
    if not still_playing:
        updated_info["top_info"] = f"Doubleheader: {winner} Won {score} First Game"

    info.update(updated_info)
    doubleheader = 0
    return not still_playing


def get_live_game_data(league: str, name: str, info: dict, comp: dict) -> dict:
    """Get live game data for a specific league.

    param league: Name of the league (e.g., "NFL", "NBA", "MLB", "NHL")
    param name: Name of the team
    param info: Dictionary containing team information
    param comp: Dictionary containing competition information

    return: Updated info with live game data for the specified league
    """
    if "NFL" in league.upper():
        return get_currently_playing_nfl_data(info, comp, comp["competitors"][0]["id"], comp["competitors"][1]["id"])
    if "NBA" in league.upper():
        return get_currently_playing_nba_data(name, info, comp)
    if "MLB" in league.upper():
        return get_currently_playing_mlb_data(name, info, comp)
    if "NHL" in league.upper():
        return get_currently_playing_nhl_data(name, info)
    return info

def get_not_playing_data(team_info: dict, competition: dict, team_league: str,
                         team_name: str, *, currently_playing: bool = False) -> tuple[dict[Any, Any], bool]:
    """Get data if team is not currently playing.

    param info: Dictionary containing team information
    param comp: Dictionary containing competition information

    return: Updated info with live game data for the specified league
    """
    # Check if Team is Done Playing
    if any(keyword in str(team_info["bottom_info"])
            for keyword in ["Delayed", "Postponed", "Final", "Canceled", "Delay"]):
        currently_playing = False
        team_info["bottom_info"] = str(team_info["bottom_info"]).upper()

    # Check if Game hasn't been played yet
    elif not currently_playing:
        team_info["bottom_info"] = str(team_info["bottom_info"])

        if settings.display_venue:
            venue = competition["venue"]["fullName"]
            team_info["bottom_info"] = str(team_info["bottom_info"] + "@ " + venue)

        if settings.display_odds:
            over_under = competition.get("odds", [{}])[0].get("overUnder", "N/A")
            spread = competition.get("odds", [{}])[0].get("details", "N/A")
            team_info["top_info"] = f"Spread: {spread} \t OverUnder: {over_under}"
            if team_league.upper() in ["NHL", "MLB"]:
                team_info["top_info"] = f"MoneyLine: {spread} \t OverUnder: {over_under}"

    # If game is over try displaying series information if available
    if "FINAL" in team_info["bottom_info"] and settings.display_series:
        team_info["top_info"] = get_series(team_league, team_name)

    return team_info, currently_playing

def get_data(team: list[str]) -> tuple:
    """Try to get data for a specific team.

    Uses the ESPN API to get data for a specific team. If the API call fails, it will
    fall back on other APIs depending on the sport. If no data is available, it will
    return a message indicating that data could not be retrieved.

    :param team: Index of teams array to get data for

    :return team_info: List of Boolean values representing if team is has data to display
    """
    team_has_data: bool = False
    currently_playing: bool = False

    team_info: dict[str, Any] = {}
    team_name: str = team[0]
    team_league: str = team[1].lower()

    try:
        team_info, team_has_data, currently_playing = get_espn_data(team, team_info)

    # If call to ESPN fails use another API corresponding to the sport
    except Exception as e:
        logger.exception("\n\nError fetching data from ESPN API\n\n")
        if "MLB" in team_league.upper():
            team_info, team_has_data, currently_playing = get_all_mlb_data(team_name)
        elif "NBA" in team_league.upper():
            team_info, team_has_data, currently_playing = get_all_nba_data(team_name)
        elif "NHL" in team_league.upper():
            team_info, team_has_data, currently_playing = get_all_nhl_data(team_name)
        elif "NFL" in team_league.upper():
            msg = f"Could Not Get {team_name} data"
            raise RuntimeError(msg) from e
        else:
            msg = f"Could Not Get {team_name} data"
            raise RuntimeError(msg) from e

        team_info["signature"] = f"Failed to get data from ESPN API for {team_league}"
        return team_info, team_has_data, currently_playing

    return team_info, team_has_data, currently_playing
