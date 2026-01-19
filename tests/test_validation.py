#!/usr/bin/env python3
"""Test input validation for API responses."""
from __future__ import annotations

from helper_functions.api_utils.exceptions import DataValidationError
from helper_functions.api_utils.validators import (
    validate_espn_competition,
    validate_espn_event,
    validate_espn_scoreboard_event,
    validate_espn_scoreboard_response,
    validate_mlb_game,
    validate_mlb_schedule_games,
    validate_mlb_schedule_response,
    validate_mlb_series_response,
    validate_mlb_teams_response,
    validate_nba_boxscore,
    validate_nba_game,
    validate_nba_scoreboard_dict,
    validate_nba_scoreboard_games,
    validate_nba_standings,
    validate_nba_teams_response,
    validate_nhl_boxscore,
    validate_nhl_game_center_response,
    validate_nhl_playoff_response,
    validate_nhl_standings,
    validate_nhl_teams_response,
)

# Test counter
tests_passed = 0
tests_failed = 0


def run_test(test_func: callable, test_name: str) -> None:
    """Run a test and track results."""
    global tests_passed, tests_failed
    try:
        test_func()
        tests_passed += 1
    except AssertionError:
        tests_failed += 1
    except Exception:
        tests_failed += 1


# ===== ESPN Scoreboard Tests =====
def test_espn_scoreboard_response_valid() -> None:
    """Test valid ESPN scoreboard response passes validation."""
    valid_response = {
        "events": [
            {
                "name": "Team A vs Team B",
                "competitions": [{"competitors": [], "status": {}, "date": "2024-01-01"}],
                "status": {},
            },
        ],
    }
    validate_espn_scoreboard_response(valid_response, "MLB")


def test_espn_scoreboard_response_missing_events() -> None:
    """Test ESPN scoreboard response without events raises validation error."""
    invalid_response = {"some_field": "value"}
    try:
        validate_espn_scoreboard_response(invalid_response, "MLB")
        msg = "Should have raised DataValidationError"
        raise AssertionError(msg)
    except DataValidationError as e:
        assert "missing events" in str(e).lower() or "events" in str(e)


# ===== ESPN Event Tests =====
def test_espn_event_valid() -> None:
    """Test valid ESPN event passes validation."""
    valid_event = {
        "name": "Team A vs Team B",
        "competitions": [{"competitors": []}],
        "status": {},
    }
    validate_espn_event(valid_event, "MLB")


def test_espn_event_missing_competitions() -> None:
    """Test ESPN event without competitions raises validation error."""
    invalid_event = {"name": "Team A vs Team B", "status": {}}
    try:
        validate_espn_event(invalid_event, "MLB")
        msg = "Should have raised DataValidationError"
        raise AssertionError(msg)
    except DataValidationError as e:
        assert "competitions" in str(e) or "missing" in str(e).lower()


# ===== ESPN Competition Tests =====
def test_espn_competition_valid() -> None:
    """Test valid ESPN competition passes validation."""
    valid_comp = {
        "competitors": [
            {"team": {"displayName": "Team A"}, "score": 5},
            {"team": {"displayName": "Team B"}, "score": 3},
        ],
        "status": {"type": {"shortDetail": "Final"}},
        "date": "2024-01-01T00:00:00Z",
    }
    validate_espn_competition(valid_comp, "MLB", "baseball")


def test_espn_competition_missing_score() -> None:
    """Test ESPN competition without score raises validation error."""
    invalid_comp = {
        "competitors": [
            {"team": {"displayName": "Team A"}},  # Missing score in first team
            {"team": {"displayName": "Team B"}, "score": 3},
        ],
        "status": {},
        "date": "2024-01-01T00:00:00Z",
    }
    try:
        validate_espn_competition(invalid_comp, "MLB", "baseball")
        msg = "Should have raised DataValidationError for missing score"
        raise AssertionError(msg)
    except DataValidationError as e:
        assert "score" in str(e) or "missing" in str(e).lower()


def test_espn_competition_missing_team_name() -> None:
    """Test ESPN competition without team displayName raises validation error."""
    invalid_comp = {
        "competitors": [
            {"team": {}, "score": 5},  # Missing displayName
            {"team": {"displayName": "Team B"}, "score": 3},
        ],
        "status": {},
        "date": "2024-01-01T00:00:00Z",
    }
    try:
        validate_espn_competition(invalid_comp, "MLB", "baseball")
        msg = "Should have raised DataValidationError"
        raise AssertionError(msg)
    except DataValidationError as e:
        assert "displayName" in str(e)


