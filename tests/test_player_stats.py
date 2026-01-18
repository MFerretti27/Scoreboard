"""Unit tests for player stats fetchers with mocked network calls."""
from __future__ import annotations

from unittest.mock import patch

from get_data.get_player_stats import (
    get_mlb_player_stats,
    get_nba_player_stats,
    get_nfl_player_stats,
    get_nhl_player_stats,
)


class DummyResponse:
    """Simple response stub returning preset JSON payload."""

    def __init__(self, payload) -> None:
        self._payload = payload

    def json(self):
        return self._payload


def test_get_nba_player_stats_returns_strings() -> None:
    fake_scoreboard = {
        "scoreboard": {
            "games": [
                {
                    "homeTeam": {"teamName": "Lakers"},
                    "awayTeam": {"teamName": "Warriors"},
                    "gameId": "1234",
                },
            ],
        },
    }

    fake_boxscore = {
        "game": {
            "homeTeam": {
                "players": [
                    {
                        "position": "G",
                        "name": "Home Player",
                        "statistics": {
                            "fieldGoalsMade": 4,
                            "threePointersMade": 2,
                            "freeThrowsMade": 1,
                            "blocks": 1,
                            "steals": 2,
                            "assists": 3,
                        },
                        "starter": "1",
                        "status": "ACTIVE",
                        "played": "1",
                        "order": 1,
                    },
                ],
            },
            "awayTeam": {
                "players": [
                    {
                        "position": "F",
                        "name": "Away Player",
                        "statistics": {
                            "fieldGoalsMade": 5,
                            "threePointersMade": 1,
                            "freeThrowsMade": 2,
                            "blocks": 0,
                            "steals": 1,
                            "assists": 4,
                        },
                        "starter": "1",
                        "status": "ACTIVE",
                        "played": "1",
                        "order": 1,
                    },
                ],
            },
        },
    }

    with (
        patch("get_data.get_player_stats.scoreboard.ScoreBoard") as mock_sb,
        patch("get_data.get_player_stats.boxscore.BoxScore") as mock_box,
        patch("get_data.get_player_stats.validate_nba_boxscore") as mock_validate,
    ):
        mock_sb.return_value.get_dict.return_value = fake_scoreboard
        mock_box.return_value.get_dict.return_value = fake_boxscore
        mock_validate.return_value = None

        home_stats, away_stats = get_nba_player_stats("Lakers")

    assert "Players Stats" in home_stats
    assert "Players Stats" in away_stats


def test_get_nhl_player_stats_returns_strings() -> None:
    fake_boxscore = {
        "awayTeam": {"commonName": {"default": "Canadiens"}},
        "homeTeam": {"commonName": {"default": "Bruins"}},
        "playerByGameStats": {
            "homeTeam": {
                "forwards": [
                    {
                        "name": {"default": "Home Center"},
                        "position": "C",
                        "goals": 1,
                        "assists": 0,
                        "sog": 3,
                        "toi": "10:00",
                    },
                ],
                "defense": [
                    {
                        "name": {"default": "Home Defense"},
                        "position": "D",
                        "goals": 0,
                        "assists": 1,
                        "sog": 2,
                        "toi": "12:00",
                    },
                ],
            },
            "awayTeam": {
                "forwards": [
                    {
                        "name": {"default": "Away Center"},
                        "position": "C",
                        "goals": 2,
                        "assists": 1,
                        "sog": 4,
                        "toi": "11:00",
                    },
                ],
                "defense": [
                    {
                        "name": {"default": "Away Defense"},
                        "position": "D",
                        "goals": 0,
                        "assists": 2,
                        "sog": 1,
                        "toi": "13:00",
                    },
                ],
            },
        },
    }

    with (
        patch("get_data.get_player_stats.get_nhl_game_id", return_value=111),
        patch("get_data.get_player_stats.requests.get", return_value=DummyResponse(fake_boxscore)),
    ):
        home_stats, away_stats = get_nhl_player_stats("Bruins")

    assert "Players Stats" in home_stats
    assert "Players Stats" in away_stats


def test_get_mlb_player_stats_returns_strings() -> None:
    fake_live = {
        "liveData": {
            "boxscore": {
                "teams": {
                    "home": {
                        "players": {
                            "ID1": {
                                "person": {"fullName": "Home Batter"},
                                "position": {"abbreviation": "C"},
                                "stats": {"batting": {"rbi": 1, "hits": 2, "atBats": 4}},
                                "seasonStats": {"batting": {"avg": ".250"}},
                            },
                        },
                        "battingOrder": [1],
                    },
                    "away": {
                        "players": {
                            "ID2": {
                                "person": {"fullName": "Away Batter"},
                                "position": {"abbreviation": "1B"},
                                "stats": {"batting": {"rbi": 0, "hits": 1, "atBats": 3}},
                                "seasonStats": {"batting": {"avg": ".300"}},
                            },
                        },
                        "battingOrder": [2],
                    },
                },
            },
            "plays": {
                "allPlays": [
                    {
                        "matchup": {"batter": {"id": 1}},
                        "result": {"event": "Single", "description": "Single"},
                    },
                    {
                        "matchup": {"batter": {"id": 2}},
                        "result": {"event": "Walk", "description": "Walk"},
                    },
                ],
            },
        },
    }

    with (
        patch("get_data.get_player_stats.get_mlb_team_id", return_value=1),
        patch("get_data.get_player_stats.statsapi.schedule", return_value=[1]),
        patch("get_data.get_player_stats.statsapi.get", return_value=[{"game_id": 999}]),
        patch("get_data.get_player_stats.requests.get", return_value=DummyResponse(fake_live)),
    ):
        home_stats, away_stats = get_mlb_player_stats("Yankees")

    assert "AVG" in home_stats or "AVG" in away_stats


def test_get_nfl_player_stats_returns_strings() -> None:
    fake_scoreboard = {
        "events": [
            {
                "name": "Detroit Lions vs Chicago Bears",
                "competitions": [
                    {
                        "leaders": [
                            {"leaders": [{"displayValue": "10-12", "athlete": {"shortName": "J Smith"}}]},
                            {"leaders": [{"displayValue": "5-50", "athlete": {"shortName": "R Johnson"}}]},
                            {"leaders": [{"displayValue": "3-30", "athlete": {"shortName": "W Brown"}}]},
                        ],
                    },
                ],
            },
        ],
    }

    with patch("get_data.get_player_stats.requests.get", return_value=DummyResponse(fake_scoreboard)):
        _home_stats, away_stats = get_nfl_player_stats("Lions")

    assert "Passing Leader" in away_stats
    assert "Rushing Leader" in away_stats
    assert "Receiving Leader" in away_stats
