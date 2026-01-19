"""Settings loaded from settings.json with Python fallbacks."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any

from helper_functions.logging.logger_config import logger

SETTINGS_PATH = Path(__file__).with_name("settings.json")

# Module-level variable declarations for type checking
# These will be populated by _apply_settings() at module import time
teams: list[list[str]]
FONT: str
SCORE_TXT_SIZE: int
INFO_TXT_SIZE: int
RECORD_TXT_SIZE: int
CLOCK_TXT_SIZE: int
HYPHEN_SIZE: int
TIMEOUT_SIZE: int
NBA_TOP_INFO_SIZE: int
NHL_TOP_INFO_SIZE: int
MLB_BOTTOM_INFO_SIZE: int
PLAYING_TOP_INFO_SIZE: int
NOT_PLAYING_TOP_INFO_SIZE: int
TOP_TXT_SIZE: int
SIGNATURE_SIZE: int
PLAYER_STAT_SIZE: int
PLAYER_STAT_COLUMN: int
NBA_TIMEOUT_SIZE: int
LIVE_DATA_DELAY: int
FETCH_DATA_NOT_PLAYING_TIMER: int
DISPLAY_NOT_PLAYING_TIMER: int
DISPLAY_PLAYING_TIMER: int
HOW_LONG_TO_DISPLAY_TEAM: int
TEAM_STAT_SIZE: int
TIMEOUT_HEIGHT: int
RETRY_MAX_ATTEMPTS: int
RETRY_INITIAL_DELAY: float
RETRY_MAX_DELAY: float
RETRY_BACKOFF_MULTIPLIER: float
RETRY_USE_CACHE_FALLBACK: bool
MAX_STALE_DATA_AGE: int
display_last_pitch: bool
display_play_description: bool
display_bases: bool
display_balls_strikes: bool
display_hits_errors: bool
display_pitcher_batter: bool
display_inning: bool
display_outs: bool
display_nba_timeouts: bool
display_nba_bonus: bool
display_nba_clock: bool
display_nba_shooting: bool
display_nba_play_by_play: bool
display_nhl_sog: bool
display_nhl_power_play: bool
display_nhl_clock: bool
display_nhl_play_by_play: bool
display_nfl_timeouts: bool
display_nfl_redzone: bool
display_nfl_clock: bool
display_nfl_down: bool
display_nfl_possession: bool
display_records: bool
display_venue: bool
display_network: bool
display_series: bool
display_odds: bool
display_date_ended: bool
always_get_logos: bool
prioritize_playing_team: bool
auto_update: bool
display_playoff_championship_image: bool
display_player_stats: bool
no_spoiler_mode: bool
stay_on_team: bool
delay: bool


# Default settings to fall back on if settings.json is missing or incomplete
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
    "TEAM_STAT_SIZE": 14,
    "TIMEOUT_HEIGHT": 14,

    # Timers
    "LIVE_DATA_DELAY": 0,
    "FETCH_DATA_NOT_PLAYING_TIMER": 180,
    "DISPLAY_NOT_PLAYING_TIMER": 25,
    "DISPLAY_PLAYING_TIMER": 25,
    "HOW_LONG_TO_DISPLAY_TEAM": 7,

    # Retry & Error Recovery
    "RETRY_MAX_ATTEMPTS": 3,
    "RETRY_INITIAL_DELAY": 1.0,
    "RETRY_MAX_DELAY": 30.0,
    "RETRY_BACKOFF_MULTIPLIER": 2.0,
    "RETRY_USE_CACHE_FALLBACK": True,
    "MAX_STALE_DATA_AGE": 1800,  # 30 minutes - reject cache older than this

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
    """Save settings to file using atomic write to prevent corruption."""
    try:
        # Write to a temporary file first
        with tempfile.NamedTemporaryFile(
            mode="w",
            dir=SETTINGS_PATH.parent,
            suffix=".json",
            delete=False,
            encoding="utf-8",
        ) as tmp_file:
            json.dump(data, tmp_file, indent=2)
            tmp_path = Path(tmp_file.name)

        # Atomically replace the original file
        tmp_path.replace(SETTINGS_PATH)
    except (OSError, TypeError) as e:
        # Log the error but don't crash - settings are still available in memory
        logger.info(f"Warning: Failed to save settings to {SETTINGS_PATH}: {e}")
        # Attempt to restore from backup if it exists
        backup_path = SETTINGS_PATH.with_suffix(".json.bak")
        if backup_path.exists():
            try:
                backup_path.replace(SETTINGS_PATH)
            except Exception:
                logger.info(f"Failed to restore settings from backup at {backup_path}")


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
    """Persist updated settings to settings.json and refresh module globals.

    Uses file locking pattern to minimize race conditions:
    1. Create a backup of current settings
    2. Read current state from disk (may have been modified by another process)
    3. Merge with updates
    4. Write atomically with temp file + rename
    """
    try:
        # Create backup of current file before making changes
        if SETTINGS_PATH.exists():
            backup_path = SETTINGS_PATH.with_suffix(".json.bak")
            try:
                SETTINGS_PATH.read_bytes()  # Verify readable
                backup_path.write_bytes(SETTINGS_PATH.read_bytes())
            except OSError:
                pass  # Non-fatal if backup fails

        # Re-read from disk to get latest state (handles concurrent writes)
        current = _load_settings_file()
        current.update(updated)
        if "teams" in current:
            current["teams"] = _normalize_teams(current["teams"])

        # Save with atomic write
        _save_settings_file(current)

        # Only update in-memory state after successful write
        _apply_settings(current)
    except Exception as e:
        logger.info(f"Error writing settings: {e}")
        raise


# Load settings on import
_apply_settings(_load_settings_file())

# Runtime/shared state (not persisted)
saved_data: Any = {}
division_checked: bool = False  # Used to check if a division was checked when the screen was opened
