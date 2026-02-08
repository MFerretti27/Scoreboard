"""Functionality for Main screen GUI."""
from __future__ import annotations

import gc
import json
import sys
import time
from pathlib import Path
from typing import Any

import FreeSimpleGUI as Sg  # type: ignore[import]

import settings
from constants import colors, messages
from get_data.get_team_league import get_team_league
from get_data.get_team_logos import get_team_logos
from get_data.get_team_names import get_new_team_names, update_new_division, update_new_names
from gui_layouts import (
    internet_connection_layout,
    keyboard_layout,
    main_screen_layout,
    manual_layout,
    reorder_teams_layout,
    scoreboard_layout,
    settings_layout,
    team_selection_layout,
)
from helper_functions.logging.logger_config import logger, rotate_error_log
from helper_functions.system.internet_connection import connect_to_wifi, is_connected
from helper_functions.system.update import (
    apply_update,
    check_for_update,
    download_specific_version,
    get_all_releases,
)
from helper_functions.ui.main_menu_helpers import (
    double_check_teams,
    positive_num,
    setting_keys_booleans,
    update_settings,
    update_teams,
)
from main import set_screen
from screens import scoreboard_screen

set_screen()
window_width = Sg.Window.get_screen_size()[0]
window_height = Sg.Window.get_screen_size()[1]
starting_message = ""

def main(window: Sg.Window, saved_data: dict) -> None:
    """Create Main screen GUI functionality.

    :param saved_data: dictionary of save team information as to not lose it going to main screen
    """
    number_of_times_pressed = 0
    teams = settings.read_settings().get("teams", [])
    team_names = [team[0] for team in teams]

    if not is_connected():
        window["update_message"].update(value="Please Connected to internet", text_color=colors.ERROR_RED)
        window["Connect to Internet"].update(button_color=colors.BUTTON_RED)
    else:
        window["update_message"].update(value=starting_message, text_color=colors.THEME_BLACK)

    while True:
        window.Maximize()
        number_of_times_pressed, team_names = check_events(window, team_names, number_of_times_pressed, saved_data)


def check_events(window: Sg.Window, team_names: list,
                 number_of_times_pressed: int, saved_data: dict) -> tuple[int, list[Any]]:
    """Check and handle events for the main screen.

    :param window: The window element
    :param team_names: The list of team names
    :param number_of_times_pressed: The number of times the update button has been pressed
    :param saved_data: The saved data dictionary

    :return: The updated number of times the update button has been pressed
    """
    event, _ = window.read()
    if event in (Sg.WIN_CLOSED, "Exit") or "Escape" in event:
        window.close()
        sys.exit()

    elif "Add" in event:
        number_of_times_pressed = 0
        league = event.split(" ")[1]
        show_view(league, window)
        window, team_names = add_team_screen(window, event, team_names)

    elif messages.BUTTON_CONNECT_TO_INTERNET in event:
        number_of_times_pressed = 0
        show_view("INTERNET", window)
        window = internet_connection_screen(window)

    elif messages.SETTINGS_TITLE in event:
        number_of_times_pressed = 0
        show_view("SETTINGS", window)
        window = settings_screen(window)

    elif messages.BUTTON_SET_TEAM_ORDER in event:
        number_of_times_pressed = 0
        show_view("SET_ORDER", window)
        window = set_team_order_screen(window)

    elif "update_button" in event:
        number_of_times_pressed = handle_update(window, number_of_times_pressed)

    elif "restore_button" in event:
        handle_restore(window, _)

    elif messages.BUTTON_START in event or "Return" in event:
        handle_starting_script(window, saved_data)

    elif messages.BUTTON_INSTRUCTIONS in event:
        number_of_times_pressed = 0
        show_view("MANUAL", window)
        window = manual_screen(window)

    return number_of_times_pressed, team_names