# ===== MLB Game Tests =====
def test_mlb_game_valid() -> None:
    """Test valid MLB game data passes validation."""
    valid_game = {
        "gameData": {
            "datetime": {"dateTime": "2024-01-01"},
            "status": {"detailedState": "In Progress"},
            "teams": {"home": {"teamName": "Yankees"}, "away": {"teamName": "Red Sox"}},
        },
        "liveData": {"plays": []},
    }
    validate_mlb_game(valid_game, "Yankees")


def test_mlb_game_missing_gamedata() -> None:
    """Test MLB game without gameData raises validation error."""
    invalid_game = {"liveData": {"plays": []}}
    try:
        validate_mlb_game(invalid_game, "Yankees")
        msg = "Should have raised DataValidationError"
        raise AssertionError(msg)
    except DataValidationError as e:
        assert "gameData" in str(e) or "missing" in str(e).lower()


def test_mlb_game_missing_teams() -> None:
    """Test MLB game without teams raises validation error."""
    invalid_game = {
        "gameData": {
            "datetime": {"dateTime": "2024-01-01"},
            "status": {"detailedState": "In Progress"},
            "teams": {},  # Missing home/away
        },
        "liveData": {"plays": []},
    }
    try:
        validate_mlb_game(invalid_game, "Yankees")
        msg = "Should have raised DataValidationError"
        raise AssertionError(msg)
    except DataValidationError as e:
        assert "teams" in str(e).lower() or "home" in str(e).lower()


# ===== NHL Boxscore Tests =====
def test_nhl_boxscore_valid() -> None:
    """Test valid NHL boxscore passes validation."""
    valid_boxscore = {
        "homeTeam": {"teamName": "Maple Leafs", "score": 5},
        "awayTeam": {"teamName": "Bruins", "score": 3},
        "gameState": "FINAL",
        "period": 3,
    }
    validate_nhl_boxscore(valid_boxscore, "Maple Leafs")


def test_nhl_boxscore_missing_score() -> None:
    """Test NHL boxscore without score raises validation error."""
    invalid_boxscore = {
        "homeTeam": {"teamName": "Maple Leafs"},  # Missing score
        "awayTeam": {"teamName": "Bruins", "score": 3},
        "gameState": "FINAL",
        "period": 3,
    }
    try:
        validate_nhl_boxscore(invalid_boxscore, "Maple Leafs")
        msg = "Should have raised DataValidationError"
        raise AssertionError(msg)
    except DataValidationError as e:
        assert "score" in str(e)


# ===== NBA Game Tests =====
def test_nba_game_valid() -> None:
    """Test valid NBA game data passes validation."""
    valid_game = {
        "gameId": "0021500001",
        "gameTimeUTC": "2024-01-01T00:00:00Z",
        "homeTeam": {"teamName": "Lakers", "score": 105},
        "awayTeam": {"teamName": "Celtics", "score": 100},
    }
    validate_nba_game(valid_game, "Lakers")


def test_nba_game_missing_team_data() -> None:
    """Test NBA game without complete team data raises validation error."""
    invalid_game = {
        "gameId": "0021500001",
        "gameTimeUTC": "2024-01-01T00:00:00Z",
        "homeTeam": {"teamName": "Lakers"},  # Missing score
        "awayTeam": {"teamName": "Celtics", "score": 100},
    }
    try:
        validate_nba_game(invalid_game, "Lakers")
        msg = "Should have raised DataValidationError"
        raise AssertionError(msg)
    except DataValidationError as e:
        assert "homeTeam" in str(e) or "score" in str(e)


# ===== MLB Schedule Tests =====
def test_mlb_schedule_valid() -> None:
    """Test valid MLB schedule passes validation."""
    valid_schedule = [
        {
            "game_id": 123456,
            "game_datetime": "2024-01-01T00:00:00Z",
            "status": "In Progress",
        },
    ]
    validate_mlb_schedule_response(valid_schedule, "Yankees")


def test_mlb_schedule_empty() -> None:
    """Test empty MLB schedule raises validation error."""
    try:
        validate_mlb_schedule_response([], "Yankees")
        msg = "Should have raised DataValidationError"
        raise AssertionError(msg)
    except DataValidationError as e:
        assert "empty" in str(e).lower() or "invalid" in str(e).lower()


