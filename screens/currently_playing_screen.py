"""Module to display live information when team is currently playing."""
import copy
import time

import FreeSimpleGUI as sg  # type: ignore
from adafruit_ticks import ticks_add, ticks_diff, ticks_ms  # type: ignore

import settings
from get_data.get_espn_data import get_data
from helper_functions.scoreboard_helpers import (
    check_events,
    reset_window_elements,
    set_spoiler_mode,
    will_text_fit_on_screen,
)


class CurrentlyPlayingScreen:
    """Class to handle the currently playing screen."""

    def __init__(self, window: sg.Window, teams: list[list]):
        """Initialize the CurrentlyPlayingScreen."""
        self.window = window
        self.teams = teams

        # Initialize variables
        self.teams_currently_playing = []
        self.first_time = True
        self.delay_over = False
        self.team_info = []
        self.teams_with_data = []
        self.saved_data = []
        self.delay_info = []
        self.display_index = 0
        self.should_scroll = False
        self.currently_displaying = {}

    def fetch_and_store_team_data(self):
        for team in self.teams:
            print(f"\nFetching data for {team[0]}")
            info, data, playing = get_data(team)
            self.teams_with_data.append(data)
        self.teams_currently_playing.append(playing)
        (self.team_info if not settings.delay or self.first_time else self.delay_info).append(info)

    def store_last_info(self):
        global last_info
        last_info = copy.deepcopy(self.delay_info)
        self.delay_info.clear()

    def apply_delay(self, delay_clock: int):
        delay_timer = settings.LIVE_DATA_DELAY * 1000  # How long till information is displayed
        self.saved_data.append(copy.deepcopy(last_info))

        if ticks_diff(ticks_ms(), delay_clock) >= delay_timer:
            self.delay_over = True
            delay_clock = ticks_add(delay_clock, delay_timer)

            self.team_info = copy.deepcopy(self.saved_data.pop(0) if self.delay_over else last_info)
            self.update_team_info_for_delay(self.delay_over)

    def update_team_info_for_delay(self) -> None:
        """Update team information for delay."""
        for i, info in enumerate(self.team_info):
            if self.teams_with_data[i] and self.teams_currently_playing[i]:
                info.update({
                    "top_info": "Game Started",
                    "bottom_info": f"Setting delay of {settings.LIVE_DATA_DELAY} seconds",
                    "home_timeouts": "",
                    "away_timeouts": "",
                    "home_score": "0",
                    "away_score": "0",
                    "above_score_txt": "" if "@" not in info.get("above_score_txt", "") else info.get("above_score_txt", ""),
                    "under_score_image": "",
                })

                # Remove visual indicators during delay
                for key in [
                    ("home_possession", "away_possession", "home_redzone", "away_redzone"),
                    ("home_bonus", "away_bonus"),
                    ("home_power_play", "away_power_play")
                ]:
                    if all(k in info for k in key):
                        for k in key:
                            info[k] = False
                        break

    def update_display(self, window: sg.Window, key: str = "", value: str = "",
                       display_index: int = 0):
        """Update display based on the sport league.

        :param window: Window Element that controls GUI
        :param key: Key to update in the window
        :param value: Value to update the key with
        :param display_index: Index of the team being displayed

        :return: None
        """
        sport_league = self.teams[display_index][1]

        for key, value in self.team_info[display_index].items():
            if "home_logo" in key or "away_logo" in key or "under_score_image" in key:
                window[key].update(filename=value)
            elif key == "signature":
                window[key].update(filename=value, text_color="red")
            elif ("possession" not in key and "redzone" not in key and "bonus" not in key and
                "power_play" not in key):
                window[key].update(value=value)

            # Football specific display information
            if "NFL" in sport_league.upper() and self.teams_currently_playing[display_index]:
                self.update_display_nfl(window, key, value, display_index)

            # NBA Specific display size for top info
            if "NBA" in sport_league.upper() and self.teams_currently_playing[display_index]:
                self.update_display_nba(window, key, value, display_index)

            # MLB Specific display size for bottom info
            if "MLB" in sport_league.upper() and self.teams_currently_playing[display_index]:
                self.update_display_mlb(window, key, value)

            # NHL Specific display size for bottom info
            if "NHL" in sport_league.upper() and self.teams_currently_playing[display_index]:
                self.update_display_nhl(window, key, value, display_index)

            if settings.no_spoiler_mode:
                set_spoiler_mode(window, self.team_info[display_index])

            self.currently_displaying = self.team_info[display_index]

    def update_display_nfl(self, window: sg.Window, key: str = "", value: str = "",
                           display_index: int = 0):
        """Update display for NFL specific information.

        :param window: Window Element that controls GUI
        :param key: Key to update in the window
        :param value: Value to update the key with
        :param display_index: Index of the team being displayed

        :return: None
        """
        if key == "top_info":
            window["top_info"].update(value=value, font=(settings.FONT, settings.MLB_BOTTOM_INFO_SIZE))
        if key == "home_timeouts":
            window["home_timeouts"].update(value=value, text_color="yellow")
        elif key == "away_timeouts":
            window["away_timeouts"].update(value=value, text_color="yellow")

        if self.team_info[display_index]["home_possession"] and key == "home_score":
            window["home_score"].update(value=value, font=(settings.FONT,
                                                        settings.SCORE_TXT_SIZE, "underline"))
        elif self.team_info[display_index]["away_possession"] and key == "away_score":
            window["away_score"].update(value=value, font=(settings.FONT,
                                                        settings.SCORE_TXT_SIZE, "underline"))
        if self.team_info[display_index]["home_redzone"] and key == "home_score":
            window["home_score"].update(value=value,
                                        font=(settings.FONT, settings.SCORE_TXT_SIZE, "underline"),
                                        text_color="red")
        elif self.team_info[display_index]["away_redzone"] and key == "away_score":
            window["away_score"].update(value=value,
                                        font=(settings.FONT, settings.SCORE_TXT_SIZE, "underline"),
                                        text_color="red")

    def update_display_nba(self, window: sg.Window, key: str = "", value: str = "",
                           display_index: int = 0):
        """Update display for NBA specific information.

        :param window: Window Element that controls GUI
        :param key: Key to update in the window
        :param value: Value to update the key with
        :param display_index: Index of the team being displayed

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
        if "home_bonus" in self.team_info[display_index] or "away_bonus" in self.team_info[display_index]:
            if self.team_info[display_index]["home_bonus"] and key == "home_score":
                window[key].update(value=value, text_color="orange")
            if self.team_info[display_index]["away_bonus"] and key == "away_score":
                window[key].update(value=value, text_color="orange")

    def update_display_mlb(self, window: sg.Window, key: str = "", value: str = ""):
        """Update display for MLB specific information.

        :param window: Window Element that controls GUI
        :param key: Key to update in the window
        :param value: Value to update the key with

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

    def update_display_nhl(self, window: sg.Window, key: str = "", value: str = "",
                           display_index: int = 0):
        """Update display for NHL specific information.
        :param window: Window Element that controls GUI
        :param key: Key to update in the window
        :param value: Value to update the key with
        :param display_index: Index of the team being displayed

        :return: None
        """
        if key == "top_info":
            window[key].update(value=value, font=(settings.FONT, settings.NBA_TOP_INFO_SIZE))
        if key == "above_score_txt" and settings.display_nhl_power_play:
            window[key].update(value=value, font=(settings.FONT, settings.TOP_TXT_SIZE))

        # Ensure power play is in dictionary to not cause key error
        if "home_power_play" in self.team_info[display_index] or "away_power_play" in self.team_info[display_index]:
            if self.team_info[display_index]["home_power_play"] and key == "home_score":
                window["home_score"].update(value=value, font=(settings.FONT, settings.SCORE_TXT_SIZE),
                                            text_color="blue")
            elif self.team_info[display_index]["away_power_play"] and key == "away_score":
                window["away_score"].update(value=value, font=(settings.FONT, settings.SCORE_TXT_SIZE),
                                            text_color="blue")


    def find_next_team(self, teams: list[list], display_index: int) -> list[int]:
        """Find the next team to display based on settings."""
        # Find next team to display (skip teams not playing)
        # If shift pressed, stay on current team playing
        original_index = display_index
        if self.teams_currently_playing[display_index] or (self.teams_with_data[display_index] and
                                                            not settings.prioritize_playing_team):
            if not settings.stay_on_team and settings.prioritize_playing_team:
                for x in range(len(teams) * 2):
                    if self.teams_currently_playing[(original_index + x) % len(teams)] is False:
                        display_index = (display_index + 1) % len(teams)
                        print(f"skipping displaying {teams[(original_index + x) % len(teams)][0]}")
                    elif self.teams_currently_playing[(original_index + x) % len(teams)] is True and x != 0:
                        print(f"Found next team currently playing {teams[(original_index + x) % len(teams)][0]}\n")
                        break
        elif not settings.stay_on_team and not settings.prioritize_playing_team:
            for x in range(len(teams) * 2):
                if self.teams_with_data[(original_index + x) % len(teams)] is False:
                    display_index = (display_index + 1) % len(teams)
                    print(f"skipping displaying {teams[(original_index + x) % len(teams)][0]}")
                elif self.teams_with_data[(original_index + x) % len(teams)] is True and x != 0:
                    print(f"Found next team that has data {teams[(original_index + x) % len(teams)][0]}\n")
                    break
        else:
            print(f"Not Switching teams that are currently playing, staying on {teams[display_index][0]}\n")

        if not settings.stay_on_team:
             display_index = (display_index + 1) % len(teams)
        return display_index, original_index

    def team_currently_playing(self, window: sg.Window, teams: list[list]) -> list:
        """Display only games that are currently playing.

        :param window: Window Element that controls GUI
        :param teams: List containing lists of teams to display data for

        :return team_info: List of information for teams following
        """
        first_time = True
        display_index = 0
        should_scroll = False

        display_clock = ticks_ms()  # Start timer for switching display
        display_timer = settings.DISPLAY_PLAYING_TIMER * 1000  # How often the display should update in seconds
        fetch_clock = ticks_ms()  # Start timer for fetching
        fetch_timer = 2 * 1000  # How often to fetch data in seconds
        delay_clock = ticks_ms()  # Start timer how long to start displaying information
        event = window.read(timeout=100)

        if ticks_diff(ticks_ms(), fetch_clock) >= fetch_timer or first_time:
            self.teams_with_data.clear()
            self.team_info.clear()
            self.teams_currently_playing.clear()
            self.fetch_and_store_team_data()

            if settings.delay:
                self.store_last_info()
                self.apply_delay(delay_clock)

            fetch_clock = ticks_add(fetch_clock, fetch_timer)

            if self.teams_with_data[display_index] and (self.teams_currently_playing[display_index] or
                                                not settings.prioritize_playing_team):
                print(f"\n{teams[display_index][0]} is currently playing, updating display")

                # Reset text color, underline and timeouts, for new display
                reset_window_elements(window)
                should_scroll = will_text_fit_on_screen(self.team_info[display_index]["bottom_info"])
                self.update_display(window, display_index=display_index)
                event = window.read(timeout=5000)

        # Find Next team to display
        if ticks_diff(ticks_ms(), display_clock) >= display_timer or first_time:
            first_time = False
            display_index, original_index = self.find_next_team(teams, display_index)
            display_clock = ticks_add(display_clock, display_timer)  # Reset Timer

        if should_scroll and not settings.no_spoiler_mode and self.currently_displaying == self.team_info[display_index]:
            text = self.team_info[display_index]["bottom_info"] + "         "
            for _ in range(2):
                for _ in range(len(text)):
                    event = window.read(timeout=100)
                    text = text[1:] + text[0]
                    window["bottom_info"].update(value=text)
                time.sleep(5)
            should_scroll = False

        if not first_time:
            temp_delay = settings.delay  # store to see if changed
            check_events(window, event, currently_playing=True)
            if settings.stay_on_team and sum(self.teams_currently_playing) == 1:
                window["top_info"].update(value='No longer set to "staying on team"')
                window["bottom_info"].update(value="Only one team playing")
                window.read(timeout=2000)
                time.sleep(5)
                settings.stay_on_team = False

            if temp_delay is not settings.delay:
                delay_clock = ticks_ms()
                self.delay_over = False

            # If button was pressed but team is already set to change, change it back
            if settings.stay_on_team and self.currently_displaying != self.team_info[display_index]:
                display_index = original_index

        print("\nNo Team Currently Playing\n")
        reset_window_elements(window)  # Reset font and color to ensure everything is back to normal
        settings.stay_on_team = False  # Ensure next time function starts, we are not staying on a team
        return self.team_info
