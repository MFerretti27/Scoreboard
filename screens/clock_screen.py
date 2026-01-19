"""Display a Clock.

This screen should be displayed when:
- When Internet Connection Goes Out
- When Grabbing Data from ESPN API Fails
- Or When There is No Team Data to Display
"""
from __future__ import annotations

import time
from datetime import datetime
from typing import TYPE_CHECKING

from adafruit_ticks import ticks_add, ticks_diff, ticks_ms  # type: ignore[import]

import settings
from constants import ui_keys
from constants.file_paths import get_sport_logo_path
from get_data.get_espn_data import get_data
from get_data.get_team_logos import get_random_logo
from helper_functions.logging.logger_config import logger
from helper_functions.system.internet_connection import is_connected, reconnect
from helper_functions.system.update import check_for_update
from helper_functions.ui.event_checks import check_events, scroll
from helper_functions.ui.scoreboard_helpers import reset_window_elements, will_text_fit_on_screen

if TYPE_CHECKING:
    import FreeSimpleGUI as Sg


def error_handling(window: Sg.Window, error: Exception) -> str:
    """Handle errors when fetching data fails.

    :param window: Window Element that controls GUI
    :param error: The exception that was raised
    """
    logger.exception("Failed to Get Data")
    if is_connected():
        message = f"Failed to Get Data, Error: {error}"
    elif not is_connected():
        logger.exception("Internet connection is down, trying to reconnect...")
        message = "No Internet Connection"
        reconnect()
        time.sleep(20)  # Wait 20 seconds for connection

    # If fetching data is failing check to see if there is an update available
    _, success, latest = check_for_update()
    if success and not latest:
        bottom_message = "Update Available! Press Escape to go to main screen and update"
        window[ui_keys.BOTTOM_INFO].update(value=bottom_message, font=(settings.FONT, settings.INFO_TXT_SIZE))

    return message


def clock(window: Sg.Window, message: str) -> list:
    """If no team has any data then display clock.

    :param window: Window Element that controls GUI
    :param message: Message to display why script is showing clock

    :return team_info: List of Boolean values representing if team is has data to display
    """
    fetch_clock = ticks_ms()  # Start timer for switching display
    fetch_timer = 180 * 1000  # How often the display should update in seconds
    fetch_picture = ticks_ms()  # Start timer for switching picture
    fetch_picture_timer = 60 * 1000  # How often the picture should update in seconds
    teams_with_data: list[bool] = []
    first_time = True

    reset_window_elements(window)
    window[ui_keys.UNDER_SCORE_IMAGE].update(filename="")
    event = window.read(timeout=100)

    while True not in teams_with_data:

        # Every minute randomly select one of the users team logos to display
        if ticks_diff(ticks_ms(), fetch_picture) >= fetch_picture_timer or first_time:
            first_time = False
            files = get_random_logo()
            fetch_picture = ticks_add(fetch_picture, fetch_picture_timer)  # Reset Timer if picture updated

        # Get the current time and display it
        current_time = datetime.now()
        hour = current_time.hour if current_time.hour < 13 else current_time.hour - 12
        minute = current_time.minute if current_time.minute > 9 else f"0{current_time.minute}"

        date = str(current_time.month) + "/" + str(current_time.day) + "/" + str(current_time.year)
        window[ui_keys.HYPHEN].update(value=":", font=(settings.FONT, settings.SCORE_TXT_SIZE))
        window[ui_keys.HOME_SCORE].update(value=minute, font=(settings.FONT, settings.CLOCK_TXT_SIZE))
        window[ui_keys.AWAY_SCORE].update(value=hour, font=(settings.FONT, settings.CLOCK_TXT_SIZE))
        window[ui_keys.AWAY_LOGO].update(filename=get_sport_logo_path(files[0][0], files[0][1]))
        window[ui_keys.HOME_LOGO].update(filename=get_sport_logo_path(files[1][0], files[1][1]))
        window[ui_keys.BOTTOM_INFO].update(value=date, font=(settings.FONT, settings.RECORD_TXT_SIZE))
        window[ui_keys.TOP_INFO].update(value=message, font=(settings.FONT, settings.TIMEOUT_SIZE))

        should_scroll = will_text_fit_on_screen(message, txt_size=settings.TIMEOUT_SIZE)
        if should_scroll:
            scroll(window, message, key=ui_keys.TOP_INFO)

        check_events(window, event)

        # Fetch to see if any teams have data and return to main loop displaying team info
        try:
            if ticks_diff(ticks_ms(), fetch_clock) >= fetch_timer:
                teams_with_data.clear()
                for fetch_index in range(len(settings.teams)):
                    logger.info("\nFetching data for %s", settings.teams[fetch_index][0])
                    data = get_data(settings.teams[fetch_index])
                    teams_with_data.append(data[1])
                    message = "No Data For Any Teams"

                fetch_clock = ticks_add(fetch_clock, fetch_timer)  # Reset Timer if fetch attempted

        # If fetched failed find out why and display message
        except Exception as error:
            message = error_handling(window, error)

        event = window.read(timeout=100)

    # Reset Text Font Size before returning to main loop
    reset_window_elements(window)
    return teams_with_data
