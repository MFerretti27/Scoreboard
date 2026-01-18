"""Data validation functions for API responses.

Validates that API responses contain all required fields before data is used.
Raises DataValidationError when required fields are missing.
"""
from __future__ import annotations

from typing import Any

from helper_functions.exceptions import DataValidationError
from helper_functions.logger_config import logger


def validate_espn_competition(competition: dict[str, Any], league: str, sport: str) -> None:
    """Validate ESPN competition/event data has required fields.

    :param competition: Competition dict from ESPN API
    :param league: League name (MLB, NBA, NFL, NHL)
    :param sport: Sport name
    :raises DataValidationError: If required fields are missing
    """
    logger.debug("Validating ESPN %s competition payload for sport %s", league, sport)

    required_fields = ["competitors", "status", "date"]
    missing = [field for field in required_fields if field not in competition]

    if missing:
        msg = f"ESPN {league} competition missing required fields"
        raise DataValidationError(
            msg,
            missing_fields=missing,
        )

    # Validate competitors structure
    competitors = competition.get("competitors", [])
    if not isinstance(competitors, list) or len(competitors) < 2:
        msg = f"ESPN {league} competition has invalid competitors structure"
        raise DataValidationError(
            msg,
            missing_fields=["competitors[0]", "competitors[1]"],
        )

    # Validate each competitor has essential fields
    for idx, competitor in enumerate(competitors):
        required_competitor_fields = ["team", "score"]
        missing_comp = [f for f in required_competitor_fields if f not in competitor]
        if missing_comp:
            msg = f"ESPN {league} competitor {idx} missing fields"
            raise DataValidationError(
                msg,
                missing_fields=[f"competitors[{idx}].{f}" for f in missing_comp],
            )

        # Validate team info
        if "team" in competitor:
            team = competitor["team"]
            if not isinstance(team, dict) or "displayName" not in team:
                msg = f"ESPN {league} competitor {idx} team missing displayName"
                raise DataValidationError(
                    msg,
                    missing_fields=[f"competitors[{idx}].team.displayName"],
                )

    logger.debug(f"Validated ESPN {league} competition data")


def validate_espn_event(event: dict[str, Any], league: str) -> None:
    """Validate ESPN event has required fields.

    :param event: Event dict from ESPN API
    :param league: League name
    :raises DataValidationError: If required fields are missing
    """
    required_fields = ["name", "competitions", "status"]
    missing = [field for field in required_fields if field not in event]

    if missing:
        msg = f"ESPN {league} event missing required fields"
        raise DataValidationError(
            msg,
            missing_fields=missing,
        )

    competitions = event.get("competitions", [])
    if not isinstance(competitions, list) or len(competitions) == 0:
        msg = f"ESPN {league} event has no competitions"
        raise DataValidationError(
            msg,
            missing_fields=["competitions[0]"],
        )

    logger.debug(f"Validated ESPN {league} event data")


def validate_mlb_game(game_data: dict[str, Any], team_name: str) -> None:
    """Validate MLB StatsAPI game data has required fields.

    :param game_data: Game dict from MLB StatsAPI
    :param team_name: Team name being validated
    :raises DataValidationError: If required fields are missing
    """
    required_fields = ["gameData", "liveData"]
    missing = [field for field in required_fields if field not in game_data]

    if missing:
        msg = f"MLB game data for {team_name} missing required sections"
        raise DataValidationError(
            msg,
            missing_fields=missing,
        )

    # Validate game data structure
    game_data_section = game_data.get("gameData", {})
    game_data_required = ["datetime", "status", "teams"]
    game_data_missing = [f for f in game_data_required if f not in game_data_section]

    if game_data_missing:
        msg = f"MLB gameData for {team_name} missing fields"
        raise DataValidationError(
            msg,
            missing_fields=[f"gameData.{f}" for f in game_data_missing],
        )

    # Validate teams exist
    teams = game_data_section.get("teams", {})
    if "home" not in teams or "away" not in teams:
        msg = f"MLB gameData for {team_name} missing home/away teams"
        raise DataValidationError(
            msg,
            missing_fields=["gameData.teams.home", "gameData.teams.away"],
        )

    # Validate liveData structure
    live_data = game_data.get("liveData", {})
    if "plays" not in live_data:
        msg = f"MLB liveData for {team_name} missing plays"
        raise DataValidationError(
            msg,
            missing_fields=["liveData.plays"],
        )

    logger.debug(f"Validated MLB game data for {team_name}")


