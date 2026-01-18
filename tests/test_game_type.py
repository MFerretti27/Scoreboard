#!/usr/bin/env python3
# ruff: noqa: E402
"""Test game type detection for playoffs and championships."""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from get_data.get_game_type import (
    get_game_type,
    get_mlb_game_type,
    get_nba_game_type,
    get_nfl_game_type,
    get_nhl_game_type,
)

# Test counter
tests_passed = 0
tests_failed = 0


def run_test(test_func: callable, test_name: str) -> None:
    """Run a test and track results."""
    global tests_passed, tests_failed
    try:
        test_func()
        print(f"✓ {test_name}")
        tests_passed += 1
    except AssertionError as e:
        print(f"✗ {test_name}: {e}")
        tests_failed += 1
    except Exception as e:
        print(f"✗ {test_name}: Unexpected error: {e}")
        tests_failed += 1


# ===== Game Type Router Tests =====
def test_get_game_type_mlb() -> None:
    """Test get_game_type routes to MLB function."""
    with patch("get_data.get_game_type.get_mlb_game_type", return_value="test_path"):
        result = get_game_type("MLB", "Test Team")
        assert result == "test_path"


def test_get_game_type_nhl() -> None:
    """Test get_game_type routes to NHL function."""
    with patch("get_data.get_game_type.get_nhl_game_type", return_value="test_path"):
        result = get_game_type("NHL", "Test Team")
        assert result == "test_path"


def test_get_game_type_nba() -> None:
    """Test get_game_type routes to NBA function."""
    with patch("get_data.get_game_type.get_nba_game_type", return_value="test_path"):
        result = get_game_type("NBA", "Test Team")
        assert result == "test_path"


def test_get_game_type_nfl() -> None:
    """Test get_game_type routes to NFL function."""
    with patch("get_data.get_game_type.get_nfl_game_type", return_value="test_path"):
        result = get_game_type("NFL", "Test Team")
        assert result == "test_path"


def test_get_game_type_unknown_league() -> None:
    """Test get_game_type returns empty for unknown league."""
    result = get_game_type("UNKNOWN", "Test Team")
    assert result == ""


# ===== NBA Game Type Tests =====
def test_nba_finals_detection() -> None:
    """Test NBA Finals game detection."""
    mock_scoreboard = MagicMock()
    mock_scoreboard.get_dict.return_value = {
        "scoreboard": {
            "games": [
                {
                    "gameLabel": "NBA Finals",  # Match exact string checked in code
                    "gameStatusText": "Final",
                    "awayTeam": {"teamName": "Lakers"},
                    "homeTeam": {"teamName": "Celtics"},
                },
            ],
        },
    }

    with patch("get_data.get_game_type.scoreboard.ScoreBoard", return_value=mock_scoreboard):
        result = get_nba_game_type("Lakers")
        # Should return the nba_finals.png path
        assert "nba_finals.png" in result, f"Expected NBA Finals path, got: {result}"


def test_nba_regular_season() -> None:
    """Test NBA regular season returns empty."""
    mock_scoreboard = MagicMock()
    mock_scoreboard.get_dict.return_value = {
        "scoreboard": {
            "games": [{"gameLabel": "Regular Season"}],
        },
    }

    with patch("get_data.get_game_type.scoreboard.ScoreBoard", return_value=mock_scoreboard):
        result = get_nba_game_type("Lakers")
        assert result == ""


def test_nba_validation_error_fallback() -> None:
    """Test NBA handles validation errors gracefully."""
    mock_scoreboard = MagicMock()
    mock_scoreboard.get_dict.return_value = {"invalid": "data"}

    with patch("get_data.get_game_type.scoreboard.ScoreBoard", return_value=mock_scoreboard):
        result = get_nba_game_type("Lakers")
        assert result == ""


# ===== MLB Game Type Tests =====
@patch("get_data.get_game_type.get_mlb_team_id")
@patch("get_data.get_game_type.statsapi.schedule")
def test_mlb_world_series(mock_schedule: MagicMock, mock_team_id: MagicMock) -> None:
    """Test MLB World Series detection."""
    mock_team_id.return_value = 123
    mock_schedule.return_value = [{"game_type": "W"}]

    result = get_mlb_game_type("Yankees")
    assert "world_series.png" in result


