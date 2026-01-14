"""Get if the Game is playoff/championship."""

from datetime import UTC, datetime, timedelta
from pathlib import Path

import requests
import statsapi  # type: ignore[import]
from nba_api.live.nba.endpoints import scoreboard  # type: ignore[import]
from nhlpy.nhl_client import NHLClient  # type: ignore[import]

from helper_functions.logger_config import logger

from .get_team_id import get_mlb_team_id, get_nhl_game_id
from .get_team_league import MLB_AL_EAST, MLB_AL_WEST, MLB_NL_EAST, MLB_NL_WEST

# NBA only has data for one day so store if it was a championship game to display for longer
was_finals_game: list[bool | str] = [False, ""]
was_western_championship_game: list[bool | str] = [False, ""]
was_eastern_championship_game: list[bool | str] = [False, ""]
was_playoff_game: list[bool | str] = [False, ""]


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
    if "NFL" in team_league.upper():
        return (get_nfl_game_type(team_name))

    return ""


def get_nba_game_type(team_name: str) -> str:
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

    except Exception:
        logger.exception("Error getting NBA game type")
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
            team=get_mlb_team_id(team_name), include_series_status=True, start_date=today, end_date=three_days_later,
        )
        game_type = games[0].get("game_type")
        if game_type == "W":
            return f"{Path.cwd()}/images/championship_images/world_series.png"
        if game_type == "L" and team_name in (MLB_AL_EAST + MLB_AL_WEST):
            return str(Path.cwd() / "images" / "conference_championship_images" / "alcs.png")
        if game_type == "L" and team_name in (MLB_NL_EAST + MLB_NL_WEST):
            return str(Path.cwd() / "images" / "conference_championship_images" / "nlcs.png")
        if game_type in ["F", "D"]:
            return str(Path.cwd() / "images" / "playoff_images" / "mlb_postseason.png")

    except Exception:
        logger.exception("Could not get MLB game type")
        return ""

    return ""


def get_nhl_game_type(team_name: str) -> str:
    """Check if NHL game is championship.

    :return: Path for championship image or empty string if not a championship game
    """
    try:

        # Get abbreviations for the teams in the current game
        team_id = get_nhl_game_id(team_name)
        resp = requests.get(f"https://api-web.nhle.com/v1/gamecenter/{team_id}/right-rail", timeout=5)
        res = resp.json()

        if res["seasonSeries"][0]["gameType"] == 2:
            return ""

        away_team_abbr = res["seasonSeries"][0]["awayTeam"]["abbrev"]
        home_team_abbr = res["seasonSeries"][0]["homeTeam"]["abbrev"]

        # Get the conference of the your team and your team abbreviation
        client = NHLClient()
        for team in client.teams.teams():
            if team["name"] == team_name:
                your_team_abbr = team["abbr"]
                conference = team["conference"]["name"]

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
        playoff_info = requests.get(f"https://api-web.nhle.com/v1/playoff-series/carousel/{season}/", timeout=5)
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

    except Exception:
        logger.exception("Error getting NHL game type")
        return ""

    return path


def get_nfl_game_type(team_name: str) -> str:
    """Return a concise stage label for a game.

    Uses ESPN's season.type and optional notes/week to distinguish:
    - preseason, regular-season, playoffs (wild card/divisional/conference championship/super bowl)
    """
    # Fetch NFL scoreboard and find the event for this team
    resp = requests.get("https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard", timeout=5)
    data = resp.json()
    events = data.get("events", [])
    event = next((e for e in events if team_name in e.get("name", "")), None)
    if not event:
        logger.info("Game type: team not found in scoreboard")
        return ""

    season_type = event.get("season", {}).get("type")  # 1->preseason, 2->regular, 3->post-season

    # Default mapping by season type
    if season_type in (1, 2):
        label = "preseason" if season_type == 1 else "regular-season"
        logger.info("Game type: %s", label)
        return label
    if season_type != 3:
        logger.info("Game type: unknown season type")
        return ""

    # Postseason: refine using notes headline or week number
    headline = "".join(n.get("headline", "") for n in event.get("notes", [])).lower()
    week_num = event.get("week", {}).get("number")

    # Map playoff rounds to image paths
    playoff_images = {
        "super_bowl": str(Path.cwd() / "images" / "championship_images" / "super_bowl.png"),
        "afc_championship": str(Path.cwd() / "images" / "conference_championship_images" / "afc_championship.png"),
        "nfl_conference": str(
            Path.cwd() / "images" / "conference_championship_images" / "nfl_conference_championship.png"
        ),
        "playoffs": str(Path.cwd() / "images" / "playoff_images" / "nfl_playoffs.png"),
    }

    # Determine playoff stage and return appropriate image
    if "super bowl" in headline or week_num == 4:
        logger.info("Game type: playoffs - super bowl")
        return playoff_images["super_bowl"]
    if "conference championship" in headline or week_num == 3:
        logger.info("Game type: playoffs - conference championship")
        return playoff_images["afc_championship"] if week_num == 3 else playoff_images["nfl_conference"]

    # Wild card (week 1), divisional (week 2), or generic playoffs
    stage = "wild card" if ("wild card" in headline or week_num == 1) else "divisional/other"
    logger.info("Game type: playoffs - %s", stage)
    return playoff_images["playoffs"]

