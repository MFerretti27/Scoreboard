import gc
import os
import platform
import subprocess
import sys
import time

import FreeSimpleGUI as sg  # type: ignore

import settings
from get_data.get_team_league import append_team_array
from get_data.get_team_logos import get_team_logos
from gui_layouts import main_screen_layout, manual_layout, reorder_teams_layout, settings_layout, team_selection_layout
from helper_functions.main_menu_helpers import (
    RedirectText,
    load_teams_order,
    positive_num,
    save_teams_order,
    setting_keys,
    update_settings,
    update_teams,
)
from helper_functions.update import check_for_update, list_backups, restore_backup, update_program
from main import set_screen


def main():
    set_screen()
    update = False
    window_width = sg.Window.get_screen_size()[0]
    window_height = sg.Window.get_screen_size()[1]
    layout = main_screen_layout.create_main_layout(window_width)
    window = sg.Window("", layout, resizable=True,
                       size=(window_width, window_height), return_keyboard_events=True).Finalize()

    current_window = "main"
    teams = load_teams_order()
    team_names = [team[0] for team in teams]
    while True:
        if platform.system() == 'Darwin':
            window.TKroot.attributes('-fullscreen', True)
        else:
            window.Maximize()

        event, values = window.read()

        if current_window == "order_teams":
            selected = values['TEAM_ORDER']
            if selected:
                index = team_names.index(selected[0])

        if event in (sg.WIN_CLOSED, "Exit") or 'Escape' in event:
            window.close()
            sys.exit()

        elif "Add" in event:
            league = event.split(" ")[1]
            new_layout = team_selection_layout.create_team_selection_layout(window_width, league)
            window.hide()
            new_window = sg.Window("", new_layout, resizable=True, finalize=True,
                                   return_keyboard_events=True, size=(window_width, window_height))
            window.close()
            window = new_window
            current_window = "team_selection"

        elif event == "Settings":
            new_layout = settings_layout.create_settings_layout(window_width)
            window.hide()
            new_window = sg.Window("", new_layout, resizable=True, finalize=True,
                                   return_keyboard_events=True, size=(window_width, window_height))
            window.close()
            window = new_window
            current_window = "settings"

        elif event == "Set Team Order":
            new_layout = reorder_teams_layout.create_order_teams_layout(window_width)
            window.hide()
            new_window = sg.Window("", new_layout, resizable=True, finalize=True,
                                   return_keyboard_events=True, size=(window_width, window_height))
            window.close()
            window = new_window
            current_window = "order_teams"
            teams = load_teams_order()
            team_names = [team[0] for team in teams]

        elif event == "Back":
            window.hide()
            new_window = sg.Window("", main_screen_layout.create_main_layout(window_width),
                                   resizable=True, finalize=True, return_keyboard_events=True,
                                   size=(window_width, window_height)).Finalize()
            window.close()
            window = new_window
            current_window = "main"

        elif event == "Save" and current_window == "team_selection":
            selected_teams = [team for team, selected in values.items() if selected]
            teams_added, teams_removed = update_teams(selected_teams, league)
            window["teams_added"].update(value=teams_added)
            window["teams_removed"].update(value=teams_removed)
            teams = load_teams_order()
            team_names = [team[0] for team in teams]

        elif event == "update_button":
            message, successful, latest = check_for_update()
            if successful and update is False:
                if latest:
                    window["update_message"].update(value=message, text_color='green')
                else:
                    window["update_button"].update(text="Update", button_color=('white', 'green'))
                    window["update_message"].update(value=message + " Press Again to Update")
                    update = True
            elif successful and update is True:
                message, successful = update_program()
                if successful:
                    window["update_button"].update(text="Update", button_color=('white', 'green'))
                    window["update_message"].update(value=message, text_color='green')
                    update = False

                    time.sleep(5)
                    python = sys.executable  # Path to current python.exe
                    os.execl(python, python, *sys.argv)  # Relaunch same script with same arguments
            else:
                window["update_message"].update(value=message, text_color='red')

        elif event == "restore_button":
            pervious_versions = list_backups()
            if not pervious_versions:
                window["update_message"].update(value="No Previous Versions Found", text_color='red')
                continue
            window["versions"].update(values=pervious_versions, visible=True)
            window["restore_button"].update(text="Press to Restore", button_color=('white', 'green'))
            window["update_message"].update(value="Select Version to Restore", text_color='black')
            window.refresh()
            selected_version = values.get("versions")
            if selected_version:
                message, successful = restore_backup(selected_version)
                if successful:
                    window["update_message"].update(value=message, text_color='green')
                else:
                    window["update_message"].update(value=message, text_color='red')

        elif event == "Save" and current_window == "settings":

            selected_items = [values.get(key, False) for key in setting_keys]

            live_data_delay = values['live_delay']
            fetch_timer = values['fetch_not_playing']
            display_timer = values['display_not_playing']
            display_timer_live = values['display_playing']
            display_time = values['display_time']
            input_error_message = "Please Enter Positive Digits Only"

            font_selected = [key for key in values if key.startswith("font_") and values[key]]
            no_fonts_available = False
            if not any(key.startswith("font_") for key in values):
                no_fonts_available = True

            if (positive_num(live_data_delay) and positive_num(fetch_timer) and positive_num(display_timer)
                and positive_num(display_time) and positive_num(display_timer_live) and
                (len(font_selected) == 1 or no_fonts_available)):

                new_font = font_selected[0].replace('"', '').replace('font_', '') if font_selected else settings.FONT
                update_settings(int(live_data_delay), int(fetch_timer), int(display_timer), int(display_time),
                                int(display_timer_live), new_font, selected_items)

                window.refresh()
                correct = True
            else:
                correct = False

            if not positive_num(live_data_delay):
                window["Live_data_message"].update(value=input_error_message, text_color="red")
            else:
                window["Live_data_message"].update(value="Delay to display live data", text_color="black")
            if not positive_num(fetch_timer):
                window["fetch_not_playing_message"].update(value=input_error_message, text_color="red")
            else:
                window["fetch_not_playing_message"].update(value="How often to get data when no team is playing",
                                                           text_color="black")
            if not positive_num(display_timer):
                window["display_not_playing_message"].update(value=input_error_message, text_color="red")
            else:
                window["display_not_playing_message"].update(value="How often to Display each team when" +
                                                             " no team is playing", text_color="black")
            if not positive_num(display_timer_live):
                window["display_playing_message"].update(value=input_error_message, text_color="red")
            else:
                window["display_playing_message"].update(value="How often to Display each team when teams are playing",
                                                         text_color="black")
            if not positive_num(display_time):
                window["display_time_message"].update(value=input_error_message, text_color="red")
            else:
                window["display_time_message"].update(value="How long to display team info when finished",
                                                      text_color="black")
            if len(font_selected) != 1 and not no_fonts_available:
                window["font_message"].update(value="Please Select One Font")
            else:
                window["font_message"].update(value="")

            if correct:
                window["confirmation_message"].update(value="Settings saved successfully!")
            else:
                window["confirmation_message"].update(value="")

        elif event == "Start" or ("Return" in event and current_window == "main"):
            redirect = RedirectText(window)  # Create an instance of RedirectText
            sys.stdout = redirect  # Redirect print statements to the window
            window["terminal_output"].update(visible=True)
            window.refresh()  # Refresh to display text
            append_team_array(settings.teams)  # Get the team league and sport name
            window.refresh()  # Refresh to display text
            get_team_logos(window, settings.teams)  # Get the team logos
            redirect.restore_stdout()  # Restore the original stdout after all output tasks are done
            window["terminal_output"].update(value="Starting scoreboard...")
            window.refresh()
            window.close()
            gc.collect()  # Clean up memory
            time.sleep(0.5)  # Give OS time to destroy the window
            subprocess.Popen([sys.executable, "-m", "screens.not_playing_screen", *sys.argv[1:]])
            sys.exit()

        elif "Manual" in event:
            current_window = "Documentation"
            window.hide()
            new_window = sg.Window("Documentation",
                                   manual_layout.create_instructions_layout(window_width),
                                   resizable=True, finalize=True, return_keyboard_events=True,
                                   size=(window_width, window_height))
            window.close()
            window = new_window

        if event == 'Move Up' and index > 0:
            team_names[index], team_names[index - 1] = team_names[index - 1], team_names[index]
            window['TEAM_ORDER'].update(team_names, set_to_index=index - 1)

        elif event == 'Move Down' and index < len(team_names) - 1:
            team_names[index], team_names[index + 1] = team_names[index + 1], team_names[index]
            window['TEAM_ORDER'].update(team_names, set_to_index=index + 1)

        elif event == 'Save' and current_window == "order_teams":
            new_teams = [[name] for name in team_names]
            save_teams_order(new_teams)
            window["order_message"].update(value="Order Saved Successfully!")


if __name__ == "__main__":
    main()
