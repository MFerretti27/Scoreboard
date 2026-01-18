"""Helper function to handle errors during data fetching."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

import settings
from constants import colors, ui_keys
from get_data.get_espn_data import get_data
from helper_functions.exceptions import NetworkError, ScoreboardError
from helper_functions.internet_connection import is_connected, reconnect
from helper_functions.logger_config import logger
from helper_functions.recovery import FallbackDataProvider, RetryManager
from helper_functions.scoreboard_helpers import check_events, wait
from screens.clock_screen import clock

if TYPE_CHECKING:
    import FreeSimpleGUI as Sg

# Global recovery utilities
_retry_manager = RetryManager()
_fallback_provider = FallbackDataProvider()

def _snapshot_settings() -> dict[str, str]:
    """Capture current settings state for error logging.

    :return: Dictionary of settings with string representations
    """
    snapshot: dict[str, str] = {}
    for key, value in vars(settings).items():
        if key.startswith("__"):
            continue
        try:
            snapshot[key] = repr(value)
        except Exception:
            snapshot[key] = "<unserializable>"
    return snapshot

def _log_error_details(team_info: list[dict[str, Any]], exc: Exception | None = None) -> None:
    """Log comprehensive error details for debugging.

    :param exc: Exception to log details for
    """
    if exc is None:
        return

    try:
        separator = "\n" + "=" * 80 + "\n"
        error_type = type(exc).__name__
        logger.error(
            "%sERROR DETAILS:%s\nType: %s\nMessage: %s\n\nTeam Info:\n%s\n\nSettings:\n%s\n%s",
            separator,
            separator,
            error_type,
            str(exc),
            json.dumps(team_info, indent=2, default=str) if team_info else "N/A",
            json.dumps(_snapshot_settings(), indent=2, default=str),
            "=" * 80,
            exc_info=(type(exc), exc, exc.__traceback__) if isinstance(exc, ScoreboardError) else None,
        )
    except Exception as log_err:
        logger.exception(f"Failed to log error details: {log_err}")

def handle_error(
    window: Sg.Window,
    *,
    error: Exception | None = None,
    team_info: list[dict[str, Any]] | None = None,
) -> None:
    """Handle errors that occur during data fetching using recovery strategies.

    Attempts to recover from errors with exponential backoff and fallback mechanisms.
    Logs detailed error information for debugging.

    :param window: FreeSimpleGUI window for status updates
    :param error: The exception that occurred
    :param team_info: Current team information for error context
    """
    # Classify error and determine if it's recoverable
    is_network_error = isinstance(error, NetworkError) or not is_connected()
    is_recoverable = isinstance(error, ScoreboardError) and error.recoverable if error else not is_network_error

    # Log the error for diagnostics
    if error:
        _log_error_details(team_info,error)

    time_till_clock = 0
    max_recovery_attempts = 12  # ~6 minutes with 30-second intervals

    # Try to recover if we have network connectivity and error is recoverable
    if is_connected() and is_recoverable:
        logger.info("Attempting data recovery with exponential backoff...")
        window[ui_keys.TOP_INFO].update(
            value="Recovering from error, retrying data fetch...",
            text_color=colors.RED,
        )

        while time_till_clock < max_recovery_attempts:
            try:
                event = window.read(timeout=5)
                check_events(window, event)  # Check for button presses

                # Attempt to fetch data for all teams with retry logic
                for _, team in enumerate(settings.teams):
                    try:
                        _retry_manager.retry_with_backoff(get_data, team, {})
                        # Cache successful data for fallback
                        _fallback_provider.cache_data(team[0], {"status": "success"})
                        logger.info(f"Successfully fetched data for {team[0]} after error")
                    except Exception as fetch_err:
                        logger.warning(f"Failed to fetch data for {team[0]}: {fetch_err}")
                        # Don't fail completely - move to next team

            except Exception as recovery_err:
                logger.info(f"Recovery attempt {time_till_clock + 1} failed: {recovery_err}")
                window[ui_keys.BOTTOM_INFO].update(
                    value=f"Recovery in progress... Attempt {time_till_clock + 1}/{max_recovery_attempts}",
                    font=(settings.FONT, settings.INFO_TXT_SIZE),
                    text_color=colors.RED,
                )
            else:
                logger.info("Successfully recovered from error")
                return

            wait(window, 30)  # Wait 30 seconds before retrying
            time_till_clock += 1

        logger.error("Data recovery failed, displaying fallback clock")
        message = "Failed to recover data, displaying clock"
        clock(window, message)
        return

    # Handle network connectivity issues
    logger.info("Internet connection issue detected, attempting reconnection...")
    time_till_clock = 0

    while not is_connected():
        logger.info("Internet connection is down, attempting to reconnect...")
        window[ui_keys.TOP_INFO].update(
            value="No internet connection. Reconnecting...",
            font=(settings.FONT, settings.NOT_PLAYING_TOP_INFO_SIZE),
            text_color=colors.RED,
        )
        window[ui_keys.BOTTOM_INFO].update(value="")

        event = window.read(timeout=1000)
        check_events(window, event)  # Check for button presses

        reconnect()
        wait(window, 20)  # Wait 20 seconds for connection to establish

        if time_till_clock >= max_recovery_attempts:
            # Extended offline - display clock with error message
            logger.error("No internet connection after extended retry period")
            message = "No Internet Connection"
            _log_error_details(team_info, error)
            clock(window, message)
            return

        time_till_clock += 1

    logger.info("Internet connection restored")
    window.refresh()
