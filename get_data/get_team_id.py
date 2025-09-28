"""Get the id of team for API calls."""
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
    client = NHLClient()
    for team in client.teams.teams():
        if team["name"] in team_name:
            abbr = team["abbr"]

    return client.schedule.team_weekly_schedule(team_abbr=abbr)[0]["id"]


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
