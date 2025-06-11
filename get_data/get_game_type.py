import logging
from datetime import UTC, datetime, timedelta
from pathlib import Path

import requests
import statsapi  # type: ignore
from nba_api.live.nba.endpoints import scoreboard  # type: ignore
from nhlpy.nhl_client import NHLClient  # type: ignore

from .get_team_id import get_mlb_team_id, get_nhl_game_id

# NBA only has data for one day so store if it was a championship game to display for longer
was_finals_game: list[bool: str] = [False, ""]
was_western_championship_game: list[bool: str] = [False, ""]
was_eastern_championship_game: list[bool: str] = [False, ""]
was_playoff_game: list[bool: str] = [False, ""]


def get_game_type(team_league: str, team_name: str) -> str:
    """Get the if game is championship or playoff.

    :param team_league: The league of the team (e.g., MLB, NHL, NBA, NFL)
    :param team_name: The name of the team

    :return: Image path or empty string if not a championship/playoff game
    """
    if "MLB" in team_league.upper():
        return (get_mlb_game_type(team_name))
    if "NHL" in team_league.upper():
        return (get_nhl_game_type(team_name))
    if "NBA" in team_league.upper():
        return (get_nba_game_type(team_name))

    return ""


def get_nba_game_type(team_name) -> str:
    """Check if NBA game is championship.

    :return: Path for championship image or empty string if not a championship game
    """

    try:
        games = scoreboard.ScoreBoard()  # Today's Score Board
        live = games.get_dict()
        game_type = live["scoreboard"]["games"][0]["gameLabel"]

        # Store data for when scoreboard data is not available
        was_finals_game[0] = "NBA Finals" in game_type
        was_finals_game[1] = team_name if was_finals_game[0] else ""

    except Exception as e:
        print(f"Error getting NBA game type: {e}")
        if was_finals_game[0] and was_finals_game[1] == team_name:
            return str(Path.cwd() / "images" / "championship_images" / "nba_finals.png")
        return ""

    if game_type == "NBA Finals":
        return str(Path.cwd() / "images" / "championship_images" / "nba_finals.png")

    return ""


def get_mlb_game_type(team_name: str) -> str:
    """Check if MLB game is championship.

    :return: Path for championship image or empty string if not a championship game
    """
    try:
        # Try to get first game from now for the next 3 days
        today = datetime.now(UTC).strftime("%Y-%m-%d")
        three_days_later = (datetime.now(UTC) + timedelta(days=3)).strftime("%Y-%m-%d")
        games = statsapi.schedule(
            team=get_mlb_team_id(team_name), include_series_status=True, start_date=today, end_date=three_days_later
        )
        game_type = games.get("game_type")
        if game_type == "WS":
            return f"{Path.cwd()}/images/championship_images/world_series.png"
        if game_type == "ALCS":
            return str(Path.cwd() / "images" / "conference_championship_images" / "alcs.png")
        if game_type == "NLCS":
            return str(Path.cwd() / "images" / "conference_championship_images" / "nlcs.png")
        if game_type == "P":
            return str(Path.cwd() / "images" / "playoff_images" / "mlb_postseason.png")
        else:
            return ""

    except Exception:
        return ""


def get_nhl_game_type(team_name: str) -> str:
    """Check if NHL game is championship.

    :return: Path for championship image or empty string if not a championship game
    """
    try:

        logging.getLogger("httpx").setLevel(logging.WARNING)

        # Get abbreviations for the teams in the current game
        team_id = get_nhl_game_id(team_name)
        resp = requests.get(f"https://api-web.nhle.com/v1/gamecenter/{team_id}/right-rail")
        res = resp.json()

        away_team_abbr = res["seasonSeries"][0]["awayTeam"]["abbrev"]
        home_team_abbr = res["seasonSeries"][0]["homeTeam"]["abbrev"]

        # Get the conference of the your team and your team abbreviation
        client = NHLClient(verbose=True)
        client.teams.teams_info()  # conference, division, abbreviation, and name of all teams
        for team in client.teams.teams_info():
            if team_name in team["name"]:
                conference = team["conference"]["name"]
                your_team_abbr = team["abbr"]
                break

        # Get the current season year
        now = datetime.now(UTC)
        year = now.year
        month = now.month

        if month >= 10:  # Season starts in October
            start_year = year
            end_year = year + 1
        else:
            start_year = year - 1
            end_year = year

        season = f"{start_year}{end_year}"

        # Get playoff information for the current season
        playoff_info = requests.get(f"https://api-web.nhle.com/v1/playoff-series/carousel/{season}/")
        playoff_info = playoff_info.json()

        # Check if the team is in the playoffs/championship
        current_round = playoff_info["currentRound"]
        path = ""
        if (your_team_abbr in (away_team_abbr, home_team_abbr)):

            if current_round == 4:
                path = str(Path.cwd() / "images" / "championship_images" / "stanley_cup.png")
            elif current_round == 3 and conference == "Eastern":
                path = str(Path.cwd() / "images" / "conference_championship_images" / "nhl_eastern_championship.png")
            elif current_round == 3 and conference == "Western":
                path = str(Path.cwd() / "images" / "conference_championship_images" / "nhl_western_championship.png")
            elif current_round in [2, 1]:
                path = str(Path.cwd() / "images" / "playoff_images" / "nhl_playoffs.png")
        return path

    except Exception as e:
        print(f"Error getting NHL game type: {e}")
        return ""