def validate_nhl_boxscore(boxscore: dict[str, Any], team_name: str) -> None:
    """Validate NHL API boxscore has required fields.

    :param boxscore: Boxscore dict from NHL API
    :param team_name: Team name being validated
    :raises DataValidationError: If required fields are missing
    """
    required_fields = ["homeTeam", "awayTeam", "gameState", "period"]
    missing = [field for field in required_fields if field not in boxscore]

    if missing:
        msg = f"NHL boxscore for {team_name} missing required fields"
        raise DataValidationError(
            msg,
            missing_fields=missing,
        )

    # Validate team structures
    home_team = boxscore.get("homeTeam", {})
    away_team = boxscore.get("awayTeam", {})

    if "teamName" not in home_team:
        msg = f"NHL boxscore for {team_name} missing homeTeam.teamName"
        raise DataValidationError(
            msg,
            missing_fields=["homeTeam.teamName"],
        )

    if "teamName" not in away_team:
        msg = f"NHL boxscore for {team_name} missing awayTeam.teamName"
        raise DataValidationError(
            msg,
            missing_fields=["awayTeam.teamName"],
        )

    # Validate score exists
    if "score" not in home_team or "score" not in away_team:
        msg = f"NHL boxscore for {team_name} missing scores"
        raise DataValidationError(
            msg,
            missing_fields=["homeTeam.score", "awayTeam.score"],
        )

    logger.debug(f"Validated NHL boxscore for {team_name}")


def validate_nba_game(game: dict[str, Any], team_name: str) -> None:
    """Validate NBA API game data has required fields.

    :param game: Game dict from NBA API
    :param team_name: Team name being validated
    :raises DataValidationError: If required fields are missing
    """
    required_fields = ["gameId", "gameTimeUTC", "homeTeam", "awayTeam"]
    missing = [field for field in required_fields if field not in game]

    if missing:
        msg = f"NBA game data for {team_name} missing required fields"
        raise DataValidationError(
            msg,
            missing_fields=missing,
        )

    # Validate team structures
    home_team = game.get("homeTeam", {})
    away_team = game.get("awayTeam", {})

    if "teamName" not in home_team or "score" not in home_team:
        msg = f"NBA game for {team_name} missing homeTeam data"
        raise DataValidationError(
            msg,
            missing_fields=["homeTeam.teamName", "homeTeam.score"],
        )

    if "teamName" not in away_team or "score" not in away_team:
        msg = f"NBA game for {team_name} missing awayTeam data"
        raise DataValidationError(
            msg,
            missing_fields=["awayTeam.teamName", "awayTeam.score"],
        )

    logger.debug(f"Validated NBA game data for {team_name}")


def validate_espn_scoreboard_response(response: dict[str, Any], league: str) -> None:
    """Validate ESPN scoreboard API response has required structure.

    :param response: Response from ESPN scoreboard API
    :param league: League name
    :raises DataValidationError: If response is malformed
    """
    if not isinstance(response, dict):
        msg = f"ESPN {league} scoreboard response is not a dictionary"
        raise DataValidationError(
            msg,
            missing_fields=["response structure"],
        )

    if "events" not in response:
        msg = f"ESPN {league} scoreboard response missing events"
        raise DataValidationError(
            msg,
            missing_fields=["events"],
        )

    events = response.get("events", [])
    if not isinstance(events, list):
        msg = f"ESPN {league} scoreboard events is not a list"
        raise DataValidationError(
            msg,
            missing_fields=["events structure"],
        )

    logger.debug(f"Validated ESPN {league} scoreboard response structure")


def validate_mlb_schedule_response(schedule: list[dict[str, Any]], team_name: str) -> None:
    """Validate MLB schedule response has required fields.

    :param schedule: Schedule list from StatsAPI
    :param team_name: Team name being validated
    :raises DataValidationError: If schedule is invalid
    """
    if not isinstance(schedule, list) or len(schedule) == 0:
        msg = f"MLB schedule for {team_name} is empty or invalid"
        raise DataValidationError(
            msg,
            missing_fields=["schedule[0]"],
        )

    first_game = schedule[0]
    if "game_id" not in first_game:
        msg = f"MLB schedule for {team_name} missing game_id"
        raise DataValidationError(
            msg,
            missing_fields=["game_id"],
        )

    logger.debug(f"Validated MLB schedule for {team_name}")


