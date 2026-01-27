"""Helper function to handle errors during data fetching."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

import settings
from constants import colors, ui_keys
from get_data.get_espn_data import get_data
from helper_functions.api_utils.exceptions import NetworkError, ScoreboardError
from helper_functions.api_utils.recovery import FallbackDataProvider, RetryManager
from helper_functions.logging.logger_config import logger
from helper_functions.system.email import notify_email
from helper_functions.system.internet_connection import is_connected, reconnect
from helper_functions.ui.event_checks import check_events, wait
from screens.clock_screen import clock

if TYPE_CHECKING:
    import FreeSimpleGUI as Sg

# Global recovery utilities
_retry_manager = RetryManager()
_fallback_provider = FallbackDataProvider()
_LOGIC_ERROR_THRESHOLD = 10
_logic_error_counter = 0

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
        logger.warning(
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

def _attempt_recovery(window: Sg.Window, max_attempts: int) -> bool:
    """Attempt to recover from recoverable errors.

    :return: True if recovery succeeded, False otherwise
    """
    logger.info("Attempting data recovery with exponential backoff...")
    window[ui_keys.TOP_INFO].update(
        value="Recovering from error, retrying data fetch...",
        text_color=colors.ERROR_RED,
    )

    for attempt in range(max_attempts):
        try:
            event = window.read(timeout=5)
            check_events(window, event)

            for team in settings.teams:
                try:
                    _retry_manager.retry_with_backoff(get_data, team)
                    _fallback_provider.cache_data(team[0], {"status": "success"})
                    logger.info(f"Successfully fetched data for {team[0]} after error")
                except Exception as fetch_err:
                    logger.warning(f"Failed to fetch data for {team[0]}: {fetch_err}")
        except Exception as recovery_err:
            logger.info(f"Recovery attempt {attempt + 1} failed: {recovery_err}")
            window[ui_keys.BOTTOM_INFO].update(
                value=f"Recovery in progress... Attempt {attempt + 1}/{max_attempts}",
                font=(settings.FONT, settings.INFO_TXT_SIZE),
                text_color=colors.ERROR_RED,
            )
            wait(window, 30)
        else:
            return True

    return False

def _attempt_reconnect(window: Sg.Window, max_attempts: int) -> bool:
    """Attempt to reconnect to internet.

    :return: True if connection restored, False otherwise
    """
    logger.info("Internet connection is down, attempting to reconnect...")
    window[ui_keys.TOP_INFO].update(
        value="No internet connection. Reconnecting...",
        font=(settings.FONT, settings.NOT_PLAYING_TOP_INFO_SIZE),
        text_color=colors.ERROR_RED,
    )
    window[ui_keys.BOTTOM_INFO].update(value="")

    for _ in range(max_attempts):
        event = window.read(timeout=1000)
        check_events(window, event)
        reconnect()
        wait(window, 20)

        if is_connected():
            logger.info("Internet connection restored")
            window.refresh()
            return True

    return False

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
    global _logic_error_counter

    is_network_error = isinstance(error, NetworkError) or not is_connected()
    is_recoverable = isinstance(error, ScoreboardError) and error.recoverable if error else not is_network_error
    max_attempts = 12

    # Try to recover if connected and error is recoverable
    if is_connected() and is_recoverable:
        if _attempt_recovery(window, max_attempts):
            _logic_error_counter = 0
            return

        _log_error_details(team_info if team_info is not None else [], error)
        try:
            notify_email()
        except Exception as e:
            logger.debug(f"Failed to send error email: {e}")
        clock(window, "Failed to recover data, displaying clock")
        return

    # Handle unrecoverable logical errors
    if is_connected():
        _logic_error_counter += 1
        if _logic_error_counter >= _LOGIC_ERROR_THRESHOLD:
            _log_error_details(team_info if team_info is not None else [], error)
            logger.warning(
                "Unrecoverable error encountered (%s/%s).",
                _logic_error_counter, _LOGIC_ERROR_THRESHOLD,
            )
            _logic_error_counter = 0
            try:
                notify_email()
            except Exception as e:
                logger.debug(f"Failed to send error email: {e}")
            clock(window, "Error in scoreboard logic, please wait for update")
        return

    # Handle offline reconnection
    if not _attempt_reconnect(window, max_attempts):
        logger.error("No internet connection after extended retry period")
        _log_error_details(team_info if team_info is not None else [], error)
        try:
            notify_email()
        except Exception as e:
            logger.debug(f"Failed to send error email: {e}")
        clock(window, "No Internet Connection")
