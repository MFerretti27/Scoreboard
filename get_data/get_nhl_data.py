"""Get NHL from NHL specific API."""
import requests
from datetime import datetime, timezone
import os
from .get_series_data import get_current_series_nhl
from .get_team_id import get_nhl_game_id
import settings


def get_all_nhl_data(team_name: dict[str, str]) -> tuple[dict[str, str], bool, bool]:
    """Get all information for NHL team.

    Call this if ESPN fails to get MLB data as backup.

    :param team_name: The team name to get information for

    :return team_info: dictionary containing team information to display
    """
    team_info = {}
    currently_playing = False
    has_data = False
    try:
        id = get_nhl_game_id(team_name)
        resp = requests.get(f"https://api-web.nhle.com/v1/gamecenter/{id}/right-rail")
        live_data = requests.get(f"https://api-web.nhle.com/v1/gamecenter/{id}/boxscore")
    except Exception:
        return team_info, has_data, currently_playing  # Could not find any game to display

    live = live_data.json()
    res = resp.json()
    has_data = True

    # Set scores to 0, will get updated later once game starts
    team_info["home_score"] = "0"
    team_info["away_score"] = "0"
    team_info["under_score_image"] = ""  # Cannot get network image so set to nothing

    # Get team names
    away_team_name = live["awayTeam"]["commonName"]["default"]
    home_team_name = live["homeTeam"]["commonName"]["default"]
    team_info["above_score_txt"] = f"{away_team_name} @ {home_team_name}"

    # Get team record
    if settings.display_records:
        record_data = requests.get("https://api-web.nhle.com/v1/standings/now")
        record = record_data.json()
        for team in record["standings"]:
            if home_team_name in team["teamName"]["default"]:
                team_info["home_record"] = str(team["wins"]) + "-"
                team_info["home_record"] += str(team["losses"])
                break
        for team in record["standings"]:
            if away_team_name in team["teamName"]["default"]:
                team_info["away_record"] = str(team["wins"]) + "-"
                team_info["away_record"] += str(team["losses"])
                break

    # Get team logos
    folder_path = os.getcwd() + '/images/sport_logos/NHL/'
    file_names = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
    for file in file_names:
        if home_team_name.upper() in file:
            home_team = file
        if away_team_name.upper() in file:
            away_team = file
    team_info["away_logo"] = (f"{os.getcwd()}/images/sport_logos/NHL/{away_team}")
    team_info["home_logo"] = (f"{os.getcwd()}/images/sport_logos/NHL/{home_team}")

    # Get game time and venue
    iso_string = res["seasonSeries"][2]["startTimeUTC"]
    utc_time = datetime.strptime(iso_string, "%Y-%m-%dT%H:%M:%SZ")
    utc_time = utc_time.replace(tzinfo=timezone.utc)
    local_time = utc_time.astimezone()

    game_time = local_time.strftime("%-m/%-d %-I:%M %p")
    if settings.display_venue:
        venue = live["venue"]["default"]
        team_info["bottom_info"] = f"{game_time} @ {venue}"
    else:
        team_info["bottom_info"] = f"{game_time}"

    # Check if game is playing
    if "LIVE" in res["seasonSeries"][2]["gameState"]:
        currently_playing = True
        team_info = append_nhl_data(team_info, team_name)

    # Check if game is over
    elif "FINAL" in res["seasonSeries"][2]["gameState"]:
        team_info["top_info"] = get_current_series_nhl(team_name)
        team_info["bottom_info"] = "FINAL"

    resp.close()
    live_data.close()
    return team_info, has_data, currently_playing


def append_nhl_data(team_info: dict[str, str], team_name: str) -> dict:
    """Get information for NHL team if playing.

    :param team_info: Dictionary where data is stored to display
    :param team_name: The team name to get information for

    :return team_info: dictionary containing team information to display
    """
    id = get_nhl_game_id(team_name)
    resp = requests.get(f"https://api-web.nhle.com/v1/gamecenter/{id}/right-rail")
    res = resp.json()

    # Get shots on goal of each team
    if settings.display_nhl_sog:
        away_shots_on_goal = res["teamGameStats"][0]["awayValue"]
        home_shots_on_goal = res["teamGameStats"][0]["homeValue"]
        team_info["top_info"] = (f"Shots on Goal: {away_shots_on_goal} \t\t Shots on Goal: {home_shots_on_goal}")

    # Get clock and period to display
    if settings.display_nhl_clock:
        clock = res["seasonSeries"][2]["clock"]["timeRemaining"]
        period = str(res["seasonSeries"][2]["periodDescriptor"]["number"])
        if period == "1":
            period += "st"
        elif period == "2":
            period += "nd"
        elif period == "3":
            period += "rd"
        team_info["bottom_info"] = f"{clock} - {period}"

    # Get score
    team_info["home_score"] = res["linescore"]["totals"]["home"]
    team_info["away_score"] = res["linescore"]["totals"]["away"]

    resp.close()
    return team_info