@patch("get_data.get_game_type.get_mlb_team_id")
@patch("get_data.get_game_type.statsapi.schedule")
def test_mlb_alcs(mock_schedule: MagicMock, mock_team_id: MagicMock) -> None:
    """Test MLB ALCS detection."""
    mock_team_id.return_value = 123
    mock_schedule.return_value = [{"game_type": "L"}]

    with patch("get_data.get_game_type.MLB_AL_EAST", ["Yankees"]):
        result = get_mlb_game_type("Yankees")
        assert "alcs.png" in result


@patch("get_data.get_game_type.get_mlb_team_id")
@patch("get_data.get_game_type.statsapi.schedule")
def test_mlb_nlcs(mock_schedule: MagicMock, mock_team_id: MagicMock) -> None:
    """Test MLB NLCS detection."""
    mock_team_id.return_value = 123
    mock_schedule.return_value = [{"game_type": "L"}]

    with patch("get_data.get_game_type.MLB_NL_EAST", ["Mets"]):
        result = get_mlb_game_type("Mets")
        assert "nlcs.png" in result


@patch("get_data.get_game_type.get_mlb_team_id")
@patch("get_data.get_game_type.statsapi.schedule")
def test_mlb_postseason(mock_schedule: MagicMock, mock_team_id: MagicMock) -> None:
    """Test MLB postseason detection."""
    mock_team_id.return_value = 123
    mock_schedule.return_value = [{"game_type": "F"}]

    result = get_mlb_game_type("Yankees")
    assert "mlb_postseason.png" in result


@patch("get_data.get_game_type.get_mlb_team_id")
@patch("get_data.get_game_type.statsapi.schedule")
def test_mlb_regular_season(mock_schedule: MagicMock, mock_team_id: MagicMock) -> None:
    """Test MLB regular season returns empty."""
    mock_team_id.return_value = 123
    mock_schedule.return_value = [{"game_type": "R"}]

    result = get_mlb_game_type("Yankees")
    assert result == ""


# ===== NHL Game Type Tests =====
@patch("get_data.get_game_type.get_nhl_game_id")
@patch("get_data.get_game_type.requests.get")
def test_nhl_stanley_cup(mock_get: MagicMock, mock_game_id: MagicMock) -> None:
    """Test NHL Stanley Cup detection."""
    mock_game_id.return_value = "2023020001"
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "seasonSeries": [{
            "gameType": 3,
            "awayTeam": {"abbrev": "TOR"},
            "homeTeam": {"abbrev": "MTL"},
        }],
    }
    mock_get.return_value = mock_response

    with patch("get_data.get_game_type.NHLClient") as mock_client:
        mock_client_instance = MagicMock()
        mock_client_instance.teams.teams.return_value = [
            {"name": "Toronto Maple Leafs", "abbr": "TOR", "conference": {"name": "Eastern"}},
        ]
        mock_client.return_value = mock_client_instance

        # Mock playoff response
        mock_playoff_response = MagicMock()
        mock_playoff_response.json.return_value = {"currentRound": 4}

        def get_side_effect(url: str, **kwargs: object) -> MagicMock:
            if "playoff-series" in url:
                return mock_playoff_response
            return mock_response

        mock_get.side_effect = get_side_effect

        result = get_nhl_game_type("Toronto Maple Leafs")
        assert "stanley_cup.png" in result


@patch("get_data.get_game_type.get_nhl_game_id")
@patch("get_data.get_game_type.requests.get")
def test_nhl_regular_season(mock_get: MagicMock, mock_game_id: MagicMock) -> None:
    """Test NHL regular season returns empty."""
    mock_game_id.return_value = "2023020001"
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "seasonSeries": [{
            "gameType": 2,  # Regular season
            "awayTeam": {"abbrev": "TOR"},
            "homeTeam": {"abbrev": "MTL"},
        }],
    }
    mock_get.return_value = mock_response

    result = get_nhl_game_type("Toronto Maple Leafs")
    assert result == ""


# ===== NFL Game Type Tests =====
@patch("get_data.get_game_type.requests.get")
def test_nfl_super_bowl(mock_get: MagicMock) -> None:
    """Test NFL Super Bowl detection."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "events": [{
            "name": "Patriots vs Giants",
            "season": {"type": 3},
            "week": {"number": 4},
            "notes": [{"headline": "Super Bowl LVIII"}],
        }],
    }
    mock_get.return_value = mock_response

    result = get_nfl_game_type("Patriots")
    assert "super_bowl.png" in result


@patch("get_data.get_game_type.requests.get")
def test_nfl_conference_championship(mock_get: MagicMock) -> None:
    """Test NFL conference championship detection."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "events": [{
            "name": "Patriots vs Bills",
            "season": {"type": 3},
            "week": {"number": 3},
            "notes": [{"headline": "AFC Championship"}],
        }],
    }
    mock_get.return_value = mock_response

    result = get_nfl_game_type("Patriots")
    assert "afc_championship.png" in result or "nfl_conference" in result


