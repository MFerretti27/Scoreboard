import FreeSimpleGUI as sg
import sys
import io
import tkinter as tk
import scoreboard
from get_team_league import MLB, NHL, NBA, NFL
from get_team_logos import get_team_logos
from get_team_league import append_team_array
import constants

filename = "constants.py"
FONT = "Helvetica"


class RedirectText(io.StringIO):
    '''Redirect print statements'''
    def __init__(self, window):
        self.window = window
        self.original_stdout = sys.stdout  # Save the original stdout

    def write(self, string):
        try:
            if self.window is not None and not self.window.was_closed():
                current_value = self.window["terminal_output"].get()
                current_value += string + "\n"  # Append the new string
                self.window["terminal_output"].update(current_value)
                self.window["terminal_output"].set_vscroll_position(1)
        except Exception as e:
            print(e)

    def flush(self):
        pass  # Optionally, handle flushing if needed

    def restore_stdout(self):
        sys.stdout = self.original_stdout  # Restore the original stdout


def create_main_layout(window_width, window_height):
    # sg.theme("LightBlue6")
    text_size = max(12, window_width // 20)
    button_size = max(12, window_width // 40)
    layout = [
        [sg.Push(), sg.Text("Major League Scoreboard", font=(FONT, text_size)), sg.Push()],
        [sg.VPush()],
        [
            sg.Push(),
            sg.Button("Add MLB team", font=(FONT, button_size)),
            sg.Button("Add NHL team", font=(FONT, button_size)),
            sg.Button("Add NBA team", font=(FONT, button_size)),
            sg.Button("Add NFL team", font=(FONT, button_size), pad=(0, button_size)),
            sg.Push(),
        ],
        [
            sg.Button("Documentation", font=(FONT, button_size), expand_x=True),
            sg.Button("Settings", font=(FONT, button_size), expand_x=True),
        ],
        [sg.Button("Start", font=(FONT, button_size), expand_x=True)],
        [
            sg.Push(),
            sg.Column([
                [sg.Multiline(size=(80, 20), key="terminal_output",
                              autoscroll=True, disabled=True,
                              background_color=sg.theme_background_color(),
                              text_color=sg.theme_text_color(),
                              sbar_background_color=sg.theme_background_color(),
                              sbar_trough_color=sg.theme_background_color(),
                              no_scrollbar=True, sbar_relief=sg.RELIEF_FLAT,
                              expand_x=True, visible=False)]
            ], expand_x=True),
            sg.Push(),
        ],
        [sg.VPush()],
    ]
    return layout


def create_team_selection_layout(window_width, window_height, league):
    checkboxes_per_column = 8
    selected_teams = read_teams_from_file()

    team_names = {
        "MLB": MLB,
        "NHL": NHL,
        "NBA": NBA,
        "NFL": NFL
    }.get(league, [])

    checkbox_width = max(20, window_width // 85)
    checkbox_height = max(2, window_height // 60)
    checkbox_size = max(12, window_width // 80)
    text_size = max(12, window_width // 20)
    button_size = max(12, window_width // 30)
    confirmation_txt_size = max(12, window_width // 60)

    team_checkboxes = [
        sg.Checkbox(team, key=f"{team}", size=(checkbox_width, checkbox_height),
                    font=(FONT, checkbox_size), pad=(5, 5), default=(team in selected_teams))
        for team in team_names
    ]

    columns = [
        team_checkboxes[i:i + checkboxes_per_column]
        for i in range(0, len(team_checkboxes), checkboxes_per_column)
    ]

    column_layouts = [
        sg.Column([[cb] for cb in col], pad=(10, 0), element_justification='Center') for col in columns
    ]

    layout = [
        [sg.VPush()],
        [sg.Push(), sg.Text(f"Choose {league} Team to Add", font=(FONT, text_size, "underline")), sg.Push()],
        [sg.VPush()],
        [sg.Push(), *column_layouts, sg.Push()],
        [sg.VPush()],
        [sg.Push(),
         sg.Text("", font=(FONT, confirmation_txt_size), key="teams_added", text_color='green'),
         sg.Push()
         ],
        [sg.Push(),
         sg.Text("", font=(FONT, confirmation_txt_size), key="teams_removed", text_color='red'),
         sg.Push()
         ],
        [sg.Push(),
         sg.Button("Save", font=(FONT, button_size)), sg.Button("Back", font=(FONT, button_size)),
         sg.Push()
         ],
        [sg.VPush()],
    ]
    return layout


def create_settings_layout(window_width, window_height):
    title_size = max(12, window_width // 20)
    button_size = max(12, window_width // 40)
    subtitle_size = max(12, window_width // 40)
    text_size = max(12, window_width // 80)
    text_input_size = max(12, window_width // 800)
    checkbox_width = max(20, window_width // 85)
    checkbox_height = max(2, window_height // 60)
    checkbox_size = max(12, window_width // 80)
    settings = read_settings_from_file()
    root = tk.Tk()
    font_options = sorted(root.tk.call("font", "families"))
    popular_fonts = [
        'Arial', 'Helvetica', 'Times New Roman', 'Courier New', 'Verdana',
        'Tahoma', 'Comic Sans MS', 'Georgia', 'Lucida Console',
        'Calibri', 'Trebuchet MS', 'Palatino', 'Century Gothic', 'Consolas'
    ]

    # Filter the available fonts to include only those that are in the "popular_fonts" list
    font_options = [font for font in popular_fonts if font in font_options]
    root.destroy()

    # Split into rows and columns
    font_rows = [font_options[i:i + 14] for i in range(0, len(font_options), 13)]

    general_setting_layout = sg.Frame(
        '',
        [
            [sg.Push(), sg.Text("General Settings", font=(FONT, subtitle_size)), sg.Push()],

            # Row containing "Live Data Delay", Input, Live Data Message, and Delay Text
            [
                sg.Text("Live Data Delay:", font=(FONT, button_size)),
                sg.Input(key='live_delay', enable_events=True, size=(text_size, 1),
                         font=('Arial', text_size), default_text=str(settings.get("LIVE_DATA_DELAY", 0))),
                sg.Text("", font=(FONT, text_input_size), key="Live_data_message", text_color='red'),
                sg.Push(),
                sg.Column([
                    [sg.Checkbox("Display Records", key="display_records",
                                 size=(checkbox_width, checkbox_height),
                                 font=(FONT, checkbox_size),
                                 default=settings.get("display_records", False))],
                    [sg.Checkbox("Display Venue", key="display_venue",
                                 size=(checkbox_width, checkbox_height),
                                 font=(FONT, checkbox_size),
                                 default=settings.get("display_venue", False))],
                ]),
                sg.Column([
                    [sg.Checkbox("Display Network", key="display_network",
                                 size=(checkbox_width, checkbox_height),
                                 font=(FONT, checkbox_size),
                                 default=settings.get("display_network", False))],
                    [sg.Checkbox("Display Odds", key="display_odds",
                                 size=(checkbox_width, checkbox_height),
                                 font=(FONT, checkbox_size),
                                 default=settings.get("display_odds", False))],
                ]),
            ],

            [sg.Text("*Delay in seconds to display live data", font=(FONT, text_input_size),
                     pad=(button_size, 0, 0, 0))],

            # Row containing "Change Font" label
            [sg.Text("Change Font:", font=(FONT, button_size)),
             sg.Text("", font=(FONT, text_input_size), key="font_message", text_color='red'),
             ],

            # Adding the checkboxes using the font
            *[
                [sg.Checkbox(f, key=f"font_{f}", font=(f, text_input_size), expand_x=True,
                             default=(f == settings["FONT"])) for f in row]
                for row in font_rows
            ],

        ],
        expand_x=True,
        relief=sg.RELIEF_SOLID,
        border_width=2,
        pad=(0, button_size, 0, 0),
    )

    specific_settings_layout = sg.Frame(
        '',
        [
            [sg.Push(),
             sg.Column([
                 [sg.Text("MLB Settings", font=(FONT, button_size), expand_x=True)],
                 [sg.Checkbox("Display Last Pitch", key="display_last_pitch",
                              size=(checkbox_width, checkbox_height),
                              font=(FONT, checkbox_size), expand_x=True,
                              default=settings.get("display_last_pitch", False))],
                 [sg.Checkbox("Display Play Description", key="display_play_description",
                              size=(checkbox_width, checkbox_height),
                              font=(FONT, checkbox_size),
                              default=settings.get("display_play_description", False))],
                 [sg.Checkbox("Display Bases", key="display_bases",
                              size=(checkbox_width, checkbox_height),
                              font=(FONT, checkbox_size), expand_x=True,
                              default=settings.get("display_bases", False))],
                 [sg.Checkbox("Display Count", key="display_balls_strikes",
                              size=(checkbox_width, checkbox_height),
                              font=(FONT, checkbox_size), expand_x=True,
                              default=settings.get("display_balls_strikes", False))],
                 [sg.Checkbox("Display Hits/Errors", key="display_hits_errors",
                              size=(checkbox_width, checkbox_height),
                              font=(FONT, checkbox_size), expand_x=True,
                              default=settings.get("display_hits_errors", False))],
                 [sg.Checkbox("Display Pitcher/Batter", key="display_pitcher_batter",
                              size=(checkbox_width, checkbox_height),
                              font=(FONT, checkbox_size), expand_x=True,
                              default=settings.get("display_pitcher_batter", False))],
                 [sg.Checkbox("Display Inning", key="display_inning",
                              size=(checkbox_width, checkbox_height),
                              font=(FONT, checkbox_size), expand_x=True,
                              default=settings.get("display_inning", False))],
                 [sg.Checkbox("Display Outs", key="display_outs",
                              size=(checkbox_width, checkbox_height),
                              font=(FONT, checkbox_size), expand_x=True,
                              default=settings.get("display_outs", False))],
             ], expand_x=True, vertical_alignment='top'),
             sg.Column([
                 [sg.Text("NBA Settings", font=(FONT, button_size), expand_x=True)],
                 [sg.Checkbox("Display Timeouts", key="display_nba_timeouts",
                              size=(checkbox_width, checkbox_height),
                              font=(FONT, checkbox_size), expand_x=True,
                              default=settings.get("display_nba_timeouts", False))],
                 [sg.Checkbox("Display Bonus", key="display_nba_bonus", size=(checkbox_width, checkbox_height),
                              font=(FONT, checkbox_size), expand_x=True,
                              default=settings.get("display_nba_bonus", False))],
                 [sg.Checkbox("Display Clock", key="display_nba_clock",
                              size=(checkbox_width, checkbox_height),
                              font=(FONT, checkbox_size), expand_x=True,
                              default=settings.get("display_nba_clock", False))],
                 [sg.Checkbox("Display Shooting Stats", key="display_nba_shooting",
                              size=(checkbox_width, checkbox_height),
                              font=(FONT, checkbox_size), expand_x=True,
                              default=settings.get("display_nba_shooting", False))],
             ], expand_x=True, vertical_alignment='top'),
             sg.Column([
                 [sg.Text("NHL Settings", font=(FONT, button_size), expand_x=True)],
                 [sg.Checkbox("Display Shots On Goal", key="display_nhl_sog",
                              size=(checkbox_width, checkbox_height),
                              font=(FONT, checkbox_size), expand_x=True,
                              default=settings.get("display_nhl_sog", False))],
                 [sg.Checkbox("Display Power Play", key="display_nhl_power_play",
                              size=(checkbox_width, checkbox_height),
                              font=(FONT, checkbox_size), expand_x=True,
                              default=settings.get("display_nhl_power_play", False))],
                 [sg.Checkbox("Display Clock", key="display_nhl_clock",
                              size=(checkbox_width, checkbox_height),
                              font=(FONT, checkbox_size), expand_x=True,
                              default=settings.get("display_nhl_clock", False))],
             ], expand_x=True, vertical_alignment='top'),
             sg.Column([
                 [sg.Text("NFL Settings", font=(FONT, button_size), expand_x=True)],
                 [sg.Checkbox("Display Timeouts", key="display_nfl_timeouts",
                              size=(checkbox_width, checkbox_height),
                              font=(FONT, checkbox_size), expand_x=True,
                              default=settings.get("display_nfl_timeouts", False))],
                 [sg.Checkbox("Display RedZone", key="display_nfl_redzone",
                              size=(checkbox_width, checkbox_height),
                              font=(FONT, checkbox_size), expand_x=True,
                              default=settings.get("display_nfl_redzone", False))],
                 [sg.Checkbox("Display Possession", key="display_possession",
                              size=(checkbox_width, checkbox_height),
                              font=(FONT, checkbox_size), expand_x=True,
                              default=settings.get("display_nfl_possession", False))],
                 [sg.Checkbox("Display Down/Yardage", key="display_down",
                              size=(checkbox_width, checkbox_height),
                              font=(FONT, checkbox_size), expand_x=True,
                              default=settings.get("display_nfl_down", False))],
                 [sg.Checkbox("Display Clock", key="display_nfl_clock",
                              size=(checkbox_width, checkbox_height),
                              font=(FONT, checkbox_size), expand_x=True,
                              default=settings.get("display_nfl_clock", False))],
             ], expand_x=True, vertical_alignment='top'),
             sg.Push(),
             ],
        ],
        expand_x=True,
        relief=sg.RELIEF_SOLID,
        border_width=2,
        pad=(0, 0)
    )

    layout = [
        [sg.Push(), sg.Text("Settings", font=(FONT, title_size, "underline")), sg.Push()],
        [general_setting_layout],
        [specific_settings_layout],
        [sg.Push(),
         sg.Text("", font=(FONT, button_size), key="confirmation_message", text_color='Green'),
         sg.Push()
         ],
        [sg.Push(),
         sg.Button("Save", font=(FONT, button_size)),
         sg.Button("Back", font=(FONT, button_size)),
         sg.Push(),
         ],
    ]
    return layout


def update_teams(selected_teams, league):
    available_checkbox_teams = {
        "MLB": MLB,
        "NHL": NHL,
        "NBA": NBA,
        "NFL": NFL
    }.get(league, [])

    existing_teams = read_teams_from_file()
    untouched_teams = [team for team in existing_teams if team not in available_checkbox_teams]
    new_teams = sorted(set(untouched_teams + selected_teams))

    teams_string = "teams = [\n"
    for team in new_teams:
        teams_string += f'    ["{team}"],\n'
    teams_string += "]\n"

    with open(filename, "r") as file:
        contents = file.readlines()

    start_index, end_index = None, None
    bracket_balance = 0
    found_teams = False

    for i, line in enumerate(contents):
        if not found_teams:
            if line.strip().startswith("teams = ["):
                start_index = i
                bracket_balance += line.count("[") - line.count("]")
                found_teams = True
        else:
            bracket_balance += line.count("[") - line.count("]")
            if bracket_balance == 0:
                end_index = i
                break

    if start_index is not None and end_index is not None:
        contents = contents[:start_index] + [teams_string] + contents[end_index + 1:]

        with open(filename, "w") as file:
            file.writelines(contents)

        added_teams = [team for team in selected_teams if team not in existing_teams]
        removed_teams = \
            [team for team in available_checkbox_teams if team in existing_teams and team not in selected_teams]

        teams_added = ""
        teams_removed = ""
        if added_teams:
            teams_added = f"Teams Added: {', '.join(added_teams)}  "
        if removed_teams:
            teams_removed = f"Teams Removed: {', '.join(removed_teams)}"
        if not added_teams and not removed_teams:
            teams_added += "No changes made."

        return teams_added, teams_removed


def read_teams_from_file():
    teams = []
    with open(filename, "r") as file:
        lines = file.readlines()
        inside_teams = False
        for line in lines:
            if line.strip().startswith("teams = ["):
                inside_teams = True
                continue
            if inside_teams:
                if line.strip().startswith("]"):
                    break
                team_name = line.strip().strip('[],').strip('"').strip("'")
                if team_name:
                    teams.append(team_name)
    return teams


def update_settings(live_data_delay, font_selected, selected_items):
    with open(filename, "r") as file:
        contents = file.readlines()

    setting_keys = [
        "display_last_pitch", "display_play_description", "display_bases", "display_balls_strikes",
        "display_hits_errors", "display_pitcher_batter", "display_inning", "display_outs",

        "display_nba_timeouts", "display_nba_bonus", "display_nba_clock", "display_nba_shooting",

        "display_nhl_clock", "display_nhl_sog", "display_nhl_power_play",

        "display_nfl_clock", "display_nfl_down", "display_nfl_possession",
        "display_nfl_timeouts", "display_nfl_redzone",

        "display_records", "display_venue", "display_network", "display_game_time", "display_odds",
    ]

    for i, line in enumerate(contents):
        if line.strip().startswith("LIVE_DATA_DELAY ="):
            contents[i] = f"LIVE_DATA_DELAY = {live_data_delay}\n"
        if line.strip().startswith("FONT ="):
            contents[i] = f'FONT = "{font_selected}"\n'

    for key, selected in zip(setting_keys, selected_items):
        for i, line in enumerate(contents):
            if line.strip().startswith(f"{key} ="):
                contents[i] = f"{key} = {str(selected)}\n"

    with open(filename, "w") as file:
        file.writelines(contents)


def read_settings_from_file():
    settings = {}
    keys_to_find = [
        "FONT", "LIVE_DATA_DELAY",
        "display_last_pitch", "display_play_description", "display_bases", "display_balls_strikes",
        "display_hits_errors", "display_pitcher_batter", "display_inning", "display_outs",

        "display_nba_timeouts", "display_nba_bonus", "display_nba_clock", "display_nba_shooting",

        "display_nhl_clock", "display_nhl_sog", "display_nhl_power_play",

        "display_nfl_clock", "display_nfl_down", "display_nfl_possession",
        "display_nfl_timeouts", "display_nfl_redzone",

        "display_records", "display_venue", "display_network", "display_game_time", "display_odds",
    ]

    with open(filename, "r") as file:
        lines = file.readlines()

    for line in lines:
        for key in keys_to_find:
            if line.strip().startswith(f"{key} ="):
                value = line.strip().split("=")[-1].strip()
                if key == "LIVE_DATA_DELAY":
                    try:
                        settings[key] = int(value)
                    except ValueError:
                        settings[key] = 0
                elif key == "FONT":
                    settings[key] = value.strip('"').strip("'")
                elif value.lower() == "true":
                    settings[key] = True
                else:
                    settings[key] = False
    return settings


def main():
    global FONT
    window_width = sg.Window.get_screen_size()[0]
    window_height = sg.Window.get_screen_size()[1]
    layout = create_main_layout(window_width, window_height)
    window = sg.Window("", layout, resizable=True,
                       size=(window_width, window_height), return_keyboard_events=True).Finalize()

    current_window = "main"
    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED, "Exit"):
            break

        elif "Add" in event:
            league = event.split(" ")[1]
            new_layout = create_team_selection_layout(window_width, window_height, league)
            window.hide()
            new_window = sg.Window("", new_layout, resizable=True, finalize=True, size=(window_width, window_height))
            window.close()
            window = new_window
            current_window = "team_selection"

        elif event == "Settings":
            new_layout = create_settings_layout(window_width, window_height)
            window.hide()
            new_window = sg.Window("", new_layout, resizable=True, finalize=True, size=(window_width, window_height))
            window.close()
            window = new_window
            current_window = "settings"

        elif event == "Back":
            window.hide()
            new_window = sg.Window("", create_main_layout(window_width, window_height),
                                   resizable=True, finalize=True,
                                   size=(window_width, window_height)).Finalize()
            window.close()
            window = new_window
            current_window = "main"

        elif event == "Save" and current_window == "team_selection":
            selected_teams = [team for team, selected in values.items() if selected]
            teams_added, teams_removed = update_teams(selected_teams, league)
            window["teams_added"].update(value=teams_added)
            window["teams_removed"].update(value=teams_removed)

        elif event == "Save" and current_window == "settings":
            setting_keys = [
                "display_last_pitch", "display_play_description",
                "display_nba_timeouts", "display_nba_bonus",
                "display_nhl_sog", "display_nhl_power_play",
                "display_nfl_timeouts", "display_nfl_redzone"
            ]
            selected_items = [values.get(key, False) for key in setting_keys]
            live_data_delay = values['live_delay']
            font_selected = [key for key in values if key.startswith("font_") and values[key]]
            if live_data_delay.isdigit() and len(font_selected) == 1:
                window["Live_data_message"].update(value="")
                window["font_message"].update(value="")
                live_data_delay = int(live_data_delay)
                font_selected = font_selected[0].replace('"', '').replace('font_', '') if font_selected else FONT
                update_settings(live_data_delay, font_selected, selected_items)
                FONT = font_selected
                window.refresh()
                window["confirmation_message"].update(value="Settings saved successfully!")
                continue
            elif not live_data_delay.isdigit():
                window["Live_data_message"].update(value="Please Enter Digits Only")
                window["confirmation_message"].update(value="")
            if len(font_selected) > 1:
                window["font_message"].update(value="Please Only Select One Font")
                window["confirmation_message"].update(value="")

        elif event == "Start" or ("Return" in event and current_window == "main"):
            redirect = RedirectText(window)  # Create an instance of RedirectText
            sys.stdout = redirect  # Redirect print statements to the window
            window["terminal_output"].update(visible=True)
            window.refresh()  # Refresh to display text
            append_team_array(constants.teams)  # Get the team league and sport name
            window.refresh()  # Refresh to display text
            get_team_logos(window, constants.teams)  # Get the team logos
            redirect.restore_stdout()  # Restore the original stdout after all output tasks are done
            window["terminal_output"].update(value="Starting scoreboard...")
            window.refresh()
            window.close()
            scoreboard.main()
            exit()

    window.close()


if __name__ == "__main__":
    main()