def validate_nhl_game_data(game_data: dict[str, Any], team_name: str) -> None:
    """Validate NHL game data has required fields.

    :param game_data: Game data from NHL API
    :param team_name: Team name being validated
    :raises DataValidationError: If required fields are missing
    """
    required_fields = ["awayTeam", "homeTeam", "boxscore"]
    missing = [field for field in required_fields if field not in game_data]

    if missing:
        msg = f"NHL game data for {team_name} missing required fields"
        raise DataValidationError(
            msg,
            missing_fields=missing,
        )

    logger.debug(f"Validated NHL game data for {team_name}")


def validate_nba_boxscore(boxscore: dict[str, Any], team_name: str) -> None:
    """Validate NBA boxscore has required fields for player stats.

    :param boxscore: Boxscore dict from NBA API
    :param team_name: Team name being validated
    :raises DataValidationError: If required fields are missing
    """
    if "game" not in boxscore:
        msg = f"NBA boxscore for {team_name} missing game section"
        raise DataValidationError(
            msg,
            missing_fields=["game"],
        )

    game = boxscore.get("game", {})
    required_fields = ["homeTeam", "awayTeam"]
    missing = [f for f in required_fields if f not in game]

    if missing:
        msg = f"NBA boxscore for {team_name} missing team data"
        raise DataValidationError(
            msg,
            missing_fields=[f"game.{f}" for f in missing],
        )

    # Validate players list exists
    home_team = game.get("homeTeam", {})
    away_team = game.get("awayTeam", {})

    if "players" not in home_team or "players" not in away_team:
        msg = f"NBA boxscore for {team_name} missing players data"
        raise DataValidationError(
            msg,
            missing_fields=["game.homeTeam.players", "game.awayTeam.players"],
        )

    logger.debug(f"Validated NBA boxscore for {team_name}")


def validate_mlb_series_response(series: dict[str, Any] | None, team_name: str) -> None:
    """Validate MLB series response has required fields.

    :param series: Series dict from StatsAPI or None
    :param team_name: Team name being validated
    :raises DataValidationError: If series data is invalid (but not if None/missing)
    """
    if series is None:
        return  # It's OK if series data is unavailable

    if not isinstance(series, dict):
        msg = f"MLB series data for {team_name} is not a dictionary"
        raise DataValidationError(
            msg,
            missing_fields=["series structure"],
        )

    logger.debug(f"Validated MLB series data for {team_name}")


def validate_nba_standings(standings: dict[str, Any], team_name: str) -> None:
    """Validate NBA standings response has required structure.

    :param standings: Standings dict from NBA API
    :param team_name: Team name being validated
    :raises DataValidationError: If required fields are missing
    """
    if "resultSets" not in standings:
        msg = f"NBA standings for {team_name} missing resultSets"
        raise DataValidationError(
            msg,
            missing_fields=["resultSets"],
        )

    result_sets = standings.get("resultSets", [])
    if not isinstance(result_sets, list) or len(result_sets) == 0:
        msg = f"NBA standings for {team_name} has no result sets"
        raise DataValidationError(
            msg,
            missing_fields=["resultSets[0]"],
        )

    logger.debug(f"Validated NBA standings for {team_name}")


def validate_nhl_standings(standings: dict[str, Any], team_name: str) -> None:
    """Validate NHL standings response has required structure.

    :param standings: Standings dict from NHL API
    :param team_name: Team name being validated
    :raises DataValidationError: If required fields are missing
    """
    if not isinstance(standings, dict):
        msg = f"NHL standings for {team_name} is not a dictionary"
        raise DataValidationError(
            msg,
            missing_fields=["standings structure"],
        )

    logger.debug(f"Validated NHL standings for {team_name}")


