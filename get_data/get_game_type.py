import logging
import os
from datetime import datetime, timedelta

import requests
import statsapi  # type: ignore
from nba_api.live.nba.endpoints import scoreboard  # type: ignore
from nhlpy.nhl_client import NHLClient  # type: ignore

from .get_team_id import get_mlb_team_id, get_nhl_game_id

was_championship_game = False


def get_game_type(team_league: str, team_name: str) -> str:
    """Get the game type from the command line arguments or settings file.

    :param team_league: The league of the team (e.g., MLB, NHL, NBA, NFL)
    :param team_name: The name of the team

    :return: Game type as a string
    """
    if "MLB" in team_league.upper():
        return (get_mlb_game_type(team_name))
    elif "NHL" in team_league.upper():
        return (get_nhl_game_type(team_name))
    elif "NBA" in team_league.upper():
        return (get_nba_game_type())
    else:
        return ""


def get_nba_game_type() -> str:
    """Check if NBA game is championship.

    :return: Path for championship image or empty string if not a championship game
    """
    global was_championship_game
    # Today's Score Board
    try:
        games = scoreboard.ScoreBoard()
        live = games.get_dict()
        game_type = live["scoreboard"]["games"][0]["gameLabel"]
        was_championship_game = True if "NBA Finals" in game_type else False
    except Exception as e:
        print(f"Error getting NBA game type: {e}")
        if was_championship_game:
            return f"{os.getcwd()}/images/championship_images/nba_finals.png"
        return ""

    if game_type == "NBA Finals":
        return f"{os.getcwd()}/images/championship_images/nba_finals.png"
    else:
        return ""


def get_mlb_game_type(team_name: str) -> str:
    """Check if MLB game is championship.

    :return: Path for championship image or empty string if not a championship game
    """
    try:
        # Try to get first game from now for the next 3 days
        today = datetime.now().strftime("%Y-%m-%d")
        three_days_later = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")
        games = statsapi.schedule(
            team=get_mlb_team_id(team_name), include_series_status=True, start_date=today, end_date=three_days_later
        )
        game_type = games.get("game_type")
        if game_type == "WS":
            return f"{os.getcwd()}/images/championship_images/world_series.png"
        elif game_type == "ALCS":
            return f"{os.getcwd()}/images/conference_championship_images/alcs.png"
        elif game_type == "NLCS":
            return f"{os.getcwd()}/images/conference_championship_images/nlcs.png"
        elif game_type == "P":
            return f"{os.getcwd()}/images/playoff_images/mlb_postseason.png"
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
        now = datetime.now()
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

        # Check if the team is in the championship series
        current_round = playoff_info["currentRound"]
        path = ""
        if (away_team_abbr == your_team_abbr or home_team_abbr == your_team_abbr):

            if current_round == 4:
                path = f"{os.getcwd()}/images/championship_images/stanley_cup.png"
            elif current_round == 3 and conference == "Eastern":
                path = f"{os.getcwd()}/images/conference_championship_images/nhl_eastern_championship.png"
            elif current_round == 3 and conference == "Western":
                path = f"{os.getcwd()}/images/conference_championship_images/nhl_western_championship.png"
            else:
                path = f"{os.getcwd()}/images/playoff_images/nfl_playoffs.png"
        return path

    except Exception as e:
        print(f"Error getting NHL game type: {e}")
        return ""
