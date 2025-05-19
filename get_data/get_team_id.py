"""Get the id of team for API calls."""
import statsapi  # type: ignore import warning
from nhlpy.nhl_client import NHLClient  # type: ignore import warning
import requests


def get_mlb_team_id(team: str) -> int:
    """Get MLB Team ID from team name.

    :param team: Name of MLB team to get ID for

    :return: integer representing Team ID
    """
    teams = statsapi.get('teams', {'sportIds': 1})['teams']
    id_list = {t["clubName"]: t["id"] for t in teams}
    for key, value in id_list.items():
        if key.upper() in team.upper():
            return value

    raise ValueError(f"Unknown MLB team name: {team}")


def get_nhl_game_id(team_name: str) -> int:
    """Get NHL Team ID from team name

    :param team: Name of NHL team to get ID for

    :return: integer representing Team ID
    """
    client = NHLClient(verbose=True)
    client.teams.teams_info()  # returns id + abbreviation + name of all teams
    resp = requests.get("https://api.nhle.com/stats/rest/en/team")
    res = resp.json()
    for teams in res["data"]:
        if teams["fullName"].upper() in team_name.upper():
            abbr = teams["triCode"]

    id = client.schedule.get_schedule_by_team_by_week(team_abbr=abbr)[0]["id"]

    return id