@patch("get_data.get_game_type.requests.get")
def test_nfl_wild_card(mock_get: MagicMock) -> None:
    """Test NFL wild card detection."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "events": [{
            "name": "Patriots vs Dolphins",
            "season": {"type": 3},
            "week": {"number": 1},
            "notes": [{"headline": "Wild Card Round"}],
        }],
    }
    mock_get.return_value = mock_response

    result = get_nfl_game_type("Patriots")
    assert "nfl_playoffs.png" in result


@patch("get_data.get_game_type.requests.get")
def test_nfl_regular_season(mock_get: MagicMock) -> None:
    """Test NFL regular season detection."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "events": [{
            "name": "Patriots vs Jets",
            "season": {"type": 2},
            "week": {"number": 5},
            "notes": [],
        }],
    }
    mock_get.return_value = mock_response

    result = get_nfl_game_type("Patriots")
    assert result == "regular-season"


@patch("get_data.get_game_type.requests.get")
def test_nfl_team_not_found(mock_get: MagicMock) -> None:
    """Test NFL when team not in scoreboard."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"events": []}
    mock_get.return_value = mock_response

    result = get_nfl_game_type("NonexistentTeam")
    assert result == ""


# ===== Error Handling Tests =====
@patch("get_data.get_game_type.get_mlb_team_id")
@patch("get_data.get_game_type.statsapi.schedule")
def test_mlb_exception_handling(mock_schedule: MagicMock, mock_team_id: MagicMock) -> None:
    """Test MLB handles exceptions gracefully."""
    mock_team_id.side_effect = Exception("API error")

    result = get_mlb_game_type("Yankees")
    assert result == ""


@patch("get_data.get_game_type.requests.get")
def test_nfl_exception_handling(mock_get: MagicMock) -> None:
    """Test NFL handles exceptions gracefully."""
    mock_get.side_effect = Exception("Network error")

    result = get_nfl_game_type("Patriots")
    assert result == ""


if __name__ == "__main__":
    print("\n=== Running Game Type Tests ===\n")

    # Router tests
    run_test(test_get_game_type_mlb, "Game type routes to MLB")
    run_test(test_get_game_type_nhl, "Game type routes to NHL")
    run_test(test_get_game_type_nba, "Game type routes to NBA")
    run_test(test_get_game_type_nfl, "Game type routes to NFL")
    run_test(test_get_game_type_unknown_league, "Game type unknown league")

    # NBA tests
    run_test(test_nba_finals_detection, "NBA Finals detection")
    run_test(test_nba_regular_season, "NBA regular season")
    run_test(test_nba_validation_error_fallback, "NBA validation error fallback")

    # MLB tests
    run_test(test_mlb_world_series, "MLB World Series")
    run_test(test_mlb_alcs, "MLB ALCS")
    run_test(test_mlb_nlcs, "MLB NLCS")
    run_test(test_mlb_postseason, "MLB postseason")
    run_test(test_mlb_regular_season, "MLB regular season")

    # NHL tests
    run_test(test_nhl_stanley_cup, "NHL Stanley Cup")
    run_test(test_nhl_regular_season, "NHL regular season")

    # NFL tests
    run_test(test_nfl_super_bowl, "NFL Super Bowl")
    run_test(test_nfl_conference_championship, "NFL conference championship")
    run_test(test_nfl_wild_card, "NFL wild card")
    run_test(test_nfl_regular_season, "NFL regular season")
    run_test(test_nfl_team_not_found, "NFL team not found")

    # Error handling
    run_test(test_mlb_exception_handling, "MLB exception handling")
    run_test(test_nfl_exception_handling, "NFL exception handling")

    print(f"\n=== Game Type Test Results ===")
    print(f"Passed: {tests_passed}")
    print(f"Failed: {tests_failed}")
    print(f"Total:  {tests_passed + tests_failed}\n")

    sys.exit(0 if tests_failed == 0 else 1)
