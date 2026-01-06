"""Settings loaded from settings.json with Python fallbacks."""
import json
from pathlib import Path
from typing import Any

SETTINGS_PATH = Path(__file__).with_name("settings.json")

DEFAULT_SETTINGS: dict[str, Any] = {
    # Teams to display
    "teams": [
        ["Detroit Lions"],
        ["Detroit Tigers"],
        ["Pittsburgh Steelers"],
        ["Detroit Pistons"],
        ["Detroit Red Wings"],
    ],

    # Text sizing
    "FONT": "Helvetica",
    "SCORE_TXT_SIZE": 150,
    "INFO_TXT_SIZE": 90,
    "RECORD_TXT_SIZE": 96,
    "CLOCK_TXT_SIZE": 204,
    "HYPHEN_SIZE": 84,
    "TIMEOUT_SIZE": 34,
    "NBA_TOP_INFO_SIZE": 56,
    "NHL_TOP_INFO_SIZE": 56,
    "MLB_BOTTOM_INFO_SIZE": 80,
    "PLAYING_TOP_INFO_SIZE": 76,
    "NOT_PLAYING_TOP_INFO_SIZE": 46,
    "TOP_TXT_SIZE": 80,
    "SIGNATURE_SIZE": 8,
    "PLAYER_STAT_SIZE": 14,
    "PLAYER_STAT_COLUMN": 30,
    "NBA_TIMEOUT_SIZE": 24,

    # Timers
    "LIVE_DATA_DELAY": 120,
    "FETCH_DATA_NOT_PLAYING_TIMER": 180,
    "DISPLAY_NOT_PLAYING_TIMER": 25,
    "DISPLAY_PLAYING_TIMER": 25,
    "HOW_LONG_TO_DISPLAY_TEAM": 7,

    # MLB
    "display_last_pitch": True,
    "display_play_description": True,
    "display_bases": True,
    "display_balls_strikes": True,
    "display_hits_errors": True,
    "display_pitcher_batter": True,
    "display_inning": True,
    "display_outs": True,

    # NBA
    "display_nba_timeouts": True,
    "display_nba_bonus": True,
    "display_nba_clock": True,
    "display_nba_shooting": True,
    "display_nba_play_by_play": True,

    # NHL
    "display_nhl_sog": True,
    "display_nhl_power_play": True,
    "display_nhl_clock": True,
    "display_nhl_play_by_play": True,

    # NFL
    "display_nfl_timeouts": True,
    "display_nfl_redzone": True,
    "display_nfl_clock": True,
    "display_nfl_down": True,
    "display_nfl_possession": True,

    # General
    "display_records": True,
    "display_venue": True,
    "display_network": True,
    "display_series": True,
    "display_odds": True,
    "display_date_ended": True,
    "always_get_logos": False,
    "prioritize_playing_team": True,
    "auto_update": True,
    "display_playoff_championship_image": True,
    "display_player_stats": True,

    # UI state flags
    "no_spoiler_mode": False,
    "stay_on_team": False,
    "delay": False,
}


def _normalize_teams(raw_teams: object) -> list[list[str]]:
    """Ensure teams are stored as list[list[str]] and escape bad shapes."""
    normalized: list[list[str]] = []
    if not isinstance(raw_teams, list):
        return DEFAULT_SETTINGS["teams"].copy()
    for entry in raw_teams:
        if isinstance(entry, list) and entry:
            normalized.append([str(entry[0])])
        elif isinstance(entry, str):
            normalized.append([entry])
    return normalized or DEFAULT_SETTINGS["teams"].copy()


def _save_settings_file(data: dict[str, Any]) -> None:
    SETTINGS_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _load_settings_file() -> dict[str, Any]:
    data = DEFAULT_SETTINGS.copy()
    changed = False

    if SETTINGS_PATH.exists():
        try:
            loaded = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                data.update(loaded)
                if "teams" in loaded:
                    data["teams"] = _normalize_teams(loaded.get("teams", []))
                for key in DEFAULT_SETTINGS:
                    if key not in loaded:
                        changed = True
            else:
                changed = True
        except json.JSONDecodeError:
            changed = True
    else:
        changed = True

    if changed:
        _save_settings_file(data)

    return data


def _apply_settings(data: dict[str, Any]) -> None:
    """Publish loaded settings as module globals for backward compatibility."""
    globals().update(data)


def read_settings() -> dict[str, Any]:
    """Return the merged settings dictionary from settings.json with defaults."""
    return _load_settings_file().copy()


def write_settings(updated: dict[str, Any]) -> None:
    """Persist updated settings to settings.json and refresh module globals."""
    current = _load_settings_file()
    current.update(updated)
    if "teams" in current:
        current["teams"] = _normalize_teams(current["teams"])
    _save_settings_file(current)
    _apply_settings(current)


# Load settings on import
_apply_settings(_load_settings_file())

# Runtime/shared state (not persisted)
saved_data: Any = {}
division_checked: bool = False  # Used to check if a division was checked when the screen was opened
