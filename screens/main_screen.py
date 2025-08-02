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
from gui_layouts import main_screen_layout, manual_layout, reorder_teams_layout, settings_layout, team_selection_layout
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
    set_screen()
    number_of_times_pressed = 0
    layout = main_screen_layout.create_main_layout(window_width)
    window = Sg.Window("", layout, resizable=True,
                       size=(window_width, window_height), return_keyboard_events=True).Finalize()

    current_window = "main"
    teams = load_teams_order()
    team_names = [team[0] for team in teams]

    while True:
        window.Maximize()
        event, values = window.read()

        if event in (Sg.WIN_CLOSED, "Exit") or "Escape" in event:
            window.close()
            sys.exit()

        elif "Add" in event:
            number_of_times_pressed = 0
            window, team_names = add_team_screen(window, event, team_names)

        elif event == "Settings":
            number_of_times_pressed = 0
            window = settings_screen(window)

        elif event == "Set Team Order":
            number_of_times_pressed = 0
            window = set_team_order_screen(window)

        elif event == "update_button":
            number_of_times_pressed = handle_update(window, number_of_times_pressed)

        elif event == "restore_button":
            handle_restore(window, values)

        elif event == "Start" or ("Return" in event and current_window == "main"):
            handle_starting_script(window, saved_data)

        elif "Manual" in event:
            number_of_times_pressed = 0
            window = manual_screen(window)

def add_team_screen(window: Sg.Window, event: str, team_names: list) -> tuple[Any, list[Any]]:
    """GUI screen to add different team to display information for.

    :param window: Window GUI to display
    :param event: The button that was pressed showing what league was selected
    :param team_names: Current teams being followed before screen was selected

    :return team_names: Names of teams the user choose to get information for
    """
    league = event.split(" ")[1]
    new_layout = team_selection_layout.create_team_selection_layout(window_width, league)
    window.hide()
    new_window = Sg.Window("", new_layout, resizable=True, finalize=True,
                        return_keyboard_events=True, size=(window_width, window_height))
    window.close()
    window = new_window
    while True:
        event, values = window.read()

        if event == "Back":
            window.hide()
            new_window = Sg.Window("", main_screen_layout.create_main_layout(window_width),
                                    resizable=True, finalize=True, return_keyboard_events=True,
                                    size=(window_width, window_height)).Finalize()
            window.close()
            window = new_window
            return window, team_names

        if event == "Save":
            selected_teams = [team for team, selected in values.items() if selected]
            teams_added, teams_removed = update_teams(selected_teams, league)
            window["teams_added"].update(value=teams_added)
            window["teams_removed"].update(value=teams_removed)
            teams = load_teams_order()
            team_names = [team[0] for team in teams]

def settings_screen(window: Sg.Window) -> Sg.Window:
    """Display the settings screen and handle user interactions for updating settings.

    :param window: window GUI to display
    """
    new_layout = settings_layout.create_settings_layout(window_width)
    window.hide()
    new_window = Sg.Window("", new_layout, resizable=True, finalize=True,
                            return_keyboard_events=True, size=(window_width, window_height))
    window.close()
    window = new_window
    while True:
        event, values = window.read()

        if event == "Save":
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
            window.hide()
            new_window = Sg.Window("", main_screen_layout.create_main_layout(window_width),
                                   resizable=True, finalize=True, return_keyboard_events=True,
                                   size=(window_width, window_height)).Finalize()
            window.close()
            return new_window

def set_team_order_screen(window: Sg.Window) -> Sg.Window:
    """Display GUI to change to order that team info is displayed.

    :param window: window GUI to display
    """
    new_layout = reorder_teams_layout.create_order_teams_layout(window_width)
    window.hide()
    new_window = Sg.Window("", new_layout, resizable=True, finalize=True,
                            return_keyboard_events=True, size=(window_width, window_height))
    window.close()
    window = new_window
    while True:
        event, values = window.read()


        teams = load_teams_order()
        team_names = [team[0] for team in teams]
        selected = values["TEAM_ORDER"]
        if selected:
            index = team_names.index(selected[0])

        if event == "Move Up" and index > 0:
            team_names[index], team_names[index - 1] = team_names[index - 1], team_names[index]
            window["TEAM_ORDER"].update(team_names, set_to_index=index - 1)

        elif event == "Move Down" and index < len(team_names) - 1:
            team_names[index], team_names[index + 1] = team_names[index + 1], team_names[index]
            window["TEAM_ORDER"].update(team_names, set_to_index=index + 1)

        elif event == "Save":
            new_teams = [[name] for name in team_names]
            save_teams_order(new_teams)
            window["order_message"].update(value="Order Saved Successfully!")

        if event == "Back":
            window.hide()
            new_window = Sg.Window("", main_screen_layout.create_main_layout(window_width),
                                   resizable=True, finalize=True, return_keyboard_events=True,
                                   size=(window_width, window_height)).Finalize()
            window.close()
            return new_window

def manual_screen(window: Sg.Window) -> Sg.Window:
    """Display GUI to change to order that team info is displayed.

    :param window: window GUI to display
    """
    window.hide()
    new_window = Sg.Window("Documentation",
                            manual_layout.create_instructions_layout(window_width),
                            resizable=True, finalize=True, return_keyboard_events=True,
                            size=(window_width, window_height))
    window.close()
    window = new_window
    while True:
        event, _ = window.read()

        if event == "Back":
            window.hide()
            new_window = Sg.Window("", main_screen_layout.create_main_layout(window_width),
                                    resizable=True, finalize=True, return_keyboard_events=True,
                                    size=(window_width, window_height)).Finalize()
            window.close()
            return new_window

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
            time.sleep(5)

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
    window.refresh()  # Refresh to display text
    append_team_array(settings.teams)  # Get the team league and sport name
    window.refresh()  # Refresh to display text
    download_logo_msg = get_team_logos(window, settings.teams)  # Get the team logos
    window["download_message"].update(value=f"{download_logo_msg}")
    window.refresh()

    # If failed dont start
    if "Failed" in download_logo_msg:
        return

    window.close()
    gc.collect()  # Clean up memory
    time.sleep(0.5)  # Give OS time to destroy the window
    json_saved_data = json.dumps(saved_data)
    subprocess.Popen([sys.executable, "-m", "screens.not_playing_screen", json_saved_data])
    sys.exit()

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
