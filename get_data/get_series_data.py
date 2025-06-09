"""Get series information."""
from datetime import datetime, timedelta

import requests
import statsapi  # type: ignore
from nba_api.live.nba.endpoints import scoreboard  # type: ignore

from .get_team_id import get_mlb_team_id, get_nhl_game_id

mlb_series = ""


def get_series(team_league: str, team_name: str) -> str:
    """Try to get series information based of Team.

    :param team_league: league to get series information for
    :param team_name: name of team to get series information for

    :return series_summary: str telling series information
    """
    if "MLB" in team_league.upper():
        return (get_current_series_mlb(team_name))
    elif "NHL" in team_league.upper():
        return (get_current_series_nhl(team_name))
    elif "NBA" in team_league.upper():
        return (get_current_series_nba(team_name))
    else:
        return ""


def get_current_series_mlb(team_name) -> str:
    """Try to get the series information for baseball team.

    :param team_name: name of team to get series information for

    :return series_summary: str telling series information
    """
    global mlb_series
    series_summary = ""
    try:
        team_id = get_mlb_team_id(team_name)

        # Get today's games for that team
        today = datetime.now().strftime("%Y-%m-%d")
        three_days_later = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")
        schedule = statsapi.schedule(team=team_id, start_date=today, end_date=three_days_later)

        game = schedule[0]  # Take the first game today
        series_summary = game.get("series_status", "")
        if series_summary == "" or series_summary is None:
            series_summary = mlb_series

        mlb_series = series_summary
        return series_summary
    except Exception as e:
        print(f"Error getting MLB series information: {e}")
        return series_summary


def get_current_series_nhl(team_name) -> str:
    """Try to get the series information for hockey team.

    :param team_name: name of team to get series information for

    :return series_summary: str telling series information
    """
    series_summary = ""
    try:
        team_id = get_nhl_game_id(team_name)
        resp = requests.get(f"https://api-web.nhle.com/v1/gamecenter/{team_id}/right-rail")
        res = resp.json()

        away_series_wins = res["seasonSeriesWins"]["awayTeamWins"]
        home_series_wins = res["seasonSeriesWins"]["homeTeamWins"]

        away_abbreviation = res["seasonSeries"][0]["awayTeam"]["abbrev"]
        home_abbreviation = res["seasonSeries"][0]["homeTeam"]["abbrev"]

        if away_series_wins == 4:
            series_summary = f"{away_abbreviation} wins {away_series_wins}-{home_series_wins}"
        elif home_series_wins == 4:
            series_summary = f"{home_abbreviation} wins {home_series_wins}-{away_series_wins}"
        elif away_series_wins > home_series_wins:
            series_summary = f"{away_abbreviation} leads {away_series_wins}-{home_series_wins}"
        elif home_series_wins > away_series_wins:
            series_summary = f"{home_abbreviation} leads {home_series_wins}-{away_series_wins}"
        elif home_series_wins == away_series_wins:
            series_summary = f"Series Tied {away_series_wins} - {home_series_wins}"

        return series_summary
    except Exception as e:
        print(f"Error getting NHL series information: {e}")
        return series_summary


def get_current_series_nba(team_name) -> str:
    """Try to get the series information for basketball team.

    :param team_name: name of team to get series information for

    :return series_summary: str telling series information
    """
    series_summary = ""
    # Today's Score Board
    games = scoreboard.ScoreBoard()
    live = games.get_dict()
    try:
        for game in live["scoreboard"]["games"]:
            if game["homeTeam"]["teamName"] in team_name or game["awayTeam"]["teamName"] in team_name:
                series_summary = game["seriesText"]
        return series_summary
    except Exception as e:
        print(f"Error getting NBA series information: {e}")
        return series_summary
