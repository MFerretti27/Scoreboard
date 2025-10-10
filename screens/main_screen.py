"""Functionality for Main screen GUI."""
import gc
import json
import logging
import os
import subprocess
import sys
import tempfile
import time
import typing
from pathlib import Path
from typing import Any

import FreeSimpleGUI as Sg  # type: ignore[import]

import settings
from get_data.get_team_league import append_team_array
from get_data.get_team_logos import get_team_logos
from get_data.get_team_names import get_new_team_names, update_new_division, update_new_names
from gui_layouts import (
    internet_connection_layout,
    main_screen_layout,
    manual_layout,
    reorder_teams_layout,
    settings_layout,
    team_selection_layout,
)
from helper_functions.internet_connection import connect_to_wifi, is_connected
from helper_functions.main_menu_helpers import (
    load_teams_order,
    positive_num,
    save_teams_order,
    setting_keys_booleans,
    settings_to_json,
    update_settings,
    update_teams,
    write_settings_to_py,
)
from helper_functions.update import check_for_update, list_backups, restore_backup, update_program
from main import set_screen

set_screen()
window_width = Sg.Window.get_screen_size()[0]
window_height = Sg.Window.get_screen_size()[1]
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
)
logger = logging.getLogger(__name__)



def main(saved_data: dict) -> None:
    """Create Main screen GUI functionality.

    :param saved_data: dictionary of save team information as to not lose it going to main screen
    """
    number_of_times_pressed = 0
    teams = load_teams_order()
    team_names = [team[0] for team in teams]

    # Create individual layout columns
    main_column = Sg.Frame("",
        main_screen_layout.create_main_layout(window_width),
        key="MAIN",
        size=(window_width, window_height),
        border_width=0,
    )

    layout = [[Sg.Column([[main_column]], key="VIEW_CONTAINER")]]
    window = Sg.Window("Scoreboard", layout, size=(window_width, window_height), resizable=True, finalize=True,
                       return_keyboard_events=True).Finalize()

    if not is_connected():
        window["update_message"].update(value="Please Connected to internet", text_color="red")
        window["Connect to Internet"].update(button_color=("white", "red"))

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
    event, values = window.read()
    if event in (Sg.WIN_CLOSED, "Exit") or "Escape" in event:
        window.close()
        sys.exit()

    elif "Add" in event:
        number_of_times_pressed = 0
        league = event.split(" ")[1]
        show_view(league, window)
        window, team_names = add_team_screen(window, event, team_names)

    elif "Connect to Internet" in event:
        number_of_times_pressed = 0
        show_view("INTERNET", window)
        window = internet_connection_screen(window)

    elif "Settings" in event:
        number_of_times_pressed = 0
        show_view("SETTINGS", window)
        window = settings_screen(window)

    elif "Set Team Order" in event:
        number_of_times_pressed = 0
        show_view("SET_ORDER", window)
        window = set_team_order_screen(window)

    elif "update_button" in event:
        number_of_times_pressed = handle_update(window, number_of_times_pressed)

    elif "restore_button" in event:
        number_of_times_pressed = 0
        handle_restore(window, values)

    elif "Start" in event or "Return" in event:
        handle_starting_script(window, saved_data)

    elif "Manual" in event:
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

    settings.division_checked = False  # Reset division checked status for new screen

    # Get the appropriate layout
    layouts = {
        "MAIN":     main_screen_layout.create_main_layout(window_width),
        "MLB":      team_selection_layout.create_team_selection_layout(window_width, "MLB"),
        "NFL":      team_selection_layout.create_team_selection_layout(window_width, "NFL"),
        "NBA":      team_selection_layout.create_team_selection_layout(window_width, "NBA"),
        "NHL":      team_selection_layout.create_team_selection_layout(window_width, "NHL"),
        "SETTINGS": settings_layout.create_settings_layout(window_width),
        "INTERNET": internet_connection_layout.create_internet_connection_layout(window_width),
        "SET_ORDER": reorder_teams_layout.create_order_teams_layout(window_width),
        "MANUAL": manual_layout.create_instructions_layout(window_width),
    }

    new_layout = [[Sg.Frame("", layouts[view_to_show], key=view_to_show,
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

        if "Back" in event:
            show_view("MAIN", window)
            return window, team_names

        if "Update Names" in event:
            show_fetch_popup(league)
            show_view(league, window)

        if "Save" in event:
            selected_teams = [team for team, selected in values.items() if selected]
            selected_teams.remove("versions")
            teams_added, teams_removed = update_teams(selected_teams, league)
            window["teams_added"].update(value=teams_added)
            window["teams_removed"].update(value=teams_removed)
            teams = load_teams_order()
            team_names = [team[0] for team in teams]

def show_fetch_popup(league: str) -> None:
    """Show a popup screen that give user a choice to update team names."""
    # Common base screen widths
    common_base_widths = [1366, 1920, 1440, 1280]

    # Find the largest base width that doesn't exceed the window width using `max()`
    base_width = max([width for width in common_base_widths if width <= window_width], default=1366)
    scale = window_width / base_width

    max_size = 100
    button_size = min(max_size, max(48, int(50 * scale)))
    message = min(max_size, max(14, int(20 * scale)))
    layout = [
        [Sg.VPush()],
        [Sg.Push(),
         Sg.Text("This will fetch new team names", key="top_message",
                 font=(settings.FONT, message),
                 ),
         Sg.Push(),
         ],
         [Sg.Push(),
         Sg.Text("Only do this if a team has changed their name",
                 key="middle_message", font=(settings.FONT, message, "underline"),
                 ),
         Sg.Push(),
         ],
         [Sg.Push(),
         Sg.Text("\nIf Team's are updated logo's will be re-downloaded when starting", key="bottom_message",
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
         Sg.Button("Update", key="update", font=(settings.FONT, button_size), pad=(20)),
         Sg.Button("Cancel", key="cancel", font=(settings.FONT, button_size), pad=(20)),
         Sg.Push(),
        ],
    ]

    window = Sg.Window(
        "",
        layout,
        modal=True,  # Forces focus until closed
        keep_on_top=True,
        size=(int(window_width/2), int(window_height/3)),
    )

    update = False
    while True:
        event, _ = window.read()

        if event in (Sg.WIN_CLOSED, "Exit") or "Escape" in event:
            window.close()
            return

        if "update" in event and not update:
            renamed, new_teams, error_message = get_new_team_names(league)
            if "Failed" in error_message:
                window["top_message"].Update(value="")
                window["bottom_message"].Update(value="")
                window["middle_message"].Update(value=error_message, font=(settings.FONT, message), text_color="red")
            elif not renamed:
                window["top_message"].Update(value="")
                window["bottom_message"].Update(value="")
                window["middle_message"].Update(value="No New Team Names Found",
                                                font=(settings.FONT, message), text_color="black")
            else:
                update = True
                display_renamed = ""
                for old, new in renamed:
                    display_renamed += f"{old}  --->  {new}\n"

                window["update"].Update(text="Confirm")
                window["bottom_message"].Update(value="")
                window["top_message"].Update(value="Found New Team Names, Press Confirm to Update")
                window["middle_message"].Update(value=display_renamed,
                                                font=(settings.FONT, message), text_color="black")

        elif "update" in event and update:
            update_new_names(league, new_teams, renamed)
            error_message = update_new_division(league)
            if "Failed" in error_message:
                window["top_message"].Update(value="")
                window["bottom_message"].Update(value="")
                window["middle_message"].Update(value=error_message, font=(settings.FONT, message), text_color="red")
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

        if "Save" in event:
            selected_items_booleans = [values.get(key, False) for key in setting_keys_booleans]

            selected_items_integers = {
                "LIVE_DATA_DELAY": values["LIVE_DATA_DELAY"],
                "FETCH_DATA_NOT_PLAYING_TIMER": values["FETCH_DATA_NOT_PLAYING_TIMER"],
                "DISPLAY_NOT_PLAYING_TIMER": values["DISPLAY_NOT_PLAYING_TIMER"],
                "DISPLAY_PLAYING_TIMER": values["DISPLAY_PLAYING_TIMER"],
                "HOW_LONG_TO_DISPLAY_TEAM": values["HOW_LONG_TO_DISPLAY_TEAM"],
            }

            if all(positive_num(v) for v in selected_items_integers.values()):
                update_settings(selected_items_integers, selected_items_booleans)

                window.refresh()
                correct = True
            else:
                correct = False

            input_error_message = "Please Enter Positive Digits Only"
            selected_items_error_messages = {
                "LIVE_DATA_DELAY": "Delay to display live data",
                "FETCH_DATA_NOT_PLAYING_TIMER": "How often to get data when no team is playing",
                "DISPLAY_NOT_PLAYING_TIMER": "How often to Display each team when no team is playing",
                "DISPLAY_PLAYING_TIMER": "How often to Display each team when teams are playing",
                "HOW_LONG_TO_DISPLAY_TEAM": "How long to display team info when finished",
            }

            for key, value in selected_items_integers.items():
                if not positive_num(value):
                    window[key + "_MESSAGE"].update(value=input_error_message, text_color="red")
                else:
                    window[key + "_MESSAGE"].update(value=selected_items_error_messages[key], text_color="black")

            if correct:
                window["confirmation_message"].update(value="Settings saved successfully!")
            else:
                window["confirmation_message"].update(value="")

        elif event == "Back":
            show_view("MAIN", window)
            return window

def set_team_order_screen(window: Sg.Window) -> Sg.Window:
    """Display GUI to change to order that team info is displayed.

    :param window: window GUI to display

    :return window: Window GUI to display
    """
    while True:
        event, values = window.read()
        if event in (Sg.WIN_CLOSED, "Exit") or "Escape" in event:
            window.close()
            sys.exit()

        teams = load_teams_order()
        team_names = [team[0] for team in teams]
        selected = values["TEAM_ORDER"]
        if selected:
            index = team_names.index(selected[0])

        if "Move Up" in event and index > 0:
            team_names[index], team_names[index - 1] = team_names[index - 1], team_names[index]
            window["TEAM_ORDER"].update(team_names, set_to_index=index - 1)

        elif "Move Down" in event and index < len(team_names) - 1:
            team_names[index], team_names[index + 1] = team_names[index + 1], team_names[index]
            window["TEAM_ORDER"].update(team_names, set_to_index=index + 1)

        elif "Save" in event:
            new_teams = [[name] for name in team_names]
            save_teams_order(new_teams)
            window["order_message"].update(value="Order Saved Successfully!")

        if "Back" in event:
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

        if "Back" in event:
            show_view("MAIN", window)
            return window

def handle_update(window: Sg.Window, number_of_times_pressed: int) -> int:
    """Update files when user pressed update button.

    :param window: window GUI to display
    :param number_of_times_pressed: How many times the user has pressed the update button

    :return number_of_times_pressed: Number of times user pressed update button
    """
    message, successful, latest = check_for_update()
    if successful and number_of_times_pressed == 0:
        if latest:
            window["update_message"].update(value=message, text_color="green")
        else:
            window["update_button"].update(text="Update", button_color=("white", "green"))
            window["update_message"].update(value=message + " Press Again to Update")
            number_of_times_pressed = 1
    elif successful and number_of_times_pressed == 1:
        window["update_message"].update(value="Updating...", text_color="green")
        window.read(timeout=100)
        settings = settings_to_json()
        serializable_settings = {
            k: v for k, v in settings.items()
            if not isinstance(v, type) and not isinstance(v, typing._SpecialForm)  # noqa: SLF001
        }

        settings_json = json.dumps(serializable_settings, indent=2)

        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".json") as tmp:
            tmp.write(settings_json)
            tmp_path = tmp.name
        message, successful = update_program()
        if successful:
            window["update_button"].update(text="Update", button_color=("white", "green"))
            window["update_message"].update(value=message, text_color="green")
            number_of_times_pressed = 0
            window.read(timeout=5)
            time.sleep(3)

            # Relaunch script, passing temp filename as argument
            python = sys.executable
            os.execl(python, python, "-m", "screens.main_screen", "--settings", tmp_path)
    else:
        window["update_message"].update(value=message, text_color="red")

    return number_of_times_pressed

def handle_restore(window: Sg.Window, values: dict[str, Any]) -> None:
    """Restore files when user pressed restore button.

    :param window: window GUI to display
    :param values: version that user wants to restore to
    """
    pervious_versions = list_backups()
    if not pervious_versions:
        window["update_message"].update(value="No Previous Versions Found", text_color="red")
        return
    window["versions"].update(values=pervious_versions, visible=True)
    window["restore_button"].update(text="Press to Restore", button_color=("white", "green"))
    window["update_message"].update(value="Select Version to Restore", text_color="black")
    window.refresh()
    selected_version = values.get("versions")
    if selected_version:
        message, successful = restore_backup(selected_version)
        if successful:
            window["update_message"].update(value=message, text_color="green")
            settings = settings_to_json()
            settings_json = json.dumps(settings, indent=2)

            time.sleep(5)
            with tempfile.NamedTemporaryFile("w", delete=False, suffix=".json") as tmp:
                tmp.write(settings_json)
                tmp_path = tmp.name

            # Relaunch script, passing temp filename as argument
            python = sys.executable
            os.execl(python, python, sys.argv[0], "--settings", tmp_path)
        else:
            window["update_message"].update(value=message, text_color="red")

def handle_starting_script(window: Sg.Window, saved_data: dict[str, Any]) -> None:
    """Run the script to display live team data in a new process.

    :param window: window GUI to display
    """
    window["PROGRESS_BAR"].update(visible=True)
    window["PROGRESS_BAR"].update(current_count=0)
    window.refresh()  # Refresh to display text
    append_team_array(settings.teams)  # Get the team league and sport name
    window.refresh()  # Refresh to display text
    download_logo_msg = get_team_logos(window, settings.teams)  # Get the team logos
    window["download_message"].update(value=f"{download_logo_msg}")
    window.refresh()

    if settings.LIVE_DATA_DELAY > 0:
        # Automatically set to true if user entered delay more than 0
        update_settings({"delay": True}, [])

    # If failed dont start
    if "Failed" in download_logo_msg:
        return

    window.close()
    gc.collect()  # Clean up memory
    time.sleep(0.5)  # Give OS time to destroy the window
    json_saved_data = json.dumps(saved_data)
    subprocess.Popen([sys.executable, "-m", "screens.not_playing_screen", json_saved_data])
    sys.exit()


def internet_connection_screen(window: Sg.Window) -> Sg.Window:
    """Run the script to display live team data in a new process.

    :param window: window GUI to display

    :return window: Window GUI to display
    """
    if is_connected():
        window["connection_message"].update(value="Already connected to internet", text_color="green")
    while True:
        event, values = window.read()
        if event in (Sg.WIN_CLOSED, "Exit") or "Escape" in event:
            window.close()
            sys.exit()

        if "Back" in event:
            show_view("MAIN", window)
            return window

        if "Save" in event:
            window["connection_message"].update(value="Trying to Connect...", text_color="black")
            event, _ = window.read(timeout=100)
            time.sleep(1)
            logger.info("User Entered %s and %s", values.get("SSID", ""), values.get("password", ""))
            connect_to_wifi(values.get("SSID", ""), values.get("password", ""))
            if is_connected():
                window["connection_message"].update(value="Connected!", text_color="green")
            else:
                window["connection_message"].update(value="Could not connect", text_color="red")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        try:
            if "--settings" in sys.argv:
                idx = sys.argv.index("--settings")
                saved_data = {}  # If settings pass passed in not saved data dont pass settings to scoreboard.py
                if idx + 1 < len(sys.argv):
                    settings_path = Path(sys.argv[idx + 1])  # Convert to Path
                    with settings_path.open(encoding="utf-8") as f:
                        settings_saved = json.load(f)
                        write_settings_to_py(settings_saved)
                        logger.info("Settings.py updated from JSON.")
            else:
                saved_data = json.loads(sys.argv[1])
        except json.JSONDecodeError:
            logger.exception("Invalid JSON argument:")
            saved_data = {}
    else:
        logger.info("No argument passed. Using default data.")
        saved_data = {}
    main(saved_data)
