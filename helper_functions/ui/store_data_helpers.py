"""Helpers for background fetch and scoreboard logic."""
from dataclasses import dataclass
from datetime import datetime, timedelta

from adafruit_ticks import ticks_ms  # type: ignore[import]

import settings
from helper_functions.logging.logger_config import logger

MILLISECONDS_PER_SECOND = 1000

@dataclass
class DisplayState:
    """Tracks the state and timing for scoreboard display updates and fetch cycles.

    Attributes:
        display_index (int): Current index of the team being displayed.
        display_clock (int): Timestamp of the last display update.
        update_clock (int): Timestamp of the last data update.
        fetch_clock (int): Timestamp of the last data fetch.
        delay_clock (int): Timestamp when delay started.
        display_first_time (bool): Flag for first display cycle.
        fetch_first_time (bool): Flag for first fetch cycle.
        delay_over (bool): Whether the delay period has ended.
        delay_started (bool): Whether the delay has started.
        original_index (int): The original team index before any changes.

    """

    display_index: int = 0
    display_clock: int = 0
    update_clock: int = 0
    fetch_clock: int = 0
    delay_clock: int = 0
    display_first_time: bool = True
    fetch_first_time: bool = True
    delay_over: bool = False
    delay_started: bool = False
    original_index: int = 0

    def __post_init__(self) -> None:
        """Initialize all clock attributes to the current tick count."""
        current_time = ticks_ms()
        self.display_clock = current_time
        self.update_clock = current_time
        self.fetch_clock = current_time
        self.delay_clock = current_time

def save_team_data(
    info: dict, fetch_index: int, teams_with_data: list[bool],
) -> tuple[dict, list[bool]]:
    """Save or retrieve team data for display, handling final states and display duration.

    params info: The team information dictionary.
    fetch_index: Index of the team in the settings.teams list.
    teams_with_data: List indicating which teams currently have data available.

    return: Updated team info and teams_with_data list.
    """
    team_name = settings.teams[fetch_index][0]
    is_team_saved = team_name in settings.saved_data
    has_data = teams_with_data[fetch_index]
    is_final = "FINAL" in info.get("bottom_info", "")

    if has_data and is_final and not is_team_saved:
        if settings.display_date_ended:
            info["bottom_info"] += "   " + datetime.now().strftime("%-m/%-d/%y")
        settings.saved_data[team_name] = [info, datetime.now()]
        logger.info("Saving Data to display longer than it's available")
        return info, teams_with_data
    if is_team_saved and has_data and is_final:
        info["bottom_info"] = settings.saved_data[team_name][0]["bottom_info"]
        return info, teams_with_data
    if is_team_saved and not has_data:
        logger.info("Data is no longer available, checking if should display")
        current_date = datetime.now()
        saved_date = settings.saved_data[team_name][1]
        saved_datetime = datetime.fromisoformat(saved_date) if isinstance(saved_date, str) else saved_date
        date_difference = current_date - saved_datetime
        if date_difference <= timedelta(days=settings.HOW_LONG_TO_DISPLAY_TEAM):
            logger.info(f"It will display, time its been: {date_difference}")
            info = settings.saved_data[team_name][0]
            teams_with_data[fetch_index] = True
            return info, teams_with_data
        del settings.saved_data[team_name]
    return info, teams_with_data