def test_mlb_schedule_missing_game_id() -> None:
    """Test MLB schedule without game_id raises validation error."""
    invalid_schedule = [{"game_datetime": "2024-01-01T00:00:00Z"}]
    try:
        validate_mlb_schedule_response(invalid_schedule, "Yankees")
        msg = "Should have raised DataValidationError"
        raise AssertionError(msg)
    except DataValidationError as e:
        assert "game_id" in str(e)


# ===== Extended Validation Tests =====
def test_nba_boxscore_valid() -> None:
    """Test valid NBA boxscore passes validation."""
    valid_boxscore = {
        "game": {
            "homeTeam": {"teamName": "Lakers", "players": []},
            "awayTeam": {"teamName": "Celtics", "players": []},
        },
    }
    validate_nba_boxscore(valid_boxscore, "Lakers")


def test_nba_boxscore_missing_players() -> None:
    """Test NBA boxscore without players raises validation error."""
    invalid_boxscore = {
        "game": {
            "homeTeam": {"teamName": "Lakers"},  # Missing players
            "awayTeam": {"teamName": "Celtics", "players": []},
        },
    }
    try:
        validate_nba_boxscore(invalid_boxscore, "Lakers")
        msg = "Should have raised DataValidationError"
        raise AssertionError(msg)
    except DataValidationError as e:
        assert "players" in str(e)


def test_mlb_series_valid() -> None:
    """Test valid MLB series passes validation."""
    valid_series = {"series_status": "2-0"}
    validate_mlb_series_response(valid_series, "Yankees")


def test_mlb_series_none() -> None:
    """Test None MLB series (missing data) is allowed."""
    # Should not raise - None is acceptable for optional series data
    validate_mlb_series_response(None, "Yankees")


def test_nba_standings_valid() -> None:
    """Test valid NBA standings passes validation."""
    valid_standings = {"resultSets": [{"rowSet": []}]}
    validate_nba_standings(valid_standings, "Lakers")


def test_nba_standings_missing_results() -> None:
    """Test NBA standings without resultSets raises validation error."""
    invalid_standings = {"some_field": "value"}
    try:
        validate_nba_standings(invalid_standings, "Lakers")
        msg = "Should have raised DataValidationError"
        raise AssertionError(msg)
    except DataValidationError as e:
        assert "resultSets" in str(e)


def test_nhl_standings_valid() -> None:
    """Test valid NHL standings passes validation."""
    valid_standings = {"division": "Atlantic", "teams": []}
    validate_nhl_standings(valid_standings, "Maple Leafs")


def test_nhl_standings_not_dict() -> None:
    """Test NHL standings that is not a dict raises validation error."""
    invalid_standings = ["not", "a", "dict"]
    try:
        validate_nhl_standings(invalid_standings, "Maple Leafs")
        msg = "Should have raised DataValidationError"
        raise AssertionError(msg)
    except DataValidationError as e:
        assert "dictionary" in str(e).lower()


# ===== MLB Teams Tests =====
def test_mlb_teams_response_valid() -> None:
    """Test valid MLB teams response passes validation."""
    valid_response = {
        "teams": [
            {"clubName": "Boston Red Sox", "id": 111},
            {"clubName": "New York Yankees", "id": 147},
        ],
    }
    validate_mlb_teams_response(valid_response)


def test_mlb_teams_response_missing_teams() -> None:
    """Test MLB teams response missing teams field raises error."""
    invalid_response = {"data": []}
    try:
        validate_mlb_teams_response(invalid_response)
        msg = "Should have raised DataValidationError"
        raise AssertionError(msg)
    except DataValidationError as e:
        assert "teams" in str(e)


def test_mlb_teams_response_empty_teams() -> None:
    """Test MLB teams response with empty teams list raises error."""
    invalid_response = {"teams": []}
    try:
        validate_mlb_teams_response(invalid_response)
        msg = "Should have raised DataValidationError"
        raise AssertionError(msg)
    except DataValidationError as e:
        assert "no teams" in str(e).lower()


def test_mlb_teams_response_missing_club_name() -> None:
    """Test MLB team missing clubName raises error."""
    invalid_response = {
        "teams": [
            {"id": 111},  # missing clubName
        ],
    }
    try:
        validate_mlb_teams_response(invalid_response)
        msg = "Should have raised DataValidationError"
        raise AssertionError(msg)
    except DataValidationError as e:
        assert any("clubName" in field for field in e.missing_fields)