def show_view(view_to_show: str, window: Sg.Window) -> None:
    """Switch main screen views.

    :param view_to_show: Which view to make visible
    :param window: element containing all buttons and texts
    """
    logger.info("Switching layout to %s", view_to_show)

    container = window["VIEW_CONTAINER"]

    for child in list(container.Widget.winfo_children()):
        child.destroy()

    # Destroy all widgets from the window
    for element_key, element in list(window.AllKeysDict.items()):
        if element_key != "VIEW_CONTAINER":  # Don't touch container
            try:
                element.Widget.destroy()
                del window.AllKeysDict[element_key]  # Remove from keys dict
            except Exception:
                logger.info("Could not delete element")

    settings.division_checked.clear()  # Reset division checked status for new screen

    logger.info(f"Switching layout to {view_to_show}")

    # Use lambdas to defer layout creation until needed
    layouts = {
        "MAIN":     lambda: main_screen_layout.create_main_layout(window_width),
        "MLB":      lambda: team_selection_layout.create_team_selection_layout(window_width, "MLB"),
        "NFL":      lambda: team_selection_layout.create_team_selection_layout(window_width, "NFL"),
        "NBA":      lambda: team_selection_layout.create_team_selection_layout(window_width, "NBA"),
        "NHL":      lambda: team_selection_layout.create_team_selection_layout(window_width, "NHL"),
        "SETTINGS": lambda: settings_layout.create_settings_layout(window_width),
        "INTERNET": lambda: internet_connection_layout.create_internet_connection_layout(window_width),
        "SET_ORDER": lambda: reorder_teams_layout.create_order_teams_layout(window_width),
        "MANUAL": lambda: manual_layout.create_instructions_layout(window_width),
    }

    new_layout = [[Sg.Frame("", layouts[view_to_show](), key=view_to_show,
                            size=(window_width, window_height), border_width=0)]]

    window.extend_layout(container, new_layout)

    # Refresh to avoid greying issues
    window.refresh()
    time.sleep(0.05)

    # Fix rendering quirks when dynamically switching views with extend_layout()
    if view_to_show == "SET_ORDER":
        window["TEAM_ORDER"].set_focus()  # Focus the listbox
    elif view_to_show == "INTERNET":
        window["password"].set_focus() # Focus the input box
        window["SSID"].set_focus()  # Focus the input box


def add_team_screen(window: Sg.Window, event: str, team_names: list) -> tuple[Any, list[Any]]:
    """GUI screen to add different team to display information for.

    :param window: Window GUI to display
    :param event: The button that was pressed showing what league was selected
    :param team_names: Current teams being followed before screen was selected

    :return team_names: Names of teams the user choose to get information for
    :return window: Window GUI to display
    """
    league = event.split(" ")[1]
    while True:
        event, values = window.read(timeout=1000)

        if event in (Sg.WIN_CLOSED, "Exit") or "Escape" in event:
            window.close()
            sys.exit()

        if messages.BUTTON_BACK in event:
            show_view("MAIN", window)
            return window, team_names

        if messages.BUTTON_UPDATE_NAMES in event:
            show_fetch_popup(league)
            show_view(league, window)

        if messages.BUTTON_SAVE in event:
            selected_teams = [team for team, selected in values.items() if selected]
            selected_teams.remove("versions")
            teams_added, teams_removed = update_teams(selected_teams, league)
            window["teams_added"].update(value=teams_added)
            window["teams_removed"].update(value=teams_removed)
            teams = settings.read_settings().get("teams", [])
            team_names = [team[0] for team in teams]

def show_fetch_popup(league: str) -> None:
    """Show a popup screen that give user a choice to update team names."""
    # Common base screen widths
    common_base_widths = [1366, 1920, 1440, 1280]

    # Find the largest base width that doesn't exceed the window width using `max()`
    base_width = max([width for width in common_base_widths if width <= window_width], default=1366)
    scale = window_width / base_width

    max_size = 100
    button_size = min(max_size, max(14, int(50 * scale)))
    message = min(max_size, max(14, int(20 * scale)))
    layout = [
        [Sg.VPush()],
        [Sg.Push(),
         Sg.Text(messages.FETCH_NEW_TEAM_NAMES, key="top_message",
                 font=(settings.FONT, message),
                 ),
         Sg.Push(),
         ],
         [Sg.Push(),
         Sg.Text(messages.ONLY_IF_CHANGED,
                 key="middle_message", font=(settings.FONT, message, "underline"),
                 ),
         Sg.Push(),
         ],
         [Sg.Push(),
         Sg.Text(messages.IF_TEAMS_UPDATED, key="bottom_message",
                 font=(settings.FONT, message),
                 ),
         Sg.Push(),
         ],
         [Sg.Push(),
         Sg.Text("",
                 font=(settings.FONT, message),
                 ),
         Sg.Push(),
         ],
         [Sg.VPush()],
        [Sg.Push(),
         Sg.Button(messages.BUTTON_UPDATE, key="update", font=(settings.FONT, button_size), pad=(20)),
         Sg.Button(messages.BUTTON_CANCEL, key="cancel", font=(settings.FONT, button_size), pad=(20)),
         Sg.Push(),
        ],
    ]

    window = Sg.Window(
        "Warning",
        layout,
        modal=True,  # Forces focus until closed
        keep_on_top=True,
        resizable=True,
        finalize=True,
        auto_close=True,
        auto_close_duration=60,
    )

    update = False
    while True:
        window.bring_to_front()
        window.force_focus()
        event, _ = window.read()

        if event in (Sg.WIN_CLOSED, "Exit") or "Escape" in event:
            window.close()
            return

        if "update" in event and not update:
            renamed, new_teams, error_message = get_new_team_names(league)
            if "Failed" in error_message:
                window["top_message"].Update(value="")
                window["bottom_message"].Update(value="")
                window["middle_message"].Update(
                    value=error_message,
                    font=(settings.FONT, message),
                    text_color=colors.ERROR_RED,
                )
            elif not renamed:
                window["top_message"].Update(value="")
                window["bottom_message"].Update(value="")
                window["middle_message"].Update(
                    value=messages.NO_NEW_TEAM_NAMES,
                    font=(settings.FONT, message),
                    text_color=colors.NEUTRAL_BLACK,
                )
            else:
                update = True
                display_renamed = ""
                for old, new in renamed:
                    display_renamed += f"{old}  --->  {new}\n"

                window["update"].Update(text=messages.BUTTON_CONFIRM)
                window["bottom_message"].Update(value="")
                window["top_message"].Update(value=messages.TEAM_NAMES_UPDATED)
                window["middle_message"].Update(value=display_renamed,
                                                font=(settings.FONT, message), text_color=colors.NEUTRAL_BLACK)

        elif "update" in event and update:
            update_new_names(league, new_teams, renamed)
            error_message = update_new_division(league)
            if "Failed" in error_message:
                window["top_message"].Update(value="")
                window["bottom_message"].Update(value="")
                window["middle_message"].Update(
                    value=error_message,
                    font=(settings.FONT, message),
                    text_color=colors.ERROR_RED,
                )
            else:
                settings.always_get_logos = True  # re-download logos when starting
                window.close()
                return

        elif "cancel" in event:
            window.close()
            return

