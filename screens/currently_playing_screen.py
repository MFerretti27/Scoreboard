"""Module to display live information when team is currently playing."""
import copy
import time

import FreeSimpleGUI as sg  # type: ignore[import]
from adafruit_ticks import ticks_add, ticks_diff, ticks_ms  # type: ignore[import]

import settings
from get_data.get_espn_data import get_data
from helper_functions.logger_config import logger
from helper_functions.scoreboard_helpers import (
    check_events,
    reset_window_elements,
    scroll,
    set_spoiler_mode,
    will_text_fit_on_screen,
)


def set_delay_display(team_info: list, teams_with_data: list,
                      teams_currently_playing: list, display_index: int) -> list:
    """Set the display to hide information until delay is over.

    :param team_info: Dictionary containing information about the teams
    :param teams_with_data: List of teams that have data available
    :param teams_currently_playing: List of teams that are currently playing
    :param display_index: Index of the team to display

    :return: Updated team_info dictionary hiding team display information
    """
    for index in range(len(settings.teams)):
        if teams_with_data[index] and teams_currently_playing[index]:
            team_info[index]["top_info"] = "Game Started"
            team_info[index]["bottom_info"] = f"Setting delay of {settings.LIVE_DATA_DELAY} seconds"
            team_info[index]["home_timeouts"] = ""
            team_info[index]["away_timeouts"] = ""
            team_info[index]["home_score"] = "0"
            team_info[index]["away_score"] = "0"
            if "@" not in team_info[index]["above_score_txt"]:  # Remove if text doesn't have team names
                team_info[index]["above_score_txt"] = ""
            team_info[index]["under_score_image"] = ""

            # Ensure score color doesn't display in delay
            if ("home_possession" in team_info and "away_possession" in team_info
                and "home_redzone" in team_info and "away_redzone" in team_info):
                team_info[display_index]["home_redzone"] = False
                team_info[display_index]["away_redzone"] = False
                team_info[display_index]["home_possession"] = False
                team_info[display_index]["away_possession"] = False
            elif "home_bonus" in team_info and "away_bonus" in team_info:
                team_info[display_index]["home_bonus"] = False
                team_info[display_index]["away_bonus"] = False
            elif "home_power_play" in team_info and "away_power_play" in team_info:
                team_info[display_index]["home_power_play"] = False
                team_info[display_index]["away_power_play"] = False

    return team_info

def display_nfl_info(window: sg.Window, team_info: dict, key: str, value: str) -> None:
    """Update the NFL display information for a specific team.

    :param window: The window element to update
    :param team_info: The team information dictionary
    :param key: The key to update
    :param value: The new value to set
    :param display_index: The index of the team to update

    :return: None
    """
    if key == "top_info":
        window["top_info"].update(value=value, font=(settings.FONT, settings.MLB_BOTTOM_INFO_SIZE))
    if key == "home_timeouts":
        window["home_timeouts"].update(value=value, text_color="yellow")
    elif key == "away_timeouts":
        window["away_timeouts"].update(value=value, text_color="yellow")

    if team_info["home_possession"] and key == "home_score":
        window["home_score"].update(value=value, font=(settings.FONT,
                                                        settings.SCORE_TXT_SIZE, "underline"))
    elif team_info["away_possession"] and key == "away_score":
        window["away_score"].update(value=value, font=(settings.FONT,
                                                        settings.SCORE_TXT_SIZE, "underline"))
    if team_info["home_redzone"] and key == "home_score":
        window["home_score"].update(value=value,
                                    font=(settings.FONT, settings.SCORE_TXT_SIZE, "underline"),
                                    text_color="red")
    elif team_info["away_redzone"] and key == "away_score":
        window["away_score"].update(value=value,
                                    font=(settings.FONT, settings.SCORE_TXT_SIZE, "underline"),
                                    text_color="red")