# ===== NHL Teams Tests =====
def test_nhl_teams_response_valid() -> None:
    """Test valid NHL teams response passes validation."""
    valid_response = [
        {"name": "Boston Bruins", "abbr": "BOS"},
        {"name": "Toronto Maple Leafs", "abbr": "TOR"},
    ]
    validate_nhl_teams_response(valid_response)


def test_nhl_teams_response_not_list() -> None:
    """Test NHL teams response that is not a list raises error."""
    invalid_response = {"teams": []}
    try:
        validate_nhl_teams_response(invalid_response)
        msg = "Should have raised DataValidationError"
        raise AssertionError(msg)
    except DataValidationError as e:
        assert "not a list" in str(e).lower()


def test_nhl_teams_response_empty() -> None:
    """Test NHL teams response with empty list raises error."""
    invalid_response = []
    try:
        validate_nhl_teams_response(invalid_response)
        msg = "Should have raised DataValidationError"
        raise AssertionError(msg)
    except DataValidationError as e:
        assert "no teams" in str(e).lower()


def test_nhl_teams_response_missing_name() -> None:
    """Test NHL team missing name raises error."""
    invalid_response = [
        {"abbr": "BOS"},  # missing name
    ]
    try:
        validate_nhl_teams_response(invalid_response)
        msg = "Should have raised DataValidationError"
        raise AssertionError(msg)
    except DataValidationError as e:
        assert any("name" in field for field in e.missing_fields)


# ===== NBA Scoreboard Games Tests =====
def test_nba_scoreboard_games_valid() -> None:
    """Test valid NBA scoreboard games passes validation."""
    valid_games = [
        {
            "homeTeam": {"teamName": "Boston Celtics", "teamTricode": "BOS"},
            "awayTeam": {"teamName": "Los Angeles Lakers", "teamTricode": "LAL"},
        },
    ]
    validate_nba_scoreboard_games(valid_games)


def test_nba_scoreboard_games_not_list() -> None:
    """Test NBA games that is not a list raises error."""
    invalid_games = {"games": []}
    try:
        validate_nba_scoreboard_games(invalid_games)
        msg = "Should have raised DataValidationError"
        raise AssertionError(msg)
    except DataValidationError as e:
        assert "not a list" in str(e).lower()


def test_nba_scoreboard_games_empty() -> None:
    """Test NBA games with empty list raises error."""
    invalid_games = []
    try:
        validate_nba_scoreboard_games(invalid_games)
        msg = "Should have raised DataValidationError"
        raise AssertionError(msg)
    except DataValidationError as e:
        assert "no games" in str(e).lower()


def test_nba_scoreboard_games_missing_team() -> None:
    """Test NBA game missing team data raises error."""
    invalid_games = [
        {
            "homeTeam": {"teamName": "Boston Celtics", "teamTricode": "BOS"},
            # missing awayTeam
        },
    ]
    try:
        validate_nba_scoreboard_games(invalid_games)
        msg = "Should have raised DataValidationError"
        raise AssertionError(msg)
    except DataValidationError as e:
        assert any("awayTeam" in field for field in e.missing_fields)


# ===== NBA Teams Tests =====
def test_nba_teams_response_valid() -> None:
    """Test valid NBA teams response passes validation."""
    valid_response = [
        {"abbreviation": "BOS", "id": 1610612738},
        {"abbreviation": "LAL", "id": 1610612747},
    ]
    validate_nba_teams_response(valid_response)


def test_nba_teams_response_not_list() -> None:
    """Test NBA teams response that is not a list raises error."""
    invalid_response = {"teams": []}
    try:
        validate_nba_teams_response(invalid_response)
        msg = "Should have raised DataValidationError"
        raise AssertionError(msg)
    except DataValidationError as e:
        assert "not a list" in str(e).lower()


def test_nba_teams_response_empty() -> None:
    """Test NBA teams response with empty list raises error."""
    invalid_response = []
    try:
        validate_nba_teams_response(invalid_response)
        msg = "Should have raised DataValidationError"
        raise AssertionError(msg)
    except DataValidationError as e:
        assert "no teams" in str(e).lower()


def test_nba_teams_response_missing_abbreviation() -> None:
    """Test NBA team missing abbreviation raises error."""
    invalid_response = [
        {"id": 1610612738},  # missing abbreviation
    ]
    try:
        validate_nba_teams_response(invalid_response)
        msg = "Should have raised DataValidationError"
        raise AssertionError(msg)
    except DataValidationError as e:
        assert any("abbreviation" in field for field in e.missing_fields)


