"""Get NHL from NHL specific API."""
from datetime import UTC
from pathlib import Path
from typing import Any

import requests
from dateutil.parser import isoparse  # type: ignore

import settings

from .get_game_type import get_game_type
from .get_series_data import get_current_series_nhl
from .get_team_id import get_nhl_game_id


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
    except requests.exceptions.RequestException as e:
        print(f"Error fetching NHL data: {e}")
        return team_info, has_data, currently_playing  # Could not find any game to display

    box_score = box_score.json()
    has_data = True

    # Get Scores, they are only available if game is playing or has finished
    try:
        team_info["home_score"] = box_score["awayTeam"]["score"]
        team_info["away_score"] = box_score["homeTeam"]["score"]
    except KeyError:
        team_info["home_score"] = "0"
        team_info["away_score"] = "0"

    team_info["under_score_image"] = ""  # Cannot get network image so ensure its set to nothing

    # Get team names
    away_team_name = box_score["awayTeam"]["commonName"]["default"]
    home_team_name = box_score["homeTeam"]["commonName"]["default"]
    team_info["above_score_txt"] = f"{away_team_name} @ {home_team_name}"

    # Get team record
    if settings.display_records:
        record_data = requests.get("https://api-web.nhle.com/v1/standings/now", timeout=5)
        record = record_data.json()
        for team in record["standings"]:
            if home_team_name in team["teamName"]["default"]:
                team_info["home_record"] = str(team["wins"]) + "-" + str(team["losses"])
                break
        for team in record["standings"]:
            if away_team_name in team["teamName"]["default"]:
                team_info["away_record"] = str(team["wins"]) + "-" + str(team["losses"])
                break

    # Get team logos
    folder_path = Path.cwd() / "images" / "sport_logos" / "NHL"
    file_names = [f for f in Path(folder_path).iterdir() if Path.is_file(Path.cwd() / folder_path / f)]
    for file in file_names:
        filename = file.name.upper()
        if home_team_name.upper() in filename:
            home_team = filename
        if away_team_name.upper() in filename:
            away_team = filename
    team_info["away_logo"] = str(Path.cwd() / "images" / "sport_logos" / "NHL" / away_team)
    team_info["home_logo"] = str(Path.cwd() / "images" / "sport_logos" / "NHL" / home_team)

    # Get game time and venue
    iso_string = box_score["startTimeUTC"]
    utc_time = isoparse(iso_string)
    utc_time = utc_time.replace(tzinfo=UTC)
    local_time = utc_time.astimezone()

    game_time = local_time.strftime("%-m/%-d %-I:%M %p")
    if settings.display_venue:
        venue = box_score["venue"]["default"]
        team_info["bottom_info"] = f"{game_time} @ {venue}"
    else:
        team_info["bottom_info"] = f"{game_time}"

    # Check if game is playing
    # CRIT is final minute of game, LIVE is game in progress
    if "LIVE" in box_score["gameState"] or "CRIT" in box_score["gameState"]:
        currently_playing = True
        team_info = append_nhl_data(team_info, team_name)

    # Check if game is over
    elif "FINAL" in box_score["gameState"] or "OFF" in box_score["gameState"]:
        team_info["top_info"] = get_current_series_nhl(team_name)

        if box_score["periodDescriptor"]["number"] == 4:
            team_info["bottom_info"] = "FINAL/OT"
        elif box_score["periodDescriptor"]["number"] > 4:
            team_info["bottom_info"] = "FINAL/SO"
        else:
            team_info["bottom_info"] = "FINAL"

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
        away_shots_on_goal = box_score["awayTeam"]["sog"]
        home_shots_on_goal = box_score["homeTeam"]["sog"]
        team_info["top_info"] = (f"Shots on Goal: {away_shots_on_goal} \t\t Shots on Goal: {home_shots_on_goal}")

    # Get clock and period to display
    if settings.display_nhl_clock:
        clock = str(box_score["clock"]["timeRemaining"])
        minutes, seconds = clock.split(":")
        clean_clock = f"{int(minutes)}:{seconds}"
        period = str(box_score["periodDescriptor"]["number"])
        if period == "1":
            period += "st"
        elif period == "2":
            period += "nd"
        elif period == "3":
            period += "rd"
        elif period == "4":
            period = "Overtime"
        elif period > "4":
            period = "Shootout"
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

    return team_info
