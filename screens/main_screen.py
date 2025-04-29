import FreeSimpleGUI as sg  # type: ignore
import sys
import os
import time
import io
import tkinter as tk
from screens import not_playing_screen
from get_team_league import MLB, NHL, NBA, NFL
from get_team_logos import get_team_logos
from get_team_league import append_team_array
from main import set_screen
from update import check_for_update, update_program, list_backups, restore_backup
import settings
import platform
from instructions import help_text

filename = "settings.py"
FONT = "Helvetica"

# List of previous versions for the restore button
pervious_versions = []

# List of setting keys to be updated
setting_keys = [
    "display_last_pitch", "display_play_description", "display_bases", "display_balls_strikes",
    "display_hits_errors", "display_pitcher_batter", "display_inning", "display_outs",

    "display_nba_timeouts", "display_nba_bonus", "display_nba_clock", "display_nba_shooting",

    "display_nhl_clock", "display_nhl_sog", "display_nhl_power_play",

    "display_nfl_clock", "display_nfl_down", "display_nfl_possession",
    "display_nfl_timeouts", "display_nfl_redzone",

    "display_records", "display_venue", "display_network", "display_series", "display_odds", "display_date_ended"
]


class RedirectText(io.StringIO):
    '''Redirect print statements'''
    def __init__(self, window):
        self.window = window
        self.original_stdout = sys.stdout  # Save the original stdout

    def write(self, string) -> None:
        """Override the write method to redirect output to the window."""
        try:
            if self.window is not None and not self.window.was_closed():
                current_value = self.window["terminal_output"].get()
                current_value += string + "\n"  # Append the new string
                self.window["terminal_output"].update(current_value)
                self.window["terminal_output"].set_vscroll_position(1)
        except Exception as e:
            print(e)

    def restore_stdout(self) -> None:
        """Restore the original stdout."""
        sys.stdout = self.original_stdout


