"""Helper function to handle errors during data fetching."""

import json
from typing import Any

import FreeSimpleGUI as Sg  # type: ignore[import]

import settings
from get_data.get_espn_data import get_data
from helper_functions.internet_connection import is_connected, reconnect
from helper_functions.logger_config import logger
from helper_functions.scoreboard_helpers import check_events, wait
from screens.clock_screen import clock


def handle_error(window: Sg.Window, *, error: Exception | None = None,
                 team_info: list[dict[str, Any]] | None = None) -> None:
    """Handle errors that occur during data fetching."""

    def _snapshot_settings() -> dict[str, str]:
        snapshot: dict[str, str] = {}
        for key, value in vars(settings).items():
            if key.startswith("__"):
                continue
            try:
                snapshot[key] = repr(value)
            except Exception:
                snapshot[key] = "<unserializable>"
        return snapshot

    time_till_clock = 0
    if is_connected():
        while time_till_clock < 12:
            try:
                event = window.read(timeout=5)
                check_events(window, event)  # Check for button presses
                for fetch_index in range(len(settings.teams)):
                    get_data(settings.teams[fetch_index])
                    logger.info("Successfully got data after error")
                    return
            except Exception as e:
                logger.info("Could not get data, trying again...")
                window["top_info"].update(value="Could not get data, trying again...", text_color="red")
                window["bottom_info"].update(value=f"Error: {e}",
                                                font=(settings.FONT, settings.NBA_TOP_INFO_SIZE), text_color="red")
            wait(window, 30) # Wait 30 seconds before trying again
            time_till_clock = time_till_clock + 1

        message = "Failed to Get Data, trying again..."
        clock(window, message)
        return

    while not is_connected():
        logger.info("Internet connection is down, trying to reconnect...")
        window["top_info"].update(value="Internet connection is down, trying to reconnect...",
                                    font=(settings.FONT, settings.NBA_TOP_INFO_SIZE), text_color="red")
        window["bottom_info"].update(value="")
        event = window.read(timeout=1000)
        check_events(window, event)  # Check for button presses
        reconnect()
        wait(window, 20) # Wait 20 seconds for connection

        if time_till_clock >= 12:  # If no connection within 4 minutes display clock
            message = "No Internet Connection"
            logger.info("\nNo Internet connection Displaying Clock\n")
            clock(window, message)
            if error is not None:
                try:
                    separator = "\n" + "=" * 80 + "\n"
                    logger.error(
                        "%sERROR DETAILS:%s\nError: %s\n\nTeam Info:\n%s\n\nSettings:\n%s\n%s",
                        separator,
                        separator,
                        error,
                        json.dumps(team_info, indent=2, default=str),
                        json.dumps(_snapshot_settings(), indent=2, default=str),
                        "=" * 80,
                        exc_info=(type(error), error, error.__traceback__),
                    )
                except Exception:
                    logger.exception("Failed to log handle_error details")
            return

        time_till_clock = time_till_clock + 1
    window.refresh()
