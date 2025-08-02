"""GUI Layout for changing scoreboard settings in main menu."""

import FreeSimpleGUI as Sg  # ignore

import settings
from helper_functions.main_menu_helpers import read_settings_from_file


def create_settings_layout(window_width: int) -> list:
    """Create General User Interface layout for changing settings.

    :param window_width: The width of the screen being used
    "param league: The sports league of the team that the user wants to add
    :return layout: List of elements and how the should be displayed
    """
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

    general_setting_layout = Sg.Frame(
        "",
        [
            # Row containing "Live Data Delay", Input, Live Data Message, and Delay Text
            [Sg.Push(),
                Sg.Column(
                    [
                        [Sg.Text("Live Data Delay:", font=(settings.FONT, top_label_size)),
                         Sg.Spin([str(i) for i in range(1000)], key="LIVE_DATA_DELAY", enable_events=True,
                                 size=(text_input_size, 1),
                                 font=("Arial", text_size),
                                 initial_value=str(current_settings.get("LIVE_DATA_DELAY", 0))),
                         Sg.Text("seconds", font=(settings.FONT, message_size), expand_x=True, pad=(0, 0)),
                         ],
                        [
                            Sg.Push(),
                            Sg.Text("Delay to display live data", key="LIVE_DATA_DELAY_MESSAGE",
                                    font=(settings.FONT, message_size, "italic")),
                            Sg.Push(),
                        ],
                    ],
            ),
                Sg.Column(
                    [
                        [Sg.Text("Display Timer (LIVE):", font=(settings.FONT, top_label_size)),
                         Sg.Spin([str(i) for i in range(1000)], key="DISPLAY_PLAYING_TIMER", enable_events=True,
                                 size=(text_input_size, 1),
                                 font=("Arial", text_size),
                                 initial_value=str(current_settings.get("DISPLAY_PLAYING_TIMER", 0))),
                         Sg.Text("seconds", font=(settings.FONT, message_size), expand_x=True, pad=(0, 0)),
                         ],
                        [
                            Sg.Push(),
                            Sg.Text("How often to Display each team when teams are playing",
                                    key="DISPLAY_PLAYING_TIMER_MESSAGE",
                                    font=(settings.FONT, message_size, "italic")),
                            Sg.Push(),
                        ],
                    ],
            ),
                Sg.Push(),
            ],
            [
                Sg.Push(),
                Sg.Column(
                    [
                        [Sg.Text("Fetch Timer:", font=(settings.FONT, top_label_size)),
                         Sg.Spin([str(i) for i in range(1000)], key="FETCH_DATA_NOT_PLAYING_TIMER", enable_events=True,
                                 size=(text_input_size, 1),
                                 font=("Arial", text_size),
                                 initial_value=str(current_settings.get("FETCH_DATA_NOT_PLAYING_TIMER", 0))),
                         Sg.Text("seconds", font=(settings.FONT, message_size), expand_x=True, pad=(0, 0)),
                         ],
                        [
                            Sg.Push(),
                            Sg.Text("How often to get data when no team is playing",
                                    key="FETCH_DATA_NOT_PLAYING_TIMER_MESSAGE",
                                    font=(settings.FONT, message_size, "italic")),
                            Sg.Push(),
                        ],
                    ],
                ),
                Sg.Column(
                    [
                        [Sg.Text("Display Timer:", font=(settings.FONT, top_label_size)),
                         Sg.Spin([str(i) for i in range(1000)], key="DISPLAY_NOT_PLAYING_TIMER", enable_events=True,
                                 size=(text_input_size, 1),
                                 font=("Arial", text_size),
                                 initial_value=str(current_settings.get("DISPLAY_NOT_PLAYING_TIMER", 0))),
                         Sg.Text("seconds", font=(settings.FONT, message_size), expand_x=True, pad=(0, 0)),
                         ],
                        [
                            Sg.Push(),
                            Sg.Text("How often to Display each team when no team is playing",
                                    key="DISPLAY_NOT_PLAYING_TIMER_MESSAGE",
                                    font=(settings.FONT, message_size, "italic")),
                            Sg.Push(),
                        ],
                    ],
                ),
                Sg.Column(
                    [
                        [Sg.Text("Display Time:", font=(settings.FONT, top_label_size)),
                         Sg.Spin([str(i) for i in range(1000)], key="HOW_LONG_TO_DISPLAY_TEAM", enable_events=True,
                                 size=(text_input_size, 1),
                                 font=("Arial", text_size),
                                 initial_value=str(current_settings.get("HOW_LONG_TO_DISPLAY_TEAM", 0))),
                         Sg.Text("days", font=(settings.FONT, message_size), expand_x=True, pad=(0, 0)),
                         ],
                        [
                            Sg.Push(),
                            Sg.Text("How long to display team info when finished",
                                    key="HOW_LONG_TO_DISPLAY_TEAM_MESSAGE",
                                    font=(settings.FONT, message_size, "italic")),
                            Sg.Push(),
                        ],
                    ],
                ),
                Sg.Push(),
            ],
            [Sg.Text("", font=(settings.FONT, bottom_label_size))],
            [
                Sg.Checkbox("Display Records", key="display_records",
                            font=(settings.FONT, text_size),
                            expand_x=True,
                            default=current_settings.get("display_records", False)),
                Sg.Checkbox("Display Venue", key="display_venue",
                            font=(settings.FONT, text_size),
                            expand_x=True,
                            default=current_settings.get("display_venue", False)),
                Sg.Checkbox("Display Broadcast", key="display_network",
                            font=(settings.FONT, text_size),
                            expand_x=True,
                            default=current_settings.get("display_network", False)),
                Sg.Checkbox("Display Odds", key="display_odds",
                            font=(settings.FONT, text_size),
                            expand_x=True,
                            default=current_settings.get("display_odds", False)),
                Sg.Checkbox("Display Series Info", key="display_series",
                            font=(settings.FONT, text_size),
                            expand_x=True,
                            default=current_settings.get("display_series", False)),
            ],
            [
                Sg.Checkbox("Display Date Ended", key="display_date_ended",
                            font=(settings.FONT, text_size),
                            expand_x=True,
                            default=current_settings.get("display_date_ended", False)),
                Sg.Checkbox("Display Playoff/Championship Image", key="display_playoff_championship_image",
                            font=(settings.FONT, text_size),
                            expand_x=True,
                            default=current_settings.get("display_playoff_championship_image", False)),
                Sg.Checkbox("Download/Resize Images when Starting", key="always_get_logos",
                            font=(settings.FONT, text_size),
                            expand_x=True,
                            default=current_settings.get("always_get_logos", False)),
                Sg.Checkbox("Prioritize Playing Team(s)", key="prioritize_playing_team",
                            font=(settings.FONT, text_size),
                            expand_x=True,
                            default=current_settings.get("prioritize_playing_team", False)),
                Sg.Checkbox("Prioritize Playoff/Championship Image Over Broadcast",
                            key="prioritize_playoff_championship_image",
                            font=(settings.FONT, text_size),
                            expand_x=True,
                            default=current_settings.get("prioritize_playoff_championship_image", False)),
            ],
        ],
        expand_x=True,
        relief=Sg.RELIEF_SOLID,
        border_width=2,
        pad=(0, button_size),
    )

    specific_settings_layout = Sg.Frame(
        "",
        [
            [Sg.Push(),
             Sg.Column([
                 [Sg.Text("MLB Settings", font=(settings.FONT, bottom_label_size), expand_x=True)],
                 [Sg.Checkbox("Display Last Pitch", key="display_last_pitch",
                              size=(checkbox_width, checkbox_height),
                              font=(settings.FONT, checkbox_size), expand_x=True,
                              default=current_settings.get("display_last_pitch", False))],
                 [Sg.Checkbox("Display Play Description", key="display_play_description",
                              size=(checkbox_width, checkbox_height),
                              font=(settings.FONT, checkbox_size),
                              default=current_settings.get("display_play_description", False))],
                 [Sg.Checkbox("Display Bases", key="display_bases",
                              size=(checkbox_width, checkbox_height),
                              font=(settings.FONT, checkbox_size), expand_x=True,
                              default=current_settings.get("display_bases", False))],
                 [Sg.Checkbox("Display Count", key="display_balls_strikes",
                              size=(checkbox_width, checkbox_height),
                              font=(settings.FONT, checkbox_size), expand_x=True,
                              default=current_settings.get("display_balls_strikes", False))],
                 [Sg.Checkbox("Display Hits/Errors", key="display_hits_errors",
                              size=(checkbox_width, checkbox_height),
                              font=(settings.FONT, checkbox_size), expand_x=True,
                              default=current_settings.get("display_hits_errors", False))],
                 [Sg.Checkbox("Display Pitcher/Batter", key="display_pitcher_batter",
                              size=(checkbox_width, checkbox_height),
                              font=(settings.FONT, checkbox_size), expand_x=True,
                              default=current_settings.get("display_pitcher_batter", False))],
                 [Sg.Checkbox("Display Inning", key="display_inning",
                              size=(checkbox_width, checkbox_height),
                              font=(settings.FONT, checkbox_size), expand_x=True,
                              default=current_settings.get("display_inning", False))],
                 [Sg.Checkbox("Display Outs", key="display_outs",
                              size=(checkbox_width, checkbox_height),
                              font=(settings.FONT, checkbox_size), expand_x=True,
                              default=current_settings.get("display_outs", False))],
             ], expand_x=True, vertical_alignment="top"),
             Sg.Column([
                 [Sg.Text("NBA Settings", font=(settings.FONT, bottom_label_size), expand_x=True)],
                 [Sg.Checkbox("Display Timeouts", key="display_nba_timeouts",
                              size=(checkbox_width, checkbox_height),
                              font=(settings.FONT, checkbox_size), expand_x=True,
                              default=current_settings.get("display_nba_timeouts", False))],
                 [Sg.Checkbox("Display Bonus", key="display_nba_bonus", size=(checkbox_width, checkbox_height),
                              font=(settings.FONT, checkbox_size), expand_x=True,
                              default=current_settings.get("display_nba_bonus", False))],
                 [Sg.Checkbox("Display Clock", key="display_nba_clock",
                              size=(checkbox_width, checkbox_height),
                              font=(settings.FONT, checkbox_size), expand_x=True,
                              default=current_settings.get("display_nba_clock", False))],
                 [Sg.Checkbox("Display Shooting Stats", key="display_nba_shooting",
                              size=(checkbox_width, checkbox_height),
                              font=(settings.FONT, checkbox_size), expand_x=True,
                              default=current_settings.get("display_nba_shooting", False))],
                [Sg.Checkbox("Display play by play", key="display_nba_play_by_play",
                              size=(checkbox_width, checkbox_height),
                              font=(settings.FONT, checkbox_size), expand_x=True,
                              default=current_settings.get("display_nba_play_by_play", False))],
             ], expand_x=True, vertical_alignment="top"),
             Sg.Column([
                 [Sg.Text("NHL Settings", font=(settings.FONT, bottom_label_size), expand_x=True)],
                 [Sg.Checkbox("Display Shots On Goal", key="display_nhl_sog",
                              size=(checkbox_width, checkbox_height),
                              font=(settings.FONT, checkbox_size), expand_x=True,
                              default=current_settings.get("display_nhl_sog", False))],
                 [Sg.Checkbox("Display Power Play", key="display_nhl_power_play",
                              size=(checkbox_width, checkbox_height),
                              font=(settings.FONT, checkbox_size), expand_x=True,
                              default=current_settings.get("display_nhl_power_play", False))],
                 [Sg.Checkbox("Display Clock", key="display_nhl_clock",
                              size=(checkbox_width, checkbox_height),
                              font=(settings.FONT, checkbox_size), expand_x=True,
                              default=current_settings.get("display_nhl_clock", False))],
                 [Sg.Checkbox("Display play by play", key="display_nhl_play_by_play",
                               size=(checkbox_width, checkbox_height),
                               font=(settings.FONT, checkbox_size), expand_x=True,
                               default=current_settings.get("display_nhl_play_by_play", False))],
             ], expand_x=True, vertical_alignment="top"),
             Sg.Column([
                 [Sg.Text("NFL Settings", font=(settings.FONT, bottom_label_size), expand_x=True)],
                 [Sg.Checkbox("Display Timeouts", key="display_nfl_timeouts",
                              size=(checkbox_width, checkbox_height),
                              font=(settings.FONT, checkbox_size), expand_x=True,
                              default=current_settings.get("display_nfl_timeouts", False))],
                 [Sg.Checkbox("Display RedZone", key="display_nfl_redzone",
                              size=(checkbox_width, checkbox_height),
                              font=(settings.FONT, checkbox_size), expand_x=True,
                              default=current_settings.get("display_nfl_redzone", False))],
                 [Sg.Checkbox("Display Possession", key="display_nfl_possession",
                              size=(checkbox_width, checkbox_height),
                              font=(settings.FONT, checkbox_size), expand_x=True,
                              default=current_settings.get("display_nfl_possession", False))],
                 [Sg.Checkbox("Display Down/Yardage", key="display_nfl_down",
                              size=(checkbox_width, checkbox_height),
                              font=(settings.FONT, checkbox_size), expand_x=True,
                              default=current_settings.get("display_nfl_down", False))],
                 [Sg.Checkbox("Display Clock", key="display_nfl_clock",
                              size=(checkbox_width, checkbox_height),
                              font=(settings.FONT, checkbox_size), expand_x=True,
                              default=current_settings.get("display_nfl_clock", False))],
             ], expand_x=True, vertical_alignment="top"),
             Sg.Push(),
             ],
        ],
        expand_x=True,
        relief=Sg.RELIEF_SOLID,
        border_width=2,
        pad=(0, 0),
    )

    return [
        [Sg.Push(), Sg.Text("Settings", font=(settings.FONT, title_size, "underline")), Sg.Push()],
        [general_setting_layout],
        [specific_settings_layout],
        [[Sg.VPush()],
         Sg.Push(),
         Sg.Text("", font=(settings.FONT, button_size), key="confirmation_message", text_color="Green"),
         Sg.Push(),
         [Sg.VPush()],
         ],
        [[Sg.VPush()],
         Sg.Push(),
         Sg.Button("Save", font=(settings.FONT, button_size)),
         Sg.Button("Back", font=(settings.FONT, button_size)),
         Sg.Push(),
         ],
    ]