def settings_screen(window: Sg.Window) -> Sg.Window:
    """Display the settings screen and handle user interactions for updating settings.

    :param window: window GUI to display

    :return window: Window GUI to display
    """
    while True:
        event, values = window.read()
        if event in (Sg.WIN_CLOSED, "Exit") or "Escape" in event:
            window.close()
            sys.exit()

        if messages.BUTTON_SAVE in event:
            selected_items_booleans = [values.get(key, False) for key in setting_keys_booleans]

            selected_items_integers = {
                "LIVE_DATA_DELAY": values["LIVE_DATA_DELAY"],
                "DISPLAY_NOT_PLAYING_TIMER": values["DISPLAY_NOT_PLAYING_TIMER"],
                "DISPLAY_PLAYING_TIMER": values["DISPLAY_PLAYING_TIMER"],
                "HOW_LONG_TO_DISPLAY_TEAM": values["HOW_LONG_TO_DISPLAY_TEAM"],
            }

            if selected_items_integers["HOW_LONG_TO_DISPLAY_TEAM"] == "0":
                window["HOW_LONG_TO_DISPLAY_TEAM_MESSAGE"].update(value="Must display for at least 1 day",
                                                                  text_color=colors.ERROR_RED)
                continue

            if all(positive_num(v) for v in selected_items_integers.values()):
                update_settings(selected_items_integers, selected_items_booleans)

                window.refresh()
                correct = True
            else:
                correct = False

            input_error_message = "Please Enter Positive Digits Only"
            selected_items_error_messages = {
                "LIVE_DATA_DELAY": "Delay to display live data",
                "DISPLAY_NOT_PLAYING_TIMER": "How often to Display each team when no team is playing",
                "DISPLAY_PLAYING_TIMER": "How often to Display each team when teams are playing",
                "HOW_LONG_TO_DISPLAY_TEAM": "How long to display team info when finished",
            }

            for key, value in selected_items_integers.items():
                if not positive_num(value):
                    window[key + "_MESSAGE"].update(
                        value=input_error_message, text_color=colors.ERROR_RED,
                    )
                else:
                    window[key + "_MESSAGE"].update(
                        value=selected_items_error_messages[key],
                        text_color=colors.NEUTRAL_BLACK,
                    )

            if correct:
                window["confirmation_message"].update(value=messages.SETTINGS_SAVED)
            else:
                window["confirmation_message"].update(value="")

        elif event == messages.BUTTON_BACK:
            show_view("MAIN", window)
            return window

