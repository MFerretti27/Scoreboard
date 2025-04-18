'''Get series information'''
import statsapi
from datetime import datetime
import requests
from .get_team_id import get_mlb_team_id, get_nhl_game_id


def get_series(URL: str, team_name: str) -> dict:
    '''Try to get series information based of Team.'''
    if "MLB" in URL.upper():
        return(get_current_series_mlb(team_name))
    elif "NHL" in URL.upper():
        return(get_current_series_nhl(team_name))


def get_current_series_mlb(team_name) -> str:
    """Try to get the series information for baseball."""
    series_summary = ""
    try: 
        team_id = get_mlb_team_id(team_name)

        # Get today's games for that team
        today = datetime.now().strftime("%Y-%m-%d")
        schedule = statsapi.schedule(team=team_id, start_date=today, end_date=today)

        game = schedule[0]  # Take the first game today
        series_summary = game.get("series_status")
        return series_summary
    except:
        return series_summary


def get_current_series_nhl(team_name) -> str:
    """Try to get the series information for hockey."""
    series_summary = ""
    try:
        id = get_nhl_game_id(team_name)
        resp = requests.get(f"https://api-web.nhle.com/v1/gamecenter/{id}/right-rail")
        res = resp.json()

        away_series_wins = res["seasonSeriesWins"]["awayTeamWins"]
        home_series_wins = res["seasonSeriesWins"]["homeTeamWins"]

        away_abbrevation = res["seasonSeries"][0]["awayTeam"]["abbrev"]
        home_abbrevation = res["seasonSeries"][0]["homeTeam"]["abbrev"]

        if away_series_wins == 4:
            series_summary = f"{away_abbrevation} wins {away_series_wins}-{home_series_wins}"
        elif home_series_wins == 4:
            series_summary = f"{home_abbrevation} wins {home_series_wins}-{away_series_wins}"
        elif away_series_wins > home_series_wins:
            series_summary = f"{away_abbrevation} leads {away_series_wins}-{home_series_wins}"
        elif home_series_wins > away_series_wins:
            series_summary = f"{home_abbrevation} leads {home_series_wins}-{away_series_wins}"
        elif home_series_wins == away_series_wins:
            series_summary = f"Series Tied {away_series_wins} - {home_series_wins}"

        return series_summary
    except:
        series_summary