"""GUI Layout for changing scoreboard settings in main menu."""
import tkinter as tk

import FreeSimpleGUI as sg  # type: ignore

import settings
from helper_functions.main_menu_helpers import read_settings_from_file


def create_settings_layout(window_width: int) -> list:
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
    text_size = min(max_size, max(12, int(16 * scale)))

    current_settings = read_settings_from_file()
    root = tk.Tk()
    font_options = sorted(root.tk.call("font", "families"))
    popular_fonts = [
        'Arial', 'Helvetica', 'Times New Roman', 'Courier New', 'Optima',
        'Gill Sans', 'Comic Sans MS', 'Georgia', 'Lucida Console',
        'Calibri', 'Trebuchet MS', 'Century Gothic', 'Consolas',
        'QuickSand', 'Z003', 'FreeMono', 'P052', 'Droid Sans Fallback',
        'C509', 'URW Bookman', 'Noto Mono', 'PibotoLt'
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
                        [sg.Text("Live Data Delay:", font=(settings.FONT, top_label_size)),
                         sg.Spin([str(i) for i in range(1000)], key='live_delay', enable_events=True,
                                 size=(text_input_size, 1),
                                 font=('Arial', text_size),
                                 initial_value=str(current_settings.get("LIVE_DATA_DELAY", 0))),
                         sg.Text("seconds", font=(settings.FONT, message_size), expand_x=True, pad=(0, 0)),
                         ],
                        [
                            sg.Push(),
                            sg.Text("Delay to display live data", key="Live_data_message",
                                    font=(settings.FONT, message_size, "italic")),
                            sg.Push(),
                        ],
                    ],
            ),
                sg.Column(
                    [
                        [sg.Text("Display Timer (LIVE):", font=(settings.FONT, top_label_size)),
                         sg.Spin([str(i) for i in range(1000)], key='display_playing', enable_events=True,
                                 size=(text_input_size, 1),
                                 font=('Arial', text_size),
                                 initial_value=str(current_settings.get("DISPLAY_PLAYING_TIMER", 0))),
                         sg.Text("seconds", font=(settings.FONT, message_size), expand_x=True, pad=(0, 0)),
                         ],
                        [
                            sg.Push(),
                            sg.Text("How often to Display each team when teams are playing",
                                    key="display_playing_message",
                                    font=(settings.FONT, message_size, "italic")),
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
                        [sg.Text("Fetch Timer:", font=(settings.FONT, top_label_size)),
                         sg.Spin([str(i) for i in range(1000)], key='fetch_not_playing', enable_events=True,
                                 size=(text_input_size, 1),
                                 font=('Arial', text_size),
                                 initial_value=str(current_settings.get("FETCH_DATA_NOT_PLAYING_TIMER", 0))),
                         sg.Text("seconds", font=(settings.FONT, message_size), expand_x=True, pad=(0, 0)),
                         ],
                        [
                            sg.Push(),
                            sg.Text("How often to get data when no team is playing",
                                    key="fetch_not_playing_message",
                                    font=(settings.FONT, message_size, "italic")),
                            sg.Push()
                        ],
                    ],
                ),
                sg.Column(
                    [
                        [sg.Text("Display Timer:", font=(settings.FONT, top_label_size)),
                         sg.Spin([str(i) for i in range(1000)], key='display_not_playing', enable_events=True,
                                 size=(text_input_size, 1),
                                 font=('Arial', text_size),
                                 initial_value=str(current_settings.get("DISPLAY_NOT_PLAYING_TIMER", 0))),
                         sg.Text("seconds", font=(settings.FONT, message_size), expand_x=True, pad=(0, 0)),
                         ],
                        [
                            sg.Push(),
                            sg.Text("How often to Display each team when no team is playing",
                                    key="display_not_playing_message",
                                    font=(settings.FONT, message_size, "italic")),
                            sg.Push(),
                        ],
                    ],
                ),
                sg.Column(
                    [
                        [sg.Text("Display Time:", font=(settings.FONT, top_label_size)),
                         sg.Spin([str(i) for i in range(1000)], key='display_time', enable_events=True,
                                 size=(text_input_size, 1),
                                 font=('Arial', text_size),
                                 initial_value=str(current_settings.get("HOW_LONG_TO_DISPLAY_TEAM", 0))),
                         sg.Text("days", font=(settings.FONT, message_size), expand_x=True, pad=(0, 0)),
                         ],
                        [
                            sg.Push(),
                            sg.Text("How long to display team info when finished",
                                    key="display_time_message",
                                    font=(settings.FONT, message_size, "italic")),
                            sg.Push(),
                        ],
                    ]
                ),
                sg.Push()
            ],
            [sg.Text("", font=(settings.FONT, bottom_label_size)),],
            [
                sg.Checkbox("Display Records", key="display_records",
                            font=(settings.FONT, text_size),
                            expand_x=True,
                            default=current_settings.get("display_records", False)),
                sg.Checkbox("Display Venue", key="display_venue",
                            font=(settings.FONT, text_size),
                            expand_x=True,
                            default=current_settings.get("display_venue", False)),
                sg.Checkbox("Display Broadcast", key="display_network",
                            font=(settings.FONT, text_size),
                            expand_x=True,
                            default=current_settings.get("display_network", False)),
                sg.Checkbox("Display Odds", key="display_odds",
                            font=(settings.FONT, text_size),
                            expand_x=True,
                            default=current_settings.get("display_odds", False)),
                sg.Checkbox("Display Series Info", key="display_series",
                            font=(settings.FONT, text_size),
                            expand_x=True,
                            default=current_settings.get("display_series", False)),
            ],
            [
                sg.Checkbox("Display Date Ended", key="display_date_ended",
                            font=(settings.FONT, text_size),
                            expand_x=True,
                            default=current_settings.get("display_date_ended", False)),
                sg.Checkbox("Always Get Logos when starting", key="always_get_logos",
                            font=(settings.FONT, text_size),
                            expand_x=True,
                            default=current_settings.get("always_get_logos", False)),
                sg.Checkbox("Prioritize Playing team(s)", key="prioritize_playing_team",
                            font=(settings.FONT, text_size),
                            expand_x=True,
                            default=current_settings.get("prioritize_playing_team", False)),
            ],
            # Row containing "Change Font" label
            [sg.Text("Change Font:", font=(settings.FONT, bottom_label_size)),
             sg.Text("", font=(settings.FONT, message_size), key="font_message", text_color='red'),
             ],

            # Adding the checkboxes using the font
            *[
                [sg.Checkbox(f, key=f"font_{f}", font=(f, message_size), expand_x=True,
                             default=(f == current_settings["FONT"])) for f in row]
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
                 [sg.Text("MLB Settings", font=(settings.FONT, bottom_label_size), expand_x=True)],
                 [sg.Checkbox("Display Last Pitch", key="display_last_pitch",
                              size=(checkbox_width, checkbox_height),
                              font=(settings.FONT, checkbox_size), expand_x=True,
                              default=current_settings.get("display_last_pitch", False))],
                 [sg.Checkbox("Display Play Description", key="display_play_description",
                              size=(checkbox_width, checkbox_height),
                              font=(settings.FONT, checkbox_size),
                              default=current_settings.get("display_play_description", False))],
                 [sg.Checkbox("Display Bases", key="display_bases",
                              size=(checkbox_width, checkbox_height),
                              font=(settings.FONT, checkbox_size), expand_x=True,
                              default=current_settings.get("display_bases", False))],
                 [sg.Checkbox("Display Count", key="display_balls_strikes",
                              size=(checkbox_width, checkbox_height),
                              font=(settings.FONT, checkbox_size), expand_x=True,
                              default=current_settings.get("display_balls_strikes", False))],
                 [sg.Checkbox("Display Hits/Errors", key="display_hits_errors",
                              size=(checkbox_width, checkbox_height),
                              font=(settings.FONT, checkbox_size), expand_x=True,
                              default=current_settings.get("display_hits_errors", False))],
                 [sg.Checkbox("Display Pitcher/Batter", key="display_pitcher_batter",
                              size=(checkbox_width, checkbox_height),
                              font=(settings.FONT, checkbox_size), expand_x=True,
                              default=current_settings.get("display_pitcher_batter", False))],
                 [sg.Checkbox("Display Inning", key="display_inning",
                              size=(checkbox_width, checkbox_height),
                              font=(settings.FONT, checkbox_size), expand_x=True,
                              default=current_settings.get("display_inning", False))],
                 [sg.Checkbox("Display Outs", key="display_outs",
                              size=(checkbox_width, checkbox_height),
                              font=(settings.FONT, checkbox_size), expand_x=True,
                              default=current_settings.get("display_outs", False))],
             ], expand_x=True, vertical_alignment='top'),
             sg.Column([
                 [sg.Text("NBA Settings", font=(settings.FONT, bottom_label_size), expand_x=True)],
                 [sg.Checkbox("Display Timeouts", key="display_nba_timeouts",
                              size=(checkbox_width, checkbox_height),
                              font=(settings.FONT, checkbox_size), expand_x=True,
                              default=current_settings.get("display_nba_timeouts", False))],
                 [sg.Checkbox("Display Bonus", key="display_nba_bonus", size=(checkbox_width, checkbox_height),
                              font=(settings.FONT, checkbox_size), expand_x=True,
                              default=current_settings.get("display_nba_bonus", False))],
                 [sg.Checkbox("Display Clock", key="display_nba_clock",
                              size=(checkbox_width, checkbox_height),
                              font=(settings.FONT, checkbox_size), expand_x=True,
                              default=current_settings.get("display_nba_clock", False))],
                 [sg.Checkbox("Display Shooting Stats", key="display_nba_shooting",
                              size=(checkbox_width, checkbox_height),
                              font=(settings.FONT, checkbox_size), expand_x=True,
                              default=current_settings.get("display_nba_shooting", False))],
             ], expand_x=True, vertical_alignment='top'),
             sg.Column([
                 [sg.Text("NHL Settings", font=(settings.FONT, bottom_label_size), expand_x=True)],
                 [sg.Checkbox("Display Shots On Goal", key="display_nhl_sog",
                              size=(checkbox_width, checkbox_height),
                              font=(settings.FONT, checkbox_size), expand_x=True,
                              default=current_settings.get("display_nhl_sog", False))],
                 [sg.Checkbox("Display Power Play", key="display_nhl_power_play",
                              size=(checkbox_width, checkbox_height),
                              font=(settings.FONT, checkbox_size), expand_x=True,
                              default=current_settings.get("display_nhl_power_play", False))],
                 [sg.Checkbox("Display Clock", key="display_nhl_clock",
                              size=(checkbox_width, checkbox_height),
                              font=(settings.FONT, checkbox_size), expand_x=True,
                              default=current_settings.get("display_nhl_clock", False))],
             ], expand_x=True, vertical_alignment='top'),
             sg.Column([
                 [sg.Text("NFL Settings", font=(settings.FONT, bottom_label_size), expand_x=True)],
                 [sg.Checkbox("Display Timeouts", key="display_nfl_timeouts",
                              size=(checkbox_width, checkbox_height),
                              font=(settings.FONT, checkbox_size), expand_x=True,
                              default=current_settings.get("display_nfl_timeouts", False))],
                 [sg.Checkbox("Display RedZone", key="display_nfl_redzone",
                              size=(checkbox_width, checkbox_height),
                              font=(settings.FONT, checkbox_size), expand_x=True,
                              default=current_settings.get("display_nfl_redzone", False))],
                 [sg.Checkbox("Display Possession", key="display_nfl_possession",
                              size=(checkbox_width, checkbox_height),
                              font=(settings.FONT, checkbox_size), expand_x=True,
                              default=current_settings.get("display_nfl_possession", False))],
                 [sg.Checkbox("Display Down/Yardage", key="display_nfl_down",
                              size=(checkbox_width, checkbox_height),
                              font=(settings.FONT, checkbox_size), expand_x=True,
                              default=current_settings.get("display_nfl_down", False))],
                 [sg.Checkbox("Display Clock", key="display_nfl_clock",
                              size=(checkbox_width, checkbox_height),
                              font=(settings.FONT, checkbox_size), expand_x=True,
                              default=current_settings.get("display_nfl_clock", False))],
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
        [sg.Push(), sg.Text("Settings", font=(settings.FONT, title_size, "underline")), sg.Push()],
        [general_setting_layout],
        [specific_settings_layout],
        [[sg.VPush()],
         sg.Push(),
         sg.Text("", font=(settings.FONT, button_size), key="confirmation_message", text_color='Green'),
         sg.Push(),
         [sg.VPush()],
         ],
        [[sg.VPush()],
         sg.Push(),
         sg.Button("Save", font=(settings.FONT, button_size)),
         sg.Button("Back", font=(settings.FONT, button_size)),
         sg.Push(),
         ],
    ]
    return layout
