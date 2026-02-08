"""Get the id of team for API calls."""
from __future__ import annotations

import statsapi  # type: ignore[import]
from nba_api.live.nba.endpoints import scoreboard  # type: ignore[import]
from nba_api.stats.static import teams as nba_teams  # type: ignore[import]
from nhlpy.nhl_client import NHLClient  # type: ignore[import]

from helper_functions.api_utils.cache import TEAM_ID_TTL, cache_result
from helper_functions.api_utils.exceptions import APIError, DataValidationError
from helper_functions.api_utils.validators import (
    validate_mlb_teams_response,
    validate_nba_scoreboard_games,
    validate_nba_teams_response,
    validate_nhl_teams_response,
)


@cache_result(ttl=TEAM_ID_TTL, key_prefix="mlb_team_id")
def get_mlb_team_id(team: str) -> int:
    """Get MLB Team ID from team name.

    :param team: Name of MLB team to get ID for
    :return: integer representing Team ID
    """
    try:
        teams_response = statsapi.get("teams", {"sportIds": 1})
        validate_mlb_teams_response(teams_response)
    except DataValidationError as e:
        msg = f"Invalid MLB teams response: {e!s}"
        raise APIError(
            msg,
            error_code="INVALID_TEAM_DATA",
        ) from e

    teams = teams_response["teams"]
    id_list = {t["clubName"]: t["id"] for t in teams}
    for key, value in id_list.items():
        if key.upper() in team.upper():
            return value

    msg = f"Unknown MLB team name: {team}"
    raise ValueError(msg)


@cache_result(ttl=TEAM_ID_TTL, key_prefix="nhl_game_id")
def get_nhl_game_id(team_name: str) -> int:
    """Get NHL Team ID from team name.

    :param team: Name of NHL team to get ID for

    :return: integer representing Team ID
    """
    try:
        client = NHLClient()
        teams_list = client.teams.teams()
        validate_nhl_teams_response(teams_list)
    except DataValidationError as e:
        msg = f"Invalid NHL teams response: {e!s}"
        raise APIError(
            msg,
            error_code="INVALID_TEAM_DATA",
        ) from e

    abbr = None
    for team in teams_list:
        if team["name"] in team_name:
            abbr = team["abbr"]
            break

    if abbr is None:
        msg = f"Unknown NHL team name: {team_name}"
        raise ValueError(msg)

    return client.schedule.team_weekly_schedule(team_abbr=abbr)[0]["id"]


@cache_result(ttl=TEAM_ID_TTL, key_prefix="nba_team_id")
def get_nba_team_id(team_name: str) -> int:
    """Get NBA Team ID from team name.

    :param team: Name of NHL team to get ID for

    :return: integer representing Team ID
    """
    try:
        nba_team_names = nba_teams.get_teams()
        validate_nba_teams_response(nba_team_names)

        games = scoreboard.ScoreBoard()
        live = games.get_dict()
        games_list = live.get("scoreboard", {}).get("games", [])
        validate_nba_scoreboard_games(games_list)
    except DataValidationError as e:
        msg = f"Invalid NBA data response: {e!s}"
        raise APIError(
            msg,
            error_code="INVALID_TEAM_DATA",
        ) from e

    team_abbreviation = None
    for game in games_list:
        if game["homeTeam"]["teamName"] in team_name:
            team_abbreviation = game["homeTeam"]["teamTricode"]
            break

        if game["awayTeam"]["teamName"] in team_name:
            team_abbreviation = game["awayTeam"]["teamTricode"]
            break

    if team_abbreviation is None:
        msg = f"Unknown NBA team name: {team_name}"
        raise ValueError(msg)

    # Select the dictionary for the team which contains their team ID
    team = next(
        team for team in nba_team_names if team["abbreviation"] == team_abbreviation
    )
    return team["id"]
