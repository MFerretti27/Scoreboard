import os
from datetime import datetime

import requests
from nba_api.live.nba.endpoints import scoreboard  # type: ignore

was_championship_game = False


def get_game_type(team_league: str, team_name: str) -> str:
    """Get the game type from the command line arguments or settings file.

    :return: Game type as a string
    """
    if "MLB" in team_league.upper():
        return (get_mlb_game_type())
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


def get_mlb_game_type() -> str:
    """Check if MLB game is championship.

    :return: Path for championship image or empty string if not a championship game
    """
    return ""


def get_nhl_game_type(team_name: str) -> str:
    """Check if NHL game is championship.

    :return: Path for championship image or empty string if not a championship game
    """
    try:
        print(f"Getting NHL Game Type for {team_name}")
        resp = requests.get("https://api.nhle.com/stats/rest/en/team")
        res = resp.json()
        for teams in res["data"]:
            if team_name.upper() in teams["fullName"].upper():
                abbr = teams["triCode"]
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
        if (playoff_info["rounds"][3]["series"][0]["bottomSeed"]["abbrev"] == abbr or
            playoff_info["rounds"][3]["series"][0]["topSeed"]["abbrev"] == abbr):
            return f"{os.getcwd()}/images/championship_images/stanley_cup.png"
        else:
            return ""

    except Exception as e:
        print(f"Error getting NHL game type: {e}")
        return ""