# ===== Game Type Validators Tests =====
def test_nba_scoreboard_dict_valid() -> None:
    """Test valid NBA scoreboard dict passes validation."""
    valid_scoreboard = {
        "scoreboard": {
            "games": [{"gameLabel": "NBA Finals"}],
        },
    }
    validate_nba_scoreboard_dict(valid_scoreboard)


def test_nba_scoreboard_dict_missing_scoreboard() -> None:
    """Test NBA scoreboard dict missing scoreboard key raises error."""
    invalid_scoreboard = {"data": {}}
    try:
        validate_nba_scoreboard_dict(invalid_scoreboard)
        msg = "Should have raised DataValidationError"
        raise AssertionError(msg)
    except DataValidationError as e:
        assert any("scoreboard" in field for field in e.missing_fields)


def test_mlb_schedule_games_valid() -> None:
    """Test valid MLB schedule games passes validation."""
    valid_games = [{"game_type": "W", "game_id": 12345}]
    validate_mlb_schedule_games(valid_games, "Red Sox")


def test_mlb_schedule_games_empty() -> None:
    """Test empty MLB schedule raises error."""
    invalid_games = []
    try:
        validate_mlb_schedule_games(invalid_games, "Red Sox")
        msg = "Should have raised DataValidationError"
        raise AssertionError(msg)
    except DataValidationError as e:
        assert "no games" in str(e).lower()


def test_nhl_game_center_valid() -> None:
    """Test valid NHL game center response passes validation."""
    valid_response = {
        "seasonSeries": [
            {
                "gameType": 3,
                "awayTeam": {"abbrev": "BOS"},
                "homeTeam": {"abbrev": "TOR"},
            },
        ],
    }
    validate_nhl_game_center_response(valid_response, "Bruins")


def test_nhl_game_center_missing_season_series() -> None:
    """Test NHL game center missing seasonSeries raises error."""
    invalid_response = {"data": {}}
    try:
        validate_nhl_game_center_response(invalid_response, "Bruins")
        msg = "Should have raised DataValidationError"
        raise AssertionError(msg)
    except DataValidationError as e:
        assert any("seasonSeries" in field for field in e.missing_fields)


def test_nhl_playoff_valid() -> None:
    """Test valid NHL playoff response passes validation."""
    valid_playoff = {"currentRound": 4}
    validate_nhl_playoff_response(valid_playoff)


def test_nhl_playoff_missing_current_round() -> None:
    """Test NHL playoff missing currentRound raises error."""
    invalid_playoff = {"data": {}}
    try:
        validate_nhl_playoff_response(invalid_playoff)
        msg = "Should have raised DataValidationError"
        raise AssertionError(msg)
    except DataValidationError as e:
        assert any("currentRound" in field for field in e.missing_fields)


def test_espn_scoreboard_event_valid() -> None:
    """Test valid ESPN event passes validation."""
    valid_event = {
        "season": {"type": 3},
        "week": {"number": 4},
    }
    validate_espn_scoreboard_event(valid_event, "Patriots")


def test_espn_scoreboard_event_missing_season() -> None:
    """Test ESPN event missing season raises error."""
    invalid_event = {"data": {}}
    try:
        validate_espn_scoreboard_event(invalid_event, "Patriots")
        msg = "Should have raised DataValidationError"
        raise AssertionError(msg)
    except DataValidationError as e:
        assert any("season" in field for field in e.missing_fields)


