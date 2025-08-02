"""Get the id of team for API calls."""
import requests
import statsapi  # type: ignore[import]
from nba_api.live.nba.endpoints import scoreboard  # type: ignore[import]
from nba_api.stats.static import teams as nba_teams  # type: ignore[import]
from nhlpy.nhl_client import NHLClient  # type: ignore[import]


def get_mlb_team_id(team: str) -> int:
    """Get MLB Team ID from team name.

    :param team: Name of MLB team to get ID for

    :return: integer representing Team ID
    """
    teams = statsapi.get("teams", {"sportIds": 1})["teams"]
    id_list = {t["clubName"]: t["id"] for t in teams}
    for key, value in id_list.items():
        if key.upper() in team.upper():
            return value

    msg = f"Unknown MLB team name: {team}"
    raise ValueError(msg)


def get_nhl_game_id(team_name: str) -> int:
    """Get NHL Team ID from team name.

    :param team: Name of NHL team to get ID for

    :return: integer representing Team ID
    """
    client = NHLClient(verbose=True)
    client.teams.teams_info()  # returns id + abbreviation + name of all teams
    resp = requests.get("https://api.nhle.com/stats/rest/en/team", timeout=5)
    res = resp.json()
    for teams in res["data"]:
        if teams["fullName"].upper() in team_name.upper():
            abbr = teams["triCode"]

    return client.schedule.get_schedule_by_team_by_week(team_abbr=abbr)[0]["id"]


def get_nba_team_id(team_name: str) -> int:
    """Get NBA Team ID from team name.

    :param team: Name of NHL team to get ID for

    :return: integer representing Team ID
    """
    nba_team_names = nba_teams.get_teams()
    games = scoreboard.ScoreBoard()
    live = games.get_dict()

    for game in live["scoreboard"]["games"]:
        if game["homeTeam"]["teamName"] in team_name:
            team_abbreviation = game["homeTeam"]["teamTricode"]
            break

        if game["awayTeam"]["teamName"] in team_name:
            team_abbreviation = game["awayTeam"]["teamTricode"]
            break

    # Select the dictionary for the Pacers, which contains their team ID
    team = next(team for team in nba_team_names if team["abbreviation"] == team_abbreviation)
    return team["id"]
