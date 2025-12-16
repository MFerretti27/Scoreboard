"""Get NHL from NHL specific API."""
from datetime import UTC
from typing import Any

import requests
from dateutil.parser import isoparse  # type: ignore[import]

import settings
from get_data.get_player_stats import get_player_stats
from helper_functions.data_helpers import check_playing_each_other, get_team_logo
from helper_functions.logger_config import logger

from .get_game_type import get_game_type
from .get_series_data import get_current_series_nhl
from .get_team_id import get_nhl_game_id

last_play_saved = ""

def get_all_nhl_data(team_name: str) -> tuple[dict[str, Any], bool, bool]:
    """Get all information for NHL team.

    Call this if ESPN fails to get MLB data as backup.

    :param team_name: The team name to get information for

    :return team_info: dictionary containing team information to display
    """
    team_info: dict[str, Any] = {}
    currently_playing: bool = False
    has_data: bool = False
    try:
        team_id = get_nhl_game_id(team_name)
        box_score = requests.get(f"https://api-web.nhle.com/v1/gamecenter/{team_id}/boxscore", timeout=5)
    except (requests.exceptions.RequestException, IndexError):
        logger.info("Error fetching NHL data for team: %s", team_name)
        return team_info, has_data, currently_playing  # Could not find any game to display

    box_score = box_score.json()
    has_data = True

    # Get Scores, they are only available if game is playing or has finished
    team_info["home_score"] = box_score["awayTeam"].get("score", "0")
    team_info["away_score"] = box_score["homeTeam"].get("score", "0")

    team_info["under_score_image"] = ""  # Cannot get network image so ensure its set to nothing

    # Get team names
    away_team_name = box_score["awayTeam"]["commonName"]["default"]
    home_team_name = box_score["homeTeam"]["commonName"]["default"]
    team_info["above_score_txt"] = f"{away_team_name} @ {home_team_name}"

    # Check if two of your teams are playing each other to not display same data twice
    full_home_team_name = box_score["homeTeam"]["placeName"]["default"] + " " + home_team_name
    full_away_team_name = box_score["awayTeam"]["placeName"]["default"] + " " + away_team_name
    if check_playing_each_other(full_home_team_name, full_away_team_name):
        team_has_data = False
        return team_info, team_has_data, currently_playing

    # Get team record
    if settings.display_records:
        record_data = requests.get("https://api-web.nhle.com/v1/standings/now", timeout=5).json()
        for team in record_data["standings"]:
            if home_team_name in team["teamName"]["default"]:
                team_info["home_record"] = str(team["wins"]) + "-" + str(team["losses"])

            if away_team_name in team["teamName"]["default"]:
                team_info["away_record"] = str(team["wins"]) + "-" + str(team["losses"])

    # Get team logos
    team_info = get_team_logo(home_team_name, away_team_name, "NHL", team_info)

    # Get game time and venue
    iso_string = box_score["startTimeUTC"]
    utc_time = isoparse(iso_string)
    game_time = utc_time.replace(tzinfo=UTC).astimezone().strftime("%-m/%-d - %-I:%M %p")

    team_info["bottom_info"] = f"{game_time}"
    if settings.display_venue:
        venue = box_score["venue"]["default"]
        team_info["bottom_info"] = f"{game_time} @ {venue}"

    # Check if game is playing
    # CRIT is final minutes of game, LIVE is game in progress
    if "LIVE" in box_score["gameState"] or "CRIT" in box_score["gameState"]:
        currently_playing = True
        team_info = append_nhl_data(team_info, team_name)

    # Check if game is over
    elif "FINAL" in box_score["gameState"] or "OFF" in box_score["gameState"]:
        team_info["top_info"] = get_current_series_nhl(team_name)
        team_info["bottom_info"] = get_final_status(box_score["periodDescriptor"]["number"],
                                                    box_score["gameType"])

        if settings.display_player_stats:
            home_player_stats, away_player_stats = get_player_stats("NBA", team_name)
            team_info["home_player_stats"] = home_player_stats
            team_info["away_player_stats"] = away_player_stats
            team_info.pop("under_score_image", None)  # Remove under score image if displaying player stats

    # Game has not started yet
    elif settings.display_odds:
        team_info["top_info"] = get_nhl_odds(box_score["homeTeam"]["abbrev"],
                                            box_score["awayTeam"]["abbrev"], team_name)

    # If str returned is not empty, then it Stanley Cup/conference championship, so display championship png
    team_info["under_score_image"] = get_game_type("NHL", team_name)

    return team_info, has_data, currently_playing