def create_main_layout(window_width):
    sg.theme("LightBlue6")
    text_size = max(12, window_width // 20)
    button_size = max(12, window_width // 40)
    update_button_size = max(12, window_width // 80)
    message_size = max(12, window_width // 60)
    layout = [
        [sg.Push(), sg.Text("Major League Scoreboard", font=(FONT, text_size)), sg.Push()],
        [sg.Push(),
         sg.Button("Restore from Version", font=(FONT, update_button_size), key="restore_button"),
         sg.Button("Check for Update", font=(FONT, update_button_size), key="update_button"),
         sg.Push()
         ],
        [
            sg.Push(),
            sg.Column(
                [
                    [sg.Combo(pervious_versions, key="versions", visible=False,
                              font=(FONT, update_button_size), size=(20, 1))]
                ],
                element_justification="center",
                justification="center",
                expand_x=True
            ),
            sg.Push()
        ],
        [sg.Push(), sg.Text("", font=(FONT, message_size), key="update_message"), sg.Push()],
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
            sg.Button("Manual", font=(FONT, button_size), expand_x=True),
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


def create_team_selection_layout(window_width, league):
    checkboxes_per_column = 8
    selected_teams = read_teams_from_file()

    team_names = {
        "MLB": MLB,
        "NHL": NHL,
        "NBA": NBA,
        "NFL": NFL
    }.get(league, [])

    # Common base screen widths
    common_base_widths = [1366, 1920, 1440, 1280]

    # Find the largest base width that doesn't exceed the window width using `max()`
    base_width = max([width for width in common_base_widths if width <= window_width], default=1366)
    scale = window_width / base_width

    max_size = 100
    text_size = min(max_size, max(60, int(65 * scale)))
    checkbox_width = min(max_size, max(10, int(20 * scale)))
    checkbox_height = min(max_size, max(2, int(2 * scale)))
    checkbox_txt_size = min(max_size, max(20, int(22 * scale)))
    button_size = min(max_size, max(48, int(50 * scale)))
    confirmation_txt_size = min(max_size, max(10, int(24 * scale)))

    team_checkboxes = [
        sg.Checkbox(team, key=f"{team}", size=(checkbox_width, checkbox_height),
                    font=(FONT, checkbox_txt_size), pad=(0, 0), default=(team in selected_teams))
        for team in team_names
    ]

    columns = [
        team_checkboxes[i:i + checkboxes_per_column]
        for i in range(0, len(team_checkboxes), checkboxes_per_column)
    ]

    column_layouts = [
        sg.Column([[cb] for cb in col], pad=(0, 0), element_justification='Center') for col in columns
    ]

    layout = [
        [sg.VPush()],
        [sg.Push(), sg.Text(f"Choose {league} Team to Add", font=(FONT, text_size, "underline")), sg.Push()],
        [sg.VPush()],
        [[sg.VPush()],
         sg.Push(), *column_layouts, sg.Push(),
         [sg.VPush()],],
        [sg.VPush()],
        [[sg.VPush()],
         sg.Push(),
         sg.Text("", font=(FONT, confirmation_txt_size), key="teams_added", text_color='green'),
         sg.Push(),
         [sg.VPush()],
         ],
        [[sg.VPush()],
         sg.Push(),
         sg.Text("", font=(FONT, confirmation_txt_size), key="teams_removed", text_color='red'),
         sg.Push(),
         [sg.VPush()],
         ],
        [sg.Push(),
         sg.Button("Save", font=(FONT, button_size)), sg.Button("Back", font=(FONT, button_size)),
         sg.Push()
         ],
        [sg.VPush()],
    ]
    return layout


def create_settings_layout(window_width):
    # Common base screen widths
    common_base_widths = [1366, 1920, 1440, 1280]
    # Find the largest base width that doesn't exceed the window width using `max()`
    base_width = max([width for width in common_base_widths if width <= window_width], default=1366)
    scale = window_width / base_width

    max_size = 100
    title_size = min(max_size, max(60, int(65 * scale)))
    checkbox_width = min(max_size, max(10, int(20 * scale)))
    checkbox_height = min(max_size, max(2, int(2 * scale)))
    message_size = min(max_size, max(6, int(12 * scale)))
    button_size = min(max_size, max(38, int(40 * scale)))
    text_input_size = min(max_size, max(2, int(4 * scale)))
    top_label_size = min(max_size, max(22, int(28 * scale)))
    bottom_label_size = min(max_size, max(22, int(26 * scale)))

    checkbox_size = min(max_size, max(10, int(16 * scale)))
    general_checkbox_width = min(max_size, max(14, int(18 * scale)))
    text_size = min(max_size, max(12, int(16 * scale)))

    settings = read_settings_from_file()
    root = tk.Tk()
    font_options = sorted(root.tk.call("font", "families"))
    popular_fonts = [
        'Arial', 'Helvetica', 'Times New Roman', 'Courier New', 'Optima',
        'Gill Sans', 'Comic Sans MS', 'Georgia', 'Lucida Console',
        'Calibri', 'Trebuchet MS', 'Century Gothic', 'Consolas'
    ]

    # Filter the available fonts to include only those that are in the "popular_fonts" list
    font_options = [font for font in popular_fonts if font in font_options]
    root.destroy()

    # Split into rows and columns
    font_rows = [font_options[i:i + 14] for i in range(0, len(font_options), 13)]

    general_setting_layout = sg.Frame(
        '',
        [
            # Row containing "Live Data Delay", Input, Live Data Message, and Delay Text
            [sg.Push(),
                sg.Column(
                    [
                        [sg.Text("Live Data Delay:", font=(FONT, top_label_size)),
                         sg.Input(key='live_delay', enable_events=True, size=(text_input_size, 1),
                                  font=('Arial', text_size),
                                  default_text=str(settings.get("LIVE_DATA_DELAY", 0))),
                         sg.Text("", font=(FONT, message_size), key="Live_data_message", text_color='red',
                                 expand_x=True)],
                        [
                            sg.Push(),
                            sg.Text("Delay in seconds to display live data",
                                    font=(FONT, message_size, "italic")),
                            sg.Push(),
                        ],
                    ],
            ),
                sg.Column(
                    [
                        [sg.Text("Display Timer (LIVE):", font=(FONT, top_label_size)),
                         sg.Input(key='display_playing', enable_events=True, size=(text_input_size, 1),
                                  font=('Arial', text_size),
                                  default_text=str(settings.get("DISPLAY_PLAYING_TIMER", 0))),
                         sg.Text("", font=(FONT, message_size), key="display_playing_message", text_color='red',
                                 expand_x=True)],
                        [
                            sg.Push(),
                            sg.Text("How often to Display each team when teams are playing",
                                    font=(FONT, message_size, "italic")),
                            sg.Push(),
                        ],
                    ],
            ),
                sg.Push(),
            ],
            [
                sg.Push(),
                sg.Column(
                    [
                        [sg.Text("Fetch Timer:", font=(FONT, top_label_size)),
                         sg.Input(key='fetch_not_playing', enable_events=True, size=(text_input_size, 1),
                                  font=('Arial', text_size),
                                  default_text=str(settings.get("FETCH_DATA_NOT_PLAYING_TIMER", 0))),
                         sg.Text("", font=(FONT, message_size), key="fetch_not_playing_message", text_color='red',
                                 expand_x=True)],
                        [
                            sg.Push(),
                            sg.Text("How often to get data when no team is playing",
                                    font=(FONT, message_size, "italic")),
                            sg.Push()
                        ],
                    ],
                ),
                sg.Column(
                    [
                        [sg.Text("Display Timer:", font=(FONT, top_label_size)),
                         sg.Input(key='display_not_playing', enable_events=True, size=(text_input_size, 1),
                                  font=('Arial', text_size),
                                  default_text=str(settings.get("DISPLAY_NOT_PLAYING_TIMER", 0))),
                         sg.Text("", font=(FONT, message_size), key="display_not_playing_message", text_color='red',
                                 expand_x=True)],
                        [
                            sg.Push(),
                            sg.Text("How often to Display each team when no team is playing",
                                    font=(FONT, message_size, "italic")),
                            sg.Push(),
                        ],
                    ]
                ),
                sg.Push()
            ],
            [sg.Text("What General Things to Display:", font=(FONT, bottom_label_size)),],
            [
                sg.Checkbox("Display Records", key="display_records",
                            size=(general_checkbox_width, checkbox_height),
                            font=(FONT, text_size),
                            default=settings.get("display_records", False)),
                sg.Checkbox("Display Venue", key="display_venue",
                            size=(general_checkbox_width, checkbox_height),
                            font=(FONT, text_size),
                            default=settings.get("display_venue", False)),
                sg.Checkbox("Display Broadcast", key="display_network",
                            size=(general_checkbox_width, checkbox_height),
                            font=(FONT, text_size),
                            default=settings.get("display_network", False)),
                sg.Checkbox("Display Odds", key="display_odds",
                            size=(general_checkbox_width, checkbox_height),
                            font=(FONT, text_size),
                            default=settings.get("display_odds", False)),
                sg.Checkbox("Display Series Info", key="display_series",
                            size=(general_checkbox_width, checkbox_height),
                            font=(FONT, text_size),
                            default=settings.get("display_series", False)),
                sg.Checkbox("Display Date Ended", key="display_date_ended",
                            size=(general_checkbox_width, checkbox_height),
                            font=(FONT, text_size),
                            default=settings.get("display_date_ended", False)),
            ],
            # Row containing "Change Font" label
            [sg.Text("Change Font:", font=(FONT, bottom_label_size)),
             sg.Text("", font=(FONT, message_size), key="font_message", text_color='red'),
             ],

            # Adding the checkboxes using the font
            *[
                [sg.Checkbox(f, key=f"font_{f}", font=(f, message_size), expand_x=True,
                             default=(f == settings["FONT"])) for f in row]
                for row in font_rows
            ],

        ],
        expand_x=True,
        relief=sg.RELIEF_SOLID,
        border_width=2,
        pad=(0, button_size)
    )

    specific_settings_layout = sg.Frame(
        '',
        [
            [sg.Push(),
             sg.Column([
                 [sg.Text("MLB Settings", font=(FONT, bottom_label_size), expand_x=True)],
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
                 [sg.Text("NBA Settings", font=(FONT, bottom_label_size), expand_x=True)],
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
                 [sg.Text("NHL Settings", font=(FONT, bottom_label_size), expand_x=True)],
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
                 [sg.Text("NFL Settings", font=(FONT, bottom_label_size), expand_x=True)],
                 [sg.Checkbox("Display Timeouts", key="display_nfl_timeouts",
                              size=(checkbox_width, checkbox_height),
                              font=(FONT, checkbox_size), expand_x=True,
                              default=settings.get("display_nfl_timeouts", False))],
                 [sg.Checkbox("Display RedZone", key="display_nfl_redzone",
                              size=(checkbox_width, checkbox_height),
                              font=(FONT, checkbox_size), expand_x=True,
                              default=settings.get("display_nfl_redzone", False))],
                 [sg.Checkbox("Display Possession", key="display_nfl_possession",
                              size=(checkbox_width, checkbox_height),
                              font=(FONT, checkbox_size), expand_x=True,
                              default=settings.get("display_nfl_possession", False))],
                 [sg.Checkbox("Display Down/Yardage", key="display_nfl_down",
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
        [[sg.VPush()],
         sg.Push(),
         sg.Text("", font=(FONT, button_size), key="confirmation_message", text_color='Green'),
         sg.Push(),
         [sg.VPush()],
         ],
        [[sg.VPush()],
         sg.Push(),
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


def update_settings(live_data_delay, fetch_timer, display_timer, display_timer_live,
                    font_selected, selected_items):
    with open(filename, "r") as file:
        contents = file.readlines()

    for i, line in enumerate(contents):
        if line.strip().startswith("LIVE_DATA_DELAY ="):
            contents[i] = f"LIVE_DATA_DELAY = {live_data_delay}\n"
        if line.strip().startswith("FONT ="):
            contents[i] = f'FONT = "{font_selected}"\n'
        if line.strip().startswith("FETCH_DATA_NOT_PLAYING_TIMER ="):
            contents[i] = f'FETCH_DATA_NOT_PLAYING_TIMER = {fetch_timer}\n'
        if line.strip().startswith("FETCH_DATA_NOT_PLAYING_TIMER ="):
            contents[i] = f'FETCH_DATA_NOT_PLAYING_TIMER = {fetch_timer}\n'
        if line.strip().startswith("DISPLAY_NOT_PLAYING_TIMER ="):
            contents[i] = f'DISPLAY_NOT_PLAYING_TIMER = {display_timer}\n'
        if line.strip().startswith("DISPLAY_PLAYING_TIMER ="):
            contents[i] = f'DISPLAY_PLAYING_TIMER = {display_timer_live}\n'

    for key, selected in zip(setting_keys, selected_items):
        for i, line in enumerate(contents):
            if line.strip().startswith(f"{key} ="):
                contents[i] = f"{key} = {str(selected)}\n"

    with open(filename, "w") as file:
        file.writelines(contents)


def read_settings_from_file():
    settings = {}
    keys_to_find = [
        "FONT", "LIVE_DATA_DELAY", "FETCH_DATA_NOT_PLAYING_TIMER", "FETCH_DATA_PLAYING_TIMER",
        "DISPLAY_NOT_PLAYING_TIMER", "DISPLAY_PLAYING_TIMER",

        "display_last_pitch", "display_play_description", "display_bases", "display_balls_strikes",
        "display_hits_errors", "display_pitcher_batter", "display_inning", "display_outs",

        "display_nba_timeouts", "display_nba_bonus", "display_nba_clock", "display_nba_shooting",

        "display_nhl_clock", "display_nhl_sog", "display_nhl_power_play",

        "display_nfl_clock", "display_nfl_down", "display_nfl_possession",
        "display_nfl_timeouts", "display_nfl_redzone",

        "display_records", "display_venue", "display_network", "display_series", "display_odds",
        "display_date_ended"
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
                elif key == "FETCH_DATA_NOT_PLAYING_TIMER":
                    try:
                        settings[key] = int(value)
                    except ValueError:
                        settings[key] = 0
                elif key == "DISPLAY_NOT_PLAYING_TIMER":
                    try:
                        settings[key] = int(value)
                    except ValueError:
                        settings[key] = 0
                elif key == "DISPLAY_PLAYING_TIMER":
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


def create_instructions_layout(window_height, window_width):
    common_base_widths = [1366, 1920, 1440, 1280]
    base_width = max([width for width in common_base_widths if width <= window_width], default=1366)
    scale = window_width / base_width
    max_size = 100
    title_size = min(max_size, max(60, int(65 * scale)))
    text_size = min(max_size, max(20, int(25 * scale)))
    button_size = min(max_size, max(48, int(50 * scale)))
    instructions_size = min(max_size, max(25, int(25 * scale)))
    layout = [
        [sg.Text('Manual', font=(FONT, title_size), justification='center', expand_x=True)],
        [sg.Multiline(help_text, size=(window_width, instructions_size), disabled=True,
                      no_scrollbar=False, font=('Courier', text_size))],
        [
            [sg.VPush()],
            sg.Push(),
            sg.Button('Back', font=(FONT, button_size)),
            sg.Push(),
        ],
    ]
    return layout


def main():
    global FONT
    set_screen()
    update = False
    window_width = sg.Window.get_screen_size()[0]
    window_height = sg.Window.get_screen_size()[1]
    layout = create_main_layout(window_width)
    window = sg.Window("", layout, resizable=True,
                       size=(window_width, window_height), return_keyboard_events=True).Finalize()

    current_window = "main"
    while True:
        if platform.system() == 'Darwin':
            window.TKroot.attributes('-fullscreen', True)
        else:
            window.Maximize()
        event, values = window.read()

        if event in (sg.WIN_CLOSED, "Exit") or 'Escape' in event:
            window.close()
            exit()

        elif "Add" in event:
            league = event.split(" ")[1]
            new_layout = create_team_selection_layout(window_width, league)
            window.hide()
            new_window = sg.Window("", new_layout, resizable=True, finalize=True,
                                   return_keyboard_events=True, size=(window_width, window_height))
            window.close()
            window = new_window
            current_window = "team_selection"

        elif event == "Settings":
            new_layout = create_settings_layout(window_width)
            window.hide()
            new_window = sg.Window("", new_layout, resizable=True, finalize=True,
                                   return_keyboard_events=True, size=(window_width, window_height))
            window.close()
            window = new_window
            current_window = "settings"

        elif event == "Back":
            window.hide()
            new_window = sg.Window("", create_main_layout(window_width),
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

            font_selected = [key for key in values if key.startswith("font_") and values[key]]
            no_fonts_available = False
            if not any(key.startswith("font_") for key in values):
                no_fonts_available = True

            if (live_data_delay.isdigit() and fetch_timer.isdigit() and display_timer.isdigit()
                and display_timer_live.isdigit() and (len(font_selected) == 1 or no_fonts_available)):

                font_selected = font_selected[0].replace('"', '').replace('font_', '') if font_selected else FONT
                update_settings(int(live_data_delay), int(fetch_timer), int(display_timer),
                                int(display_timer_live), font_selected, selected_items)

                FONT = font_selected
                window.refresh()
                window["Live_data_message"].update(value="")
                window["font_message"].update(value="")
                window["confirmation_message"].update(value="Settings saved successfully!")
                window["Live_data_message"].update(value="")
                window["fetch_not_playing_message"].update(value="")
                window["display_playing_message"].update(value="")
                window["font_message"].update(value="")
                continue

            if not live_data_delay.isdigit():
                window["Live_data_message"].update(value="Please Enter Digits Only")
            if not fetch_timer.isdigit():
                window["fetch_not_playing_message"].update(value="Please Enter Digits Only")
            if not display_timer.isdigit():
                window["display_not_playing_message"].update(value="Please Enter Digits Only")
            if not display_timer_live.isdigit():
                window["display_playing_message"].update(value="Please Enter Digits Only")
            if len(font_selected) != 1:
                window["font_message"].update(value="Please Select One Font")

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
            not_playing_screen.main()
            exit()

        elif "Manual" in event:
            current_window = "Documentation"
            window.hide()
            new_window = sg.Window("Documentation", create_instructions_layout(window_height, window_width),
                                   resizable=True, finalize=True, return_keyboard_events=True,
                                   size=(window_width, window_height))
            window.close()
            window = new_window


if __name__ == "__main__":
    main()