if __name__ == "__main__":

    # ESPN Scoreboard tests
    run_test(test_espn_scoreboard_response_valid, "Valid ESPN scoreboard response")
    run_test(
        test_espn_scoreboard_response_missing_events,
        "ESPN scoreboard missing events raises error",
    )

    # ESPN Event tests
    run_test(test_espn_event_valid, "Valid ESPN event")
    run_test(
        test_espn_event_missing_competitions,
        "ESPN event missing competitions raises error",
    )

    # ESPN Competition tests
    run_test(test_espn_competition_valid, "Valid ESPN competition")
    run_test(
        test_espn_competition_missing_score,
        "ESPN competition missing score raises error",
    )
    run_test(
        test_espn_competition_missing_team_name,
        "ESPN competition missing displayName raises error",
    )

    # MLB Game tests
    run_test(test_mlb_game_valid, "Valid MLB game")
    run_test(
        test_mlb_game_missing_gamedata,
        "MLB game missing gameData raises error",
    )
    run_test(
        test_mlb_game_missing_teams,
        "MLB game missing teams raises error",
    )

    # NHL Boxscore tests
    run_test(test_nhl_boxscore_valid, "Valid NHL boxscore")
    run_test(
        test_nhl_boxscore_missing_score,
        "NHL boxscore missing score raises error",
    )

    # NBA Game tests
    run_test(test_nba_game_valid, "Valid NBA game")
    run_test(
        test_nba_game_missing_team_data,
        "NBA game missing team data raises error",
    )

    # MLB Schedule tests
    run_test(test_mlb_schedule_valid, "Valid MLB schedule")
    run_test(test_mlb_schedule_empty, "Empty MLB schedule raises error")
    run_test(
        test_mlb_schedule_missing_game_id,
        "MLB schedule missing game_id raises error",
    )

    # NBA Boxscore tests
    run_test(test_nba_boxscore_valid, "Valid NBA boxscore")
    run_test(
        test_nba_boxscore_missing_players,
        "NBA boxscore missing players raises error",
    )

    # MLB Series tests
    run_test(test_mlb_series_valid, "Valid MLB series")
    run_test(test_mlb_series_none, "MLB series None is allowed")

    # NBA Standings tests
    run_test(test_nba_standings_valid, "Valid NBA standings")
    run_test(
        test_nba_standings_missing_results,
        "NBA standings missing resultSets raises error",
    )

    # NHL Standings tests
    run_test(test_nhl_standings_valid, "Valid NHL standings")
    run_test(
        test_nhl_standings_not_dict,
        "NHL standings not dict raises error",
    )

    # MLB Teams tests
    run_test(test_mlb_teams_response_valid, "Valid MLB teams response")
    run_test(
        test_mlb_teams_response_missing_teams,
        "MLB teams response missing teams raises error",
    )
    run_test(
        test_mlb_teams_response_empty_teams,
        "MLB teams response empty raises error",
    )
    run_test(
        test_mlb_teams_response_missing_club_name,
        "MLB team missing clubName raises error",
    )

    # NHL Teams tests
    run_test(test_nhl_teams_response_valid, "Valid NHL teams response")
    run_test(
        test_nhl_teams_response_not_list,
        "NHL teams response not list raises error",
    )
    run_test(
        test_nhl_teams_response_empty,
        "NHL teams response empty raises error",
    )
    run_test(
        test_nhl_teams_response_missing_name,
        "NHL team missing name raises error",
    )

    # NBA Scoreboard Games tests
    run_test(test_nba_scoreboard_games_valid, "Valid NBA scoreboard games")
    run_test(
        test_nba_scoreboard_games_not_list,
        "NBA games not list raises error",
    )
    run_test(
        test_nba_scoreboard_games_empty,
        "NBA games empty raises error",
    )
    run_test(
        test_nba_scoreboard_games_missing_team,
        "NBA game missing team raises error",
    )

    # NBA Teams tests
    run_test(test_nba_teams_response_valid, "Valid NBA teams response")
    run_test(
        test_nba_teams_response_not_list,
        "NBA teams response not list raises error",
    )
    run_test(
        test_nba_teams_response_empty,
        "NBA teams response empty raises error",
    )
    run_test(
        test_nba_teams_response_missing_abbreviation,
        "NBA team missing abbreviation raises error",
    )

    # Game Type Validators tests
    run_test(test_nba_scoreboard_dict_valid, "Valid NBA scoreboard dict")
    run_test(
        test_nba_scoreboard_dict_missing_scoreboard,
        "NBA scoreboard dict missing scoreboard raises error",
    )
    run_test(test_mlb_schedule_games_valid, "Valid MLB schedule games")
    run_test(
        test_mlb_schedule_games_empty,
        "Empty MLB schedule raises error",
    )
    run_test(test_nhl_game_center_valid, "Valid NHL game center response")
    run_test(
        test_nhl_game_center_missing_season_series,
        "NHL game center missing seasonSeries raises error",
    )
    run_test(test_nhl_playoff_valid, "Valid NHL playoff response")
    run_test(
        test_nhl_playoff_missing_current_round,
        "NHL playoff missing currentRound raises error",
    )
    run_test(test_espn_scoreboard_event_valid, "Valid ESPN scoreboard event")
    run_test(
        test_espn_scoreboard_event_missing_season,
        "ESPN event missing season raises error",
    )

    # Print summary

    if tests_failed == 0:
        pass
    else:
        pass
