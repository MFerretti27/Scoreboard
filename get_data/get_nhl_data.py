"""Get NHL from NHL specific API."""
from datetime import UTC
from pathlib import Path
from typing import Any

import requests
from dateutil.parser import isoparse  # type: ignore

import settings
from helper_functions.data_helpers import check_playing_each_other

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
    except (requests.exceptions.RequestException, IndexError) as e:
        print(f"Error fetching NHL data: {e}, team: {team_name}")
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
    folder_path = Path.cwd() / "images" / "sport_logos" / "NHL"
    file_names = [f for f in Path(folder_path).iterdir() if Path.is_file(Path.cwd() / folder_path / f)]
    for file in file_names:
        filename = file.name.upper()
        if home_team_name.upper() in filename:
            home_team = filename
        if away_team_name.upper() in filename:
            away_team = filename
    team_info["away_logo"] = str(Path.cwd() / "images" / "sport_logos" / "NHL" / away_team.replace("PNG", "png"))
    team_info["home_logo"] = str(Path.cwd() / "images" / "sport_logos" / "NHL" / home_team.replace("PNG", "png"))

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

    # Check if game is a championship game, if so display its championship game
    if get_game_type("NHL", team_name) != "":
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
            team_info["bottom_info"] += get_play_by_play(box_score["id"],
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
    """Get play by play information."""
    global last_play_saved

    play_by_play = requests.get(f"https://api-web.nhle.com/v1/gamecenter/{game_id}/play-by-play", timeout=5)
    play = play_by_play.json()
    plays = play["plays"][-1]["typeDescKey"]

    last_play = ""

    # Get play and player if shooting play
    if plays not in ["period-end", "giveaway", "stoppage"]:
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
                    last_play= plays.replace("-", " ")

    if last_play != "":
        last_play = "  " + last_play

    if last_play == last_play_saved:
        last_play = ""
    else:
        last_play_saved = last_play

    return last_play