def display_nba_info(window: sg.Window, team_info: dict, key: str, value: str) -> None:
    """Update the NBA display information for a specific team.

    :param window: The window element to update
    :param team_info: The team information dictionary
    :param key: The key to update
    :param value: The new value to set
    :param display_index: The index of the team to update

    :return: None
    """
    if key == "above_score_txt" and settings.display_nba_play_by_play:
        window[key].update(value=value, font=(settings.FONT, settings.TOP_TXT_SIZE))
    if key == "top_info":
        window["top_info"].update(value=value, font=(settings.FONT, settings.NBA_TOP_INFO_SIZE))
    elif key == "home_timeouts":
        window["home_timeouts"].update(value=value, font=(settings.FONT, settings.TIMEOUT_SIZE - 10),
                                        text_color="yellow")
    elif key == "away_timeouts":
        window["away_timeouts"].update(value=value, font=(settings.FONT, settings.TIMEOUT_SIZE - 10),
                                        text_color="yellow")

    # Ensure bonus is in dictionary to not cause key error
    if "home_bonus" in team_info or "away_bonus" in team_info:
        if team_info["home_bonus"] and key == "home_score":
            window[key].update(value=value, text_color="orange")
        if team_info["away_bonus"] and key == "away_score":
            window[key].update(value=value, text_color="orange")

def display_mlb_info(window: sg.Window, key: str, value: str) -> None:
    """Update the MLB display information for a specific team.

    :param window: The window element to update
    :param key: The key to update
    :param value: The new value to set

    :return: None
    """
    if key == "top_info":
        window["top_info"].update(value=value, font=(settings.FONT, settings.MLB_BOTTOM_INFO_SIZE))
    if key == "bottom_info":
        window[key].update(value=value, font=(settings.FONT, settings.MLB_BOTTOM_INFO_SIZE))
    elif key == "under_score_image":
        window[key].update(filename=value)
    elif key == "above_score_txt" and settings.display_inning:
        window[key].update(value=value, font=(settings.FONT, settings.TOP_TXT_SIZE))

def display_nhl_info(window: sg.Window, team_info: dict, key: str, value: str) -> None:
    """Update the NHL display information for a specific team.

    :param window: The window element to update
    :param team_info: The team information dictionary
    :param key: The key to update
    :param value: The new value to set

    :return: None
    """
    if key == "top_info":
        window[key].update(value=value, font=(settings.FONT, settings.NBA_TOP_INFO_SIZE))
    if key == "above_score_txt" and settings.display_nhl_play_by_play:
        window[key].update(value=value, font=(settings.FONT, settings.TOP_TXT_SIZE))

    # Ensure power play is in dictionary to not cause key error
    if "home_power_play" in team_info or "away_power_play" in team_info:
        if team_info["home_power_play"] and key == "home_score":
            window["home_score"].update(value=value, font=(settings.FONT, settings.SCORE_TXT_SIZE),
                                        text_color="blue")
        elif team_info["away_power_play"] and key == "away_score":
            window["away_score"].update(value=value, font=(settings.FONT, settings.SCORE_TXT_SIZE),
                                        text_color="blue")

def update_display(window: sg.Window, team_info: dict, display_index: int, teams_currently_playing: list[bool]) -> None:
    """Update the display for a specific team.

    :param window: The window element to update
    :param team_info: The team information dictionary
    :param display_index: The index of the team to update

    :return: None
    """
    sport_league = settings.teams[display_index][1]
    for key, value in team_info[display_index].items():
        if "home_logo" in key or "away_logo" in key or "under_score_image" in key:
            window[key].update(filename=value)
        elif key == "signature":
            window[key].update(value=value, text_color="red")
        elif ("possession" not in key and "redzone" not in key and "bonus" not in key and
                "power_play" not in key):
            window[key].update(value=value)

        # Football specific display information
        if "NFL" in sport_league.upper() and teams_currently_playing[display_index]:
            display_nfl_info(window, team_info[display_index], key, value)

        # NBA Specific display size for top info
        if "NBA" in sport_league.upper() and teams_currently_playing[display_index]:
            display_nba_info(window, team_info[display_index], key, value)

        # MLB Specific display size for bottom info
        if "MLB" in sport_league.upper() and teams_currently_playing[display_index]:
            display_mlb_info(window, key, value)

        # NHL Specific display size for bottom info
        if "NHL" in sport_league.upper() and teams_currently_playing[display_index]:
            display_nhl_info(window, team_info[display_index], key, value)

        if settings.no_spoiler_mode:
            set_spoiler_mode(window, team_info[display_index])