def validate_mlb_teams_response(teams_response: dict[str, Any]) -> None:
    """Validate MLB teams response has required fields.

    :param teams_response: Teams response dict from statsapi
    :raises DataValidationError: If required fields are missing
    """
    required_fields = ["teams"]
    missing = [field for field in required_fields if field not in teams_response]

    if missing:
        msg = "MLB teams response missing required fields"
        raise DataValidationError(
            msg,
            missing_fields=missing,
        )

    teams = teams_response.get("teams", [])
    if not isinstance(teams, list):
        msg = "MLB teams is not a list"
        raise DataValidationError(
            msg,
            missing_fields=["teams (invalid type)"],
        )

    if len(teams) == 0:
        msg = "MLB teams response contains no teams"
        raise DataValidationError(
            msg,
            missing_fields=["teams[0]"],
        )

    # Validate each team has required fields
    for idx, team in enumerate(teams):
        required_team_fields = ["clubName", "id"]
        missing_team = [f for f in required_team_fields if f not in team]
        if missing_team:
            msg = f"MLB team {idx} missing fields"
            raise DataValidationError(
                msg,
                missing_fields=[f"teams[{idx}].{f}" for f in missing_team],
            )

    logger.debug("Validated MLB teams response")


def validate_nhl_teams_response(teams_response: list[dict[str, Any]]) -> None:
    """Validate NHL teams response has required fields.

    :param teams_response: Teams list from NHLClient.teams.teams()
    :raises DataValidationError: If required fields are missing
    """
    if not isinstance(teams_response, list):
        msg = "NHL teams response is not a list"
        raise DataValidationError(
            msg,
            missing_fields=["teams (invalid type)"],
        )

    if len(teams_response) == 0:
        msg = "NHL teams response contains no teams"
        raise DataValidationError(
            msg,
            missing_fields=["teams[0]"],
        )

    # Validate each team has required fields
    for idx, team in enumerate(teams_response):
        if not isinstance(team, dict):
            msg = f"NHL team {idx} is not a dictionary"
            raise DataValidationError(
                msg,
                missing_fields=[f"teams[{idx}] (invalid type)"],
            )

        required_fields = ["name", "abbr"]
        missing_fields = [f for f in required_fields if f not in team]
        if missing_fields:
            msg = f"NHL team {idx} missing fields"
            raise DataValidationError(
                msg,
                missing_fields=[f"teams[{idx}].{f}" for f in missing_fields],
            )

    logger.debug("Validated NHL teams response")


def validate_nba_scoreboard_games(games: list[dict[str, Any]]) -> None:
    """Validate NBA scoreboard games list has required fields.

    :param games: Games list from NBA scoreboard API
    :raises DataValidationError: If required fields are missing
    """
    if not isinstance(games, list):
        msg = "NBA scoreboard games is not a list"
        raise DataValidationError(
            msg,
            missing_fields=["games (invalid type)"],
        )

    if len(games) == 0:
        msg = "NBA scoreboard contains no games"
        raise DataValidationError(
            msg,
            missing_fields=["games[0]"],
        )

    # Validate each game has required fields
    for idx, game in enumerate(games):
        required_fields = ["homeTeam", "awayTeam"]
        missing = [f for f in required_fields if f not in game]
        if missing:
            msg = f"NBA game {idx} missing fields"
            raise DataValidationError(
                msg,
                missing_fields=[f"games[{idx}].{f}" for f in missing],
            )

        # Validate team info in game
        for team_type in ["homeTeam", "awayTeam"]:
            team = game.get(team_type, {})
            required_team_fields = ["teamName", "teamTricode"]
            missing_team = [f for f in required_team_fields if f not in team]
            if missing_team:
                msg = f"NBA game {idx} {team_type} missing fields"
                raise DataValidationError(
                    msg,
                    missing_fields=[f"games[{idx}].{team_type}.{f}" for f in missing_team],
                )

    logger.debug("Validated NBA scoreboard games")


def validate_nba_teams_response(teams_response: list[dict[str, Any]]) -> None:
    """Validate NBA teams response has required fields.

    :param teams_response: Teams list from nba_teams.get_teams()
    :raises DataValidationError: If required fields are missing
    """
    if not isinstance(teams_response, list):
        msg = "NBA teams response is not a list"
        raise DataValidationError(
            msg,
            missing_fields=["teams (invalid type)"],
        )

    if len(teams_response) == 0:
        msg = "NBA teams response contains no teams"
        raise DataValidationError(
            msg,
            missing_fields=["teams[0]"],
        )

    # Validate each team has required fields
    for idx, team in enumerate(teams_response):
        required_fields = ["abbreviation", "id"]
        missing = [f for f in required_fields if f not in team]
        if missing:
            msg = f"NBA team {idx} missing fields"
            raise DataValidationError(
                msg,
                missing_fields=[f"teams[{idx}].{f}" for f in missing],
            )

    logger.debug("Validated NBA teams response")