def set_team_order_screen(window: Sg.Window) -> Sg.Window:
    """Display GUI to change to order that team info is displayed.

    :param window: window GUI to display

    :return window: Window GUI to display
    """
    # Read teams once at the start
    teams = settings.read_settings().get("teams", [])
    team_names = [team[0] for team in teams]

    while True:
        event, values = window.read()
        if event in (Sg.WIN_CLOSED, "Exit") or "Escape" in event:
            window.close()
            sys.exit()

        selected = values["TEAM_ORDER"]

        if messages.BUTTON_MOVE_UP in event and selected:
            index = team_names.index(selected[0])
            if index > 0:
                team_names[index], team_names[index - 1] = team_names[index - 1], team_names[index]
                window["TEAM_ORDER"].update(team_names, set_to_index=index - 1)

        elif messages.BUTTON_MOVE_DOWN in event and selected:
            index = team_names.index(selected[0])
            if index < len(team_names) - 1:
                team_names[index], team_names[index + 1] = team_names[index + 1], team_names[index]
                window["TEAM_ORDER"].update(team_names, set_to_index=index + 1)

        elif messages.BUTTON_SAVE in event:
            new_teams = [[name] for name in team_names]
            flattened_teams = ([team[0] for team in new_teams] if
                       isinstance(new_teams[0], list) else new_teams)

            redefined_teams = []
            for team in new_teams:
                team_name, team_league, team_sport = get_team_league(str(team))
                redefined_teams.append([team_name, team_league, team_sport])

            settings.write_settings({"teams": redefined_teams})
            logger.info("Teams Reordered: %s", ", ".join(flattened_teams))

            window["order_message"].update(value=messages.ORDER_SAVED)

        if messages.BUTTON_BACK in event:
            show_view("MAIN", window)
            return window

def manual_screen(window: Sg.Window) -> Sg.Window:
    """Display GUI to change to order that team info is displayed.

    :param window: window GUI to display

    :return window: Window GUI to display
    """
    while True:
        event, _ = window.read()
        if event in (Sg.WIN_CLOSED, "Exit") or "Escape" in event:
            window.close()
            sys.exit()

        if messages.BUTTON_BACK in event:
            show_view("MAIN", window)
            return window

def handle_update(window: Sg.Window, number_of_times_pressed: int) -> int:
    """Update app when user pressed update button.

    :param window: window GUI to display
    :param number_of_times_pressed: How many times the user has pressed the update button

    :return number_of_times_pressed: Number of times user pressed update button
    """
    message, successful, latest = check_for_update()
    if successful and number_of_times_pressed == 0:
        if latest:
            window["update_message"].update(value=message, text_color=colors.SUCCESS_GREEN)
        else:
            window["update_button"].update(text="Update", button_color=colors.BUTTON_GREEN)
            window["update_message"].update(value=message + " Press Again to Update")
            number_of_times_pressed = 1
    elif successful and number_of_times_pressed == 1:
        window["update_message"].update(value=messages.UPDATING, text_color=colors.SUCCESS_GREEN)
        window.read(timeout=100)
        message, successful = apply_update()
        if successful:
            window["update_button"].update(text="Update", button_color=colors.BUTTON_GREEN)
            window["update_message"].update(value=message, text_color=colors.SUCCESS_GREEN)
            number_of_times_pressed = 0
            window.read(timeout=2000)  # Wait for update to complete
    else:
        window["update_message"].update(value=message, text_color=colors.ERROR_RED)

    return number_of_times_pressed

def handle_restore(window: Sg.Window, values: dict[str, Any]) -> None:
    """Show available versions and allow user to restore to an earlier version.

    :param window: window GUI to display
    :param values: dict containing selected version from dropdown
    """
    releases = get_all_releases()
    if not releases:
        window["update_message"].update(value=messages.NO_PREVIOUS_VERSIONS, text_color=colors.ERROR_RED)
        return

    # Extract version tags and format for display
    versions = []
    for release in releases:
        tag = release.get("tag_name", "")
        if tag:
            # Strip 'V' or 'v' prefix for cleaner display
            clean_tag = tag.lstrip("vV")
            versions.append(clean_tag)

    if not versions:
        window["update_message"].update(value=messages.NO_PREVIOUS_VERSIONS, text_color=colors.ERROR_RED)
        return

    window["versions"].update(values=versions, visible=True)
    window["restore_button"].update(text="Restore", button_color=colors.BUTTON_GREEN)
    window["update_message"].update(
        value=messages.SELECT_VERSION_RESTORE,
        text_color=colors.NEUTRAL_BLACK,
        font="italic",
    )
    window.refresh()

    # Get selected version
    selected_version = values.get("versions")
    if selected_version:
        message, successful = download_specific_version(selected_version)
        if successful:
            window["update_message"].update(value=message, text_color=colors.SUCCESS_GREEN)
            window.read(timeout=2000)
        else:
            window["update_message"].update(value=message, text_color=colors.ERROR_RED)

