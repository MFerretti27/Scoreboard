'''Script to Display a Scoreboard for your Favorite Teams'''

import time
from adafruit_ticks import ticks_ms, ticks_add, ticks_diff  # type: ignore
from datetime import datetime, timedelta
from internet_connection import is_connected, reconnect
from gui_setup import gui_setup, will_text_fit_on_screen, reset_window_elements, check_events, set_spoiler_mode, resize_text
from screens.currently_playing_screen import team_currently_playing
from get_data.get_espn_data import get_data
from screens.clock_screen import clock
import settings


##################################
#                                #
#          Event Loop            #
#                                #
##################################
def main():
    team_info = []
    teams_with_data = []
    saved_data = {}
    display_index = 0
    should_scroll = False
    display_clock = ticks_ms()  # Start Timer for Switching Display
    display_timer = settings.DISPLAY_NOT_PLAYING_TIMER * 1000  # how often the display should update in seconds
    fetch_clock = ticks_ms()  # Start Timer for fetching data
    fetch_timer = settings.FETCH_DATA_NOT_PLAYING_TIMER * 1000  # how often to fetch data
    teams = settings.teams
    display_first_time = True
    fetch_first_time = True

    # resize_text()
    window = gui_setup()  # Create window to display teams

    while True:
        try:
            # Fetch Data
            if ticks_diff(ticks_ms(), fetch_clock) >= fetch_timer or fetch_first_time:
                fetch_first_time = False
                teams_with_data.clear()
                team_info.clear()
                for fetch_index in range(len(teams)):
                    print(f"\nFetching data for {teams[fetch_index][0]}")
                    info, data, currently_playing = get_data(teams[fetch_index])

                    # If Game in Play call function to display data differently
                    if currently_playing:
                        print(f"{teams[fetch_index][0]} Currently Playing")
                        team_info = team_currently_playing(window, teams)
                        # Reset timers
                        while ticks_diff(ticks_ms(), display_clock) >= display_timer * 2:
                            display_clock = ticks_add(display_clock, display_timer)
                        while ticks_diff(ticks_ms(), fetch_clock) >= fetch_timer * 2:
                            fetch_clock = ticks_add(fetch_clock, fetch_timer)

                    # Save data for to display longer than data is available (minimum 3 days)
                    if data is True and "FINAL" in info['bottom_info'] and teams[fetch_index][0] not in saved_data:
                        saved_data[teams[fetch_index][0]] = [info, datetime.now()]
                        if settings.display_date_ended:
                            info['bottom_info'] += "   " + datetime.now().strftime("%-m/%-d/%y")
                        print("Saving Data to display longer that its available")

                    elif teams[fetch_index][0] in saved_data and data is True:
                        if "FINAL" in info["bottom_info"]:
                            info['bottom_info'] = saved_data[teams[fetch_index][0]][0]['bottom_info']

                    elif teams[fetch_index][0] in saved_data and data is False:
                        print("Data is no longer available, checking if should display")
                        current_date = datetime.now()
                        date_difference = current_date - saved_data[teams[fetch_index][0]][1]
                        # Check if 3 days have passed after data is no longer available
                        if date_difference <= timedelta(days=settings.HOW_LONG_TO_DISPLAY_TEAM):
                            print(f"It will display, time its been: {date_difference}")
                            team_info.append(saved_data[teams[fetch_index][0]])
                            teams_with_data.append(True)
                            continue
                        # If greater than 3 days remove
                        else:
                            del saved_data[teams[fetch_index][0]]

                    team_info.append(info)
                    teams_with_data.append(data)

                fetch_clock = ticks_add(fetch_clock, fetch_timer)  # Reset Timer if data fetched

            # Display Team Information
            if ticks_diff(ticks_ms(), display_clock) >= display_timer or display_first_time:
                if teams_with_data[display_index]:
                    display_first_time = False
                    print(f"\nUpdating Display for {teams[display_index][0]}")
                    reset_window_elements(window)

                    should_scroll = will_text_fit_on_screen(team_info[display_index]['bottom_info'])

                    for key, value in team_info[display_index].items():
                        if "home_logo" in key or "away_logo" in key or "under_score_image" in key:
                            window[key].update(filename=value)
                        elif "possession" not in key and "redzone" not in key:
                            window[key].update(value=value, text_color='white')

                    if settings.no_spoiler_mode:
                        set_spoiler_mode(window, currently_playing=False, team_info=team_info[display_index])
                    event = window.read(timeout=2000)

                    # Find next team to display (skip teams with no data)
                    original_index = display_index
                    for x in range(len(teams)):
                        if teams_with_data[(original_index + x) % len(teams)] is False:
                            display_index = (display_index + 1) % len(teams)
                            print(f"skipping displaying {teams[(original_index + x) % len(teams)][0]}, has no data")
                        elif teams_with_data[(original_index + x) % len(teams)] is True and x != 0:
                            print(f"Found next team that has data {teams[(original_index + x) % len(teams)][0]}\n")
                            break

                    display_clock = ticks_add(display_clock, display_timer)  # Reset Timer if display updated
                else:
                    print(f"Team doesn't have data {teams[display_index][0]}")
                display_index = (display_index + 1) % len(teams)

            event = window.read(timeout=1)
            check_events(window, event)  # Check for button presses
            if settings.no_spoiler_mode:
                set_spoiler_mode(window, currently_playing=False, team_info=team_info[display_index])
            elif "Down" in event[0]:
                settings.no_spoiler_mode = False
                fetch_first_time = True
                display_first_time = True
                window["top_info"].update(value="")
                window["bottom_info"].update(value="Exiting No Spoiler Mode")
                event = window.read(timeout=1)

            # Scroll bottom info if text is too long
            if should_scroll and not settings.no_spoiler_mode:
                text = team_info[original_index]['bottom_info'] + "         "
                for _ in range(2):
                    for _ in range(len(text)):
                        event = window.read(timeout=100)
                        text = text[1:] + text[0]
                        window["bottom_info"].update(value=text)
                    time.sleep(5)

            if True not in teams_with_data:  # No data to display
                print("\nNo Teams with Data Displaying Clock\n")
                teams_with_data = clock(window, message="No Data For Any Teams")

        except Exception as error:
            print(f"Error: {error}")
            time_till_clock = 0
            if is_connected():
                while time_till_clock < 12:
                    try:
                        get_data(teams[display_index])
                        break  # If data is fetched successfully, break out of loop
                    except Exception as error:
                        print("Could not get data, trying again...")
                        window["top_info"].update(value="Could not get data, trying again...", text_color="red")
                        window["bottom_info"].update(value=error, text_color="red")
                        event = window.read(timeout=1)
                    time.sleep(30)
                    time_till_clock = time_till_clock + 1
                if time_till_clock >= 12:  # 6 minutes without data, display clock
                    message = 'Failed to Get Data, trying again every 3 minutes'
                    teams_with_data = clock(window, message)
                # Reset timers
                while ticks_diff(ticks_ms(), display_clock) >= display_timer * 2:
                    display_clock = ticks_add(display_clock, display_timer)
                while ticks_diff(ticks_ms(), fetch_clock) >= fetch_timer * 2:
                    fetch_clock = ticks_add(fetch_clock, fetch_timer)
            else:
                print("Internet connection is active")

            while not is_connected():
                print("Internet connection is down, trying to reconnect...")
                window["top_info"].update(value="Internet connection is down, trying to reconnect...", text_color="red")
                event = window.read(timeout=1)
                reconnect()
                time.sleep(20)  # Check every 20 seconds

                if time_till_clock >= 12:  # If no connection within 4 minutes display clock
                    message = "No Internet Connection"
                    print("\nNo Internet connection Displaying Clock\n")
                    teams_with_data = clock(window, message)
                    # Reset timers
                    while ticks_diff(ticks_ms(), display_clock) >= display_timer * 2:
                        display_clock = ticks_add(display_clock, display_timer)
                    while ticks_diff(ticks_ms(), fetch_clock) >= fetch_timer * 2:
                        fetch_clock = ticks_add(fetch_clock, fetch_timer)

                time_till_clock = time_till_clock + 1
            window.refresh()


if __name__ == "__main__":
    main()