def append_nhl_data(team_info: dict[str, Any], team_name: str) -> dict:
    """Get information for NHL team if playing.

    :param team_info: Dictionary where data is stored to display
    :param team_name: The team name to get information for

    :return team_info: dictionary containing team information to display
    """
    team_id = get_nhl_game_id(team_name)
    box_score = requests.get(f"https://api-web.nhle.com/v1/gamecenter/{team_id}/boxscore", timeout=5)
    box_score = box_score.json()

    # Get shots on goal of each team
    if settings.display_nhl_sog:
        away_shots_on_goal = box_score["awayTeam"].get("sog", "0")
        home_shots_on_goal = box_score["homeTeam"].get("sog", "0")
        team_info["top_info"] = (f"Shots on Goal: {away_shots_on_goal} \t\t Shots on Goal: {home_shots_on_goal}")

    # Get clock and period to display
    if settings.display_nhl_clock:
        clock = box_score["clock"]["timeRemaining"]
        minutes, seconds = clock.split(":")
        clean_clock = f"{int(minutes)}:{seconds}"

        period_map = {
            "1": "1st",
            "2": "2nd",
            "3": "3rd",
            "4": "Overtime",
        }

        period = str(box_score["periodDescriptor"]["number"])
        period = period_map.get(period, "Shootout")

        # There is no shootouts in playoffs
        if box_score["gameType"] == 3 and box_score["periodDescriptor"]["number"] >= 4:
            period = "Overtime"

        team_info["bottom_info"] = f"{clean_clock} - {period}"

        if box_score["clock"]["inIntermission"]:
            team_info["bottom_info"] = f"End of {period}"

    # Get score
    team_info["home_score"] = box_score["homeTeam"]["score"]
    team_info["away_score"] = box_score["awayTeam"]["score"]

    # Get if team is in power play
    if settings.display_nhl_power_play:
        try:
            # Dont need to store info just has to ensure call is successful
            _ = box_score["situation"]["awayTeam"]["situationDescriptions"]
            team_info["away_power_play"] = True
        except KeyError:
            team_info["away_power_play"] = False
        try:
            # Dont need to store info just has to ensure call is successful
            _ = box_score["situation"]["homeTeam"]["situationDescriptions"]
            team_info["home_power_play"] = True
        except KeyError:
            team_info["home_power_play"] = False

    if settings.display_nhl_play_by_play:
        team_info["above_score_txt"] = team_info["bottom_info"]  # Move clock to above score
        team_info["bottom_info"] = get_play_by_play(box_score["id"],
                                                    box_score["homeTeam"]["abbrev"],
                                                    box_score["awayTeam"]["abbrev"])

    return team_info


def get_final_status(period_descriptor: int, game_type: int) -> str:
    """Get what should display as final status of game.

    :param game_type: what type of game is it playoff/regular season
    :param period_descriptor: what period the game ended in

    :returns final_status: str of what how final status should be displayed
    """
    if period_descriptor == 4:
        final_status = "FINAL/OT"
    elif period_descriptor > 4 and game_type <= 2:  # There are no shootouts in playoffs
        final_status = "FINAL/SO"
    elif period_descriptor > 4:
        final_status = "FINAL/OT"
    else:
        final_status = "FINAL"

    return final_status


def get_play_by_play(game_id: int, home_team_abrr: str, away_team_abbr: str) -> str:
    """Get play by play information.

    param game_id: The game ID to get play by play information for
    param home_team_abrr: The abbreviation of the home team
    param away_team_abbr: The abbreviation of the away team

    :return last_play: The last play that occurred in the game, if it was a shooting play
    """
    play_by_play = requests.get(f"https://api-web.nhle.com/v1/gamecenter/{game_id}/play-by-play", timeout=5)
    play = play_by_play.json()

    try:
        plays = play["plays"][-1]["typeDescKey"].capitalize()
    except IndexError:
        return ""

    last_play = ""

    # Get play and player if shooting play
    if plays not in ["Period-end", "Giveaway", "Stoppage"]:
        players = requests.get(f"https://api-web.nhle.com/v1/roster/{home_team_abrr}/current", timeout=5)
        positions = players.json()
        for position in positions:
            for player in positions[position]:
                try:
                    if player["id"] == play["plays"][-1]["details"]["shootingPlayerId"]:
                        last_play = plays.replace("-", " ") + " (" + player["lastName"]["default"] + ")"
                        break
                except KeyError:
                    last_play = plays.replace("-", " ")
        players = requests.get(f"https://api-web.nhle.com/v1/roster/{away_team_abbr}/current", timeout=5)
        positions = players.json()
        for position in positions:
            for player in positions[position]:
                try:
                    if player["id"] == play["plays"][-1]["details"]["shootingPlayerId"]:
                        last_play = plays.replace("-", " ") + " (" + player["lastName"]["default"] + ")"
                        break
                except KeyError:
                    last_play = plays.replace("-", " ")

    return last_play


def get_nhl_odds(home_team_abbr: str, away_team_abbr: str, team: str) -> str:
    """Get NHL odds for the game.

    :param home_team_abbr: The abbreviation of the home team
    :param away_team_abbr: The abbreviation of the away team
    :param team: The team name to get odds for

    :return str: The spread and over/under for the game
    """
    home_spread = None
    away_spread = None
    over_under = ""

    resp = requests.get("https://api-web.nhle.com/v1/partner-game/US/now", timeout=5)
    res = resp.json()
    for game in res["games"]:
        if game["homeTeam"]["name"]["default"] in team or game["awayTeam"]["name"]["default"] in team:
            for item in game["homeTeam"]["odds"]:
                desc = item["description"]
                qual = item["qualifier"]

                if desc == "PUCK_LINE":
                    home_spread = qual

                elif desc == "OVER_UNDER" and qual.startswith(("O", "U")):
                    over_under = qual

            for item in game["awayTeam"]["odds"]:
                desc = item["description"]
                qual = item["qualifier"]

                if desc == "PUCK_LINE":
                    away_spread = qual

            if home_spread and away_spread:
                home_val = float(home_spread.replace("+",""))
                away_val = float(away_spread.replace("+",""))

                if int(home_val) < int(away_val):
                    spread = f"{home_team_abbr} {home_spread}"
                else:
                    spread = f"{away_team_abbr} {away_spread}"
            else:
                spread = "N/A"

            over_under = over_under.replace("O", "").replace("U", "") if over_under else "N/A"

            return f"Spread: {spread} \t\t OverUnder: {over_under}"
    # If no matching game is found, return default values
    return "Spread: N/A \t OverUnder: N/A"
