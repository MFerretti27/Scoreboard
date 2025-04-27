from constants import *
import constants
import FreeSimpleGUI as sg  # pip install FreeSimpleGUI
from get_data.get_espn_data import get_data
from gui_setup import will_text_fit_on_screen, set_spoiler_mode, reset_window_elements, check_events
import time
from adafruit_ticks import ticks_ms, ticks_add, ticks_diff  # pip3 install adafruit-circuitpython-ticks


def team_currently_playing(window: sg.Window, teams: list) -> list:
    '''Display only games that are playing

    :param window: Window Element that controls GUI
    :param teams: Array of teams to search data for

    :return team_info: List of information for teams following
    '''

    teams_currently_playing = []
    first_time = True
    team_info = []
    teams_with_data = []
    display_index = 0
    should_scroll = False

    display_clock = ticks_ms()  # Start timer for switching display
    display_timer = 25 * 1000  # How often the display should update in seconds

    event = window.read(timeout=5000)

    while True in teams_currently_playing or first_time:
        teams_with_data.clear()
        team_info.clear()
        teams_currently_playing.clear()
        for fetch_index in range(len(teams)):
            print(f"\nFetching data for {teams[fetch_index][0]}")
            info, data, currently_playing = get_data(teams[fetch_index])
            team_info.append(info)
            teams_with_data.append(data)
            teams_currently_playing.append(currently_playing)

        if teams_with_data[display_index] and teams_currently_playing[display_index]:
            print(f"\n{teams[display_index][0]} is currently playing, updating display")
            sport_league = teams[display_index][1]

            # Reset text color, underline and timeouts, for new display
            reset_window_elements(window)

            should_scroll = will_text_fit_on_screen(team_info[display_index]['bottom_info'])

            for key, value in team_info[display_index].items():
                if "home_logo" in key or "away_logo" in key or "under_score_image" in key:
                    window[key].update(filename=value)
                elif "possession" not in key and "redzone" not in key and "bonus" not in key:
                    window[key].update(value=value)

                # Football specific display information
                if "NFL" in sport_league.upper():
                    if key == "home_timeouts":
                        window['home_timeouts'].update(value=value, text_color='yellow')
                    elif key == "away_timeouts":
                        window['away_timeouts'].update(value=value, text_color='yellow')

                    if team_info[display_index]['home_possession'] and key == 'home_score':
                        window[key].update(value=value, font=(FONT, SCORE_TXT_SIZE, "underline"))
                    elif team_info[display_index]['away_possession'] and key == 'away_score':
                        window[key].update(value=value, font=(FONT, SCORE_TXT_SIZE, "underline"))
                    if team_info[display_index]['home_redzone'] and key == 'home_score':
                        window[key].update(value=value, font=(FONT, SCORE_TXT_SIZE, "underline"), text_color='red')
                    elif team_info[display_index]['away_redzone'] and key == 'away_score':
                        window[key].update(value=value, font=(FONT, SCORE_TXT_SIZE, "underline"), text_color='red')

                # NBA Specific display size for top info
                if "NBA" in sport_league.upper():
                    if key == "top_info":
                        window['top_info'].update(value=value, font=(FONT, NBA_TOP_INFO_SIZE))
                    elif key == "home_timeouts":
                        window['home_timeouts'].update(value=value, font=(FONT, TIMEOUT_SIZE - 10), text_color='yellow')
                    elif key == "away_timeouts":
                        window['away_timeouts'].update(value=value, font=(FONT, TIMEOUT_SIZE - 10), text_color='yellow')

                    if team_info[display_index]['home_bonus'] and key == "home_score":
                        window[key].update(value=value, text_color='orange')
                    if team_info[display_index]['away_bonus'] and key == "away_score":
                        window[key].update(value=value, text_color='orange')

                # MLB Specific display size for bottom info
                if "MLB" in sport_league.upper():
                    if key == "top_info":
                        window['top_info'].update(value=value, font=(FONT, MLB_BOTTOM_INFO_SIZE))
                    if key == 'bottom_info':
                        window[key].update(value=value, font=(FONT, MLB_BOTTOM_INFO_SIZE))
                    elif key == 'under_score_image':
                        if "Networks" in team_info[display_index]['under_score_image']:
                            value = "baseball_base_images/empty_bases.png"
                        window[key].update(filename=value)
                    elif key == 'above_score_txt':
                        window[key].update(value=value, font=(FONT, TOP_TXT_SIZE))

                # NHL Specific display size for bottom info
                if "NHL" in sport_league.upper():
                    if key == 'top_info':
                        window[key].update(value=value, font=(FONT, NBA_TOP_INFO_SIZE))

                if constants.no_spoiler_mode:
                    set_spoiler_mode(window, True)

            event = window.read(timeout=5000)

        # Display Team Information
        if ticks_diff(ticks_ms(), display_clock) >= display_timer or first_time:
            if teams_with_data[display_index] and teams_currently_playing[display_index]:
                first_time = False
                # Find next team to display (skip teams not playing)
                if not constants.stay_on_team:  # If space pressed, stay on current team playing
                    original_index = display_index
                    for x in range(len(teams) * 2):
                        if teams_currently_playing[(original_index + x) % len(teams)] is False:
                            display_index = (display_index + 1) % len(teams)
                            print(f"skipping displaying {teams[(original_index + x) % len(teams)][0]}")
                        elif teams_currently_playing[(original_index + x) % len(teams)] is True and x != 0:
                            print(f"Found next team currently playing {teams[(original_index + x) % len(teams)][0]}\n")
                            break
                else:
                    print(f"Not Switching teams that are currently playing, staying on {teams[display_index][0]}\n")

            display_clock = ticks_add(display_clock, display_timer)
            if not constants.stay_on_team:
                display_index = (display_index + 1) % len(teams)

        if should_scroll:
            text = team_info[display_index]['bottom_info'] + "         "
            for _ in range(2):
                for _ in range(len(text)):
                    event = window.read(timeout=100)
                    text = text[1:] + text[0]
                    window["bottom_info"].update(value=text)
                time.sleep(5)
            should_scroll = False

        check_events(window, event)
        if constants.stay_on_team and sum(teams_currently_playing) == 1:
            constants.stay_on_team = False

    print("\nNo Team Currently Playing\n")
    # Reset font and color to ensure everything is back to normal
    reset_window_elements(window)
    return team_info
