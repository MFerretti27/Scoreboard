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
    abbr = None
    
    for team in client.teams.teams():
        if team.get("name", "") in team_name:
            abbr = team.get("abbr")
            break
    
    if not abbr:
        error_msg = f"Could not find NHL team abbreviation for: {team_name}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    schedule = client.schedule.team_weekly_schedule(team_abbr=abbr)
    if not schedule:
        error_msg = f"No NHL schedule found for team: {team_name} ({abbr})"
        logger.error(error_msg)
        raise ValueError(error_msg)
        
    return schedule[0]["id"]


def get_nba_team_id(team_name: str) -> int:
    """Get NBA Team ID from team name.

    :param team: Name of NHL team to get ID for

    :return: integer representing Team ID
    """
    nba_team_names = nba_teams.get_teams()
    games = scoreboard.ScoreBoard()
    live = games.get_dict()

    team_abbreviation = None
    scoreboard_data = live.get("scoreboard", {})
    games_list = scoreboard_data.get("games", [])
    
    for game in games_list:
        home_team = game.get("homeTeam", {})
        away_team = game.get("awayTeam", {})
        
        if home_team.get("teamName", "") in team_name:
            team_abbreviation = home_team.get("teamTricode")
            break

        if away_team.get("teamName", "") in team_name:
            team_abbreviation = away_team.get("teamTricode")
            break

    if not team_abbreviation:
        error_msg = f"Could not find NBA team abbreviation for: {team_name}"
        logger.error(error_msg)
        raise ValueError(error_msg)

    # Select the dictionary for the team, which contains their team ID
    team = next((team for team in nba_team_names if team.get("abbreviation") == team_abbreviation), None)
    
    if not team:
        error_msg = f"Could not find NBA team ID for abbreviation: {team_abbreviation}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    team_id = team.get("id")
    if not team_id:
        error_msg = f"NBA team data missing 'id' field for: {team_abbreviation}"
        logger.error(error_msg)
        raise ValueError(error_msg)
        
    return team_id