def validate_nba_scoreboard_dict(scoreboard: dict[str, Any]) -> None:
    """Validate NBA scoreboard dict has required structure.

    :param scoreboard: Scoreboard dict from NBA API
    :raises DataValidationError: If required fields are missing
    """
    if "scoreboard" not in scoreboard:
        msg = "NBA scoreboard response missing scoreboard key"
        raise DataValidationError(
            msg,
            missing_fields=["scoreboard"],
        )

    scoreboard_data = scoreboard.get("scoreboard", {})
    if "games" not in scoreboard_data:
        msg = "NBA scoreboard missing games array"
        raise DataValidationError(
            msg,
            missing_fields=["scoreboard.games"],
        )

    logger.debug("Validated NBA scoreboard structure")


def validate_mlb_schedule_games(games: list[dict[str, Any]], team_name: str) -> None:
    """Validate MLB schedule games list has required fields for game type detection.

    :param games: Games list from statsapi.schedule()
    :param team_name: Team name being validated
    :raises DataValidationError: If required fields are missing
    """
    if not isinstance(games, list):
        msg = f"MLB schedule for {team_name} is not a list"
        raise DataValidationError(
            msg,
            missing_fields=["games (invalid type)"],
        )

    if len(games) == 0:
        msg = f"MLB schedule for {team_name} contains no games"
        raise DataValidationError(
            msg,
            missing_fields=["games[0]"],
        )

    # Validate first game has game_type field
    first_game = games[0]
    if "game_type" not in first_game:
        msg = f"MLB game for {team_name} missing game_type"
        raise DataValidationError(
            msg,
            missing_fields=["games[0].game_type"],
        )

    logger.debug(f"Validated MLB schedule for {team_name}")


def validate_nhl_game_center_response(response: dict[str, Any], team_name: str) -> None:
    """Validate NHL game center API response.

    :param response: Response dict from NHL game center API
    :param team_name: Team name being validated
    :raises DataValidationError: If required fields are missing
    """
    if "seasonSeries" not in response:
        msg = f"NHL game center response for {team_name} missing seasonSeries"
        raise DataValidationError(
            msg,
            missing_fields=["seasonSeries"],
        )

    season_series = response.get("seasonSeries", [])
    if not isinstance(season_series, list) or len(season_series) == 0:
        msg = f"NHL game center for {team_name} has no season series data"
        raise DataValidationError(
            msg,
            missing_fields=["seasonSeries[0]"],
        )

    first_series = season_series[0]
    required_fields = ["gameType", "awayTeam", "homeTeam"]
    missing = [f for f in required_fields if f not in first_series]
    if missing:
        msg = f"NHL season series for {team_name} missing fields"
        raise DataValidationError(
            msg,
            missing_fields=[f"seasonSeries[0].{f}" for f in missing],
        )

    logger.debug(f"Validated NHL game center response for {team_name}")


def validate_nhl_playoff_response(playoff_data: dict[str, Any]) -> None:
    """Validate NHL playoff carousel API response.

    :param playoff_data: Playoff data dict from NHL API
    :raises DataValidationError: If required fields are missing
    """
    if "currentRound" not in playoff_data:
        msg = "NHL playoff data missing currentRound"
        raise DataValidationError(
            msg,
            missing_fields=["currentRound"],
        )

    logger.debug("Validated NHL playoff response")


def validate_espn_scoreboard_event(event: dict[str, Any], team_name: str) -> None:
    """Validate ESPN scoreboard event for NFL game type detection.

    :param event: Event dict from ESPN API
    :param team_name: Team name being validated
    :raises DataValidationError: If required fields are missing
    """
    if "season" not in event:
        msg = f"ESPN event for {team_name} missing season data"
        raise DataValidationError(
            msg,
            missing_fields=["season"],
        )

    season = event.get("season", {})
    if "type" not in season:
        msg = f"ESPN season data for {team_name} missing type"
        raise DataValidationError(
            msg,
            missing_fields=["season.type"],
        )

    logger.debug(f"Validated ESPN event for {team_name}")