def find_next_team_to_display(teams: list[list], teams_currently_playing: list[bool],
                              display_index: int, teams_with_data: list[bool]) -> tuple[int, int]:
    """Find the next team to display.

    :param teams: List of teams to display
    :param teams_currently_playing: List of currently playing teams
    :param display_index: Index of the team to display
    :param teams_with_data: List of teams with data

    :return: Index of the next team to display
    """
    original_index : int = display_index
    # Find next team to display (skip teams not playing)
    # If shift pressed, stay on current team playing
    if not settings.stay_on_team and settings.prioritize_playing_team:
        for x in range(len(teams) * 2):
            if teams_currently_playing[(original_index + x) % len(teams)] is False:
                display_index = (display_index + 1) % len(teams)
                logger.info(f"skipping displaying {teams[(original_index + x) % len(teams)][0]}")
            elif teams_currently_playing[(original_index + x) % len(teams)] is True and x != 0:
                logger.info(
                    f"Found next team currently playing {teams[(original_index + x) % len(teams)][0]}\n")
                break
    elif not settings.stay_on_team and not settings.prioritize_playing_team:
        for x in range(len(teams) * 2):
            if teams_with_data[(original_index + x) % len(teams)] is False:
                display_index = (display_index + 1) % len(teams)
                logger.info(f"skipping displaying {teams[(original_index + x) % len(teams)][0]}")
            elif teams_with_data[(original_index + x) % len(teams)] is True and x != 0:
                logger.info(
                    f"Found next team that has data {teams[(original_index + x) % len(teams)][0]}\n")
                break
    else:
        logger.info(
            f"Not Switching teams that are currently playing, staying on {teams[display_index][0]}\n")

    display_index = (display_index + 1) % len(teams)

    if settings.stay_on_team:
        display_index = original_index

    return display_index, original_index

def get_display_data(display_index: int, delay_started: list[bool],
                     delay_clock: list[dict], fetch_clock: list[dict], delay_over: dict[str, bool]) -> tuple:
    """Fetch and update display data for teams.

    :param display_index: Index of the team to display
    :param delay_started: List indicating if delays have started for each team
    :param delay_clock: List of dictionaries containing delay clocks for each team
    :param fetch_clock: List of dictionaries containing fetch clocks for each team
    :param delay_over: List indicating if delays are over for each team

    :return: None
    """
    teams_with_data = []
    team_info = []
    teams_currently_playing = []
    saved_data = []
    delay_info = []
    fetch_timer = 2 * 1000  # How often to fetch data in seconds
    delay_timer = settings.LIVE_DATA_DELAY * 1000  # How long till information is displayed
    for fetch_index in range(len(settings.teams)):
        logger.info(f"\nFetching data for {settings.teams[fetch_index][0]}")
        info, data, currently_playing = get_data(settings.teams[fetch_index])
        teams_with_data.append(data)
        teams_currently_playing.append(currently_playing)

        if settings.delay:
            # Wait for delay to be over to start displaying data
            if ticks_diff(ticks_ms(), delay_clock[fetch_index]) >= delay_timer and delay_started[fetch_index]:
                delay_over[settings.teams[fetch_index][0]] = True
            elif currently_playing and not delay_started[fetch_index]:
                    logger.info("Setting delay")
                    delay_started[fetch_index] = True
                    delay_clock[fetch_index] = ticks_ms()

        # If delay don't keep updating as to not display latest data
        if not settings.delay:
            team_info.append(info)
        else:
            delay_info.append(info)

    # if there is a delay save data for after delay
    if settings.delay:
        last_info = copy.deepcopy(delay_info)
        delay_info.clear()
        saved_data.append(copy.deepcopy(last_info))  # Save last_info

        if delay_over[settings.teams[display_index][0]]:  # If delay over start displaying delayed info in order
            team_info = copy.deepcopy(saved_data.pop(0))  # get the first thing saved and remove it

            # Ensure currently_playing is true until delay catches up
            for index, team_info_temp in enumerate(team_info):
                if ("bottom_info" in team_info_temp and teams_with_data[index] and
                    not any(keyword in str(team_info_temp["bottom_info"]).lower()
                        for keyword in ["delayed", "postponed", "final", "canceled", "delay", "am", "pm"])):
                    teams_currently_playing[index] = True
        else:
            team_info = copy.deepcopy(last_info)  # if delay is not over continue displaying last thing
            team_info = set_delay_display(team_info, teams_with_data, teams_currently_playing, display_index)

    fetch_clock = ticks_add(fetch_clock, fetch_timer)  # Reset Timer

    return teams_with_data, team_info, teams_currently_playing, delay_clock, fetch_clock, delay_over