def handle_starting_script(window: Sg.Window, saved_data: dict[str, Any]) -> None:
    """Run the script to display live team data by calling scoreboard screen directly.

    :param window: window GUI to display
    """
    if len(settings.teams) == 0:
        window["download_message"].update(value=messages.ADD_AT_LEAST_ONE, text_color=colors.ERROR_RED)
        return

    double_check_teams()  # Ensure all teams in settings.teams are valid teams
    window["PROGRESS_BAR"].update(visible=True)
    window["PROGRESS_BAR"].update(current_count=0)
    succeeded, download_logo_msg = get_team_logos(window, settings.teams)  # Get the team logos
    window["download_message"].update(value=f"{download_logo_msg}")
    window.refresh()

    # If failed dont start
    if not succeeded:
        return

    # Update saved_data in settings before launching scoreboard
    settings.saved_data.update(saved_data)

    # Create the window with initial alpha of 0 for fade-in effect
    new_window = Sg.Window("Scoreboard", scoreboard_layout.create_scoreboard_layout(), no_titlebar=False,
                       resizable=True, return_keyboard_events=True, alpha_channel=0).Finalize()

    window.close()
    gc.collect()  # Clean up memory

    # Fade in the new window
    fade_duration = 300  # milliseconds
    fade_steps = 20
    step_duration = fade_duration / fade_steps
    for step in range(fade_steps):
        alpha = (step + 1) / fade_steps
        new_window.set_alpha(alpha)
        new_window.read(timeout=int(step_duration))

    # Call scoreboard screen directly instead of subprocess
    scoreboard_screen.main(new_window)
    sys.exit()


def internet_connection_screen(window: Sg.Window) -> Sg.Window:
    """Run the script to display live team data in a new process.

    :param window: window GUI to display

    :return window: Window GUI to display
    """
    if is_connected():
        window["connection_message"].update(value=messages.ALREADY_CONNECTED, text_color=colors.SUCCESS_GREEN)
    while True:
        event, values = window.read()
        if event in (Sg.WIN_CLOSED, "Exit") or "Escape" in event:
            window.close()
            sys.exit()

        if "open_keyboard" in event:
            keyboard_layout.keyboard_layout(window, ["SSID", "password"])

        if messages.BUTTON_BACK in event:
            show_view("MAIN", window)
            return window

        if messages.BUTTON_SAVE in event:
            window["connection_message"].update(value=messages.TRYING_TO_CONNECT, text_color=colors.NEUTRAL_BLACK)
            event, _ = window.read(timeout=100)
            time.sleep(1)
            # Avoid logging plaintext Wi-Fi passwords
            entered_ssid = values.get("SSID", "")
            _entered_password = values.get("password", "")
            logger.info("User entered SSID=%s and a password=%s", entered_ssid, _entered_password)
            connect_to_wifi(values.get("SSID", ""), values.get("password", ""))
            if is_connected():
                window["connection_message"].update(value=messages.CONNECTED, text_color=colors.SUCCESS_GREEN)
            else:
                window["connection_message"].update(value=messages.COULD_NOT_CONNECT, text_color=colors.ERROR_RED)


if __name__ == "__main__":
    saved_data = {}
    settings_saved = None
    rotate_error_log()  # Start fresh log file for this session

    # Load saved_data from settings.json first (backup from last session)
    persisted = settings.read_settings().get("saved_data", {})
    if persisted:
        saved_data = persisted

    # Parse arguments flexibly
    args = sys.argv[1:]
    try:
        if "--settings" in args:
            idx = args.index("--settings")
            if idx + 1 < len(args):
                settings_path = Path(args[idx + 1])
                with settings_path.open(encoding="utf-8") as f:
                    settings_saved = json.load(f)
                    settings.write_settings(settings_saved)
                    logger.info("settings.json updated from JSON.")

        if "--saved-data" in args:
            idx = args.index("--saved-data")
            if idx + 1 < len(args):
                saved_data = json.loads(args[idx + 1])

    except Exception:
        logger.exception("Error parsing startup arguments")
        saved_data = {}

    main_column = Sg.Frame("",
        main_screen_layout.create_main_layout(window_width),
        key="MAIN",
        size=(window_width, window_height),
        border_width=0,
    )

    layout = [[Sg.Column([[main_column]], key="VIEW_CONTAINER")]]
    window = Sg.Window("Scoreboard", layout, size=(window_width, window_height), resizable=True, finalize=True,
                       return_keyboard_events=True).Finalize()

    logger.info("Launching main_screen with saved_data=%s", bool(saved_data))
    main(window, saved_data)