def team_currently_playing(window: sg.Window, teams: list[list]) -> list:
    """Display only games that are currently playing.

    :param window: Window Element that controls GUI
    :param teams: List containing lists of teams to display data for

    :return team_info: List of information for teams following
    """
    teams_currently_playing: list[bool] = []
    first_time: bool = True
    delay_over: dict[str, bool] = {}
    team_info: list[dict] = []
    teams_with_data: list[bool] = []
    delay_started: list[bool] = []
    display_index: int = 0
    should_scroll: bool = False
    currently_displaying: dict = {}

    display_clock: int = ticks_ms()  # Start timer for switching display
    display_timer: int = settings.DISPLAY_PLAYING_TIMER * 1000  # How often the display should update in seconds
    fetch_clock: int = ticks_ms()  # Start timer for fetching
    fetch_timer: int = 2 * 1000  # How often to fetch data in seconds
    delay_clock: list[int] = []  # Start timer how long to start displaying information

    for team in settings.teams:
        delay_over[team[0]] = False
        delay_clock.append(0)
        delay_started.append(False)

    while True in teams_currently_playing or first_time:
        if ticks_diff(ticks_ms(), fetch_clock) >= fetch_timer or first_time:
            (teams_with_data, team_info, teams_currently_playing,
             delay_clock, fetch_clock, delay_over) = get_display_data(display_index, delay_started,
                                                                      delay_clock, fetch_clock, delay_over)

        if teams_with_data[display_index] and (teams_currently_playing[display_index] or
                                               not settings.prioritize_playing_team):
            logger.info(f"\n{teams[display_index][0]} is currently playing, updating display")

            # Reset text color, underline and timeouts, for new display
            reset_window_elements(window)

            # Check if bottom text fits on screen
            should_scroll = will_text_fit_on_screen(team_info[display_index]["bottom_info"])

            # Update the display with the current team information
            update_display(window, team_info, display_index, teams_currently_playing)

            currently_displaying = team_info[display_index]
            event = window.read(timeout=5000)

        # Find Next team to display
        if ((ticks_diff(ticks_ms(), display_clock) >= display_timer or first_time) and
            (teams_currently_playing[display_index] or (teams_with_data[display_index] and
                                                          not settings.prioritize_playing_team))):
            first_time = False
            display_index, original_index = find_next_team_to_display(teams, teams_currently_playing,
                                                                        display_index, teams_with_data)
            display_clock = ticks_add(display_clock, display_timer)  # Reset Timer

        else:
            display_index = (display_index + 1) % len(teams)

        if should_scroll and not settings.no_spoiler_mode and currently_displaying == team_info[display_index]:
            scroll(window, team_info, display_index)
            should_scroll = False

        temp_delay = settings.delay  # store to see if changed
        if not first_time:
            check_events(window, event, currently_playing=True)
        if settings.stay_on_team and sum(teams_currently_playing) == 1:
            window["top_info"].update(value='No longer set to "staying on team"')
            window["bottom_info"].update(value="Only one team playing")
            window.read(timeout=2000)
            time.sleep(5)
            settings.stay_on_team = False

        if temp_delay is not settings.delay:
            delay_clock = ticks_ms()
            delay_over[teams[display_index][0]] = False

        # If button was pressed but team is already set to change, change it back
        if settings.stay_on_team and currently_displaying != team_info[display_index]:
            display_index = original_index

    logger.info("\nNo Team Currently Playing\n")
    reset_window_elements(window)  # Reset font and color to ensure everything is back to normal
    settings.stay_on_team = False  # Ensure next time function starts, we are not staying on a team
    return team_info
