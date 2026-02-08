"""GUI Layout for changing scoreboard settings in main menu."""
from __future__ import annotations

import FreeSimpleGUI as Sg  # ignore

import settings
from constants import colors, messages, ui_keys
from constants.sizing_utils import (
    calculate_button_size,
    calculate_message_size,
    calculate_text_size,
    calculate_title_size,
    get_responsive_scale,
)


def create_settings_layout(window_width: int) -> list:
    """Create General User Interface layout for changing settings."""
    color = "lightgray"
    _, scale = get_responsive_scale(window_width)

    title_size = calculate_title_size(scale)
    checkbox_width = min(30, max(10, int(25 * scale)))
    checkbox_height = min(100, max(2, int(2 * scale)))
    message_size = calculate_message_size(scale, min_size=8, base_multiplier=14)
    button_size = calculate_button_size(scale, min_size=20, base_multiplier=40)
    text_input_size = min(100, max(4, int(6 * scale)))
    top_label_size = min(100, max(14, int(28 * scale)))
    bottom_label_size = min(100, max(15, int(32 * scale)))
    checkbox_size = min(100, max(10, int(20 * scale)))
    text_size = calculate_text_size(scale, min_size=12, base_multiplier=24)

    current_settings = settings.read_settings()

    general_setting_layout = Sg.Frame(
        "",
        [
            [
                Sg.Text(
                    messages.CHANGE_FUNCTIONALITY,
                    font=(settings.FONT, bottom_label_size, "underline"),
                    pad=(0, button_size),
                    background_color=color,
                ),
                Sg.Push(background_color=color),
            ],
            [
                Sg.Push(background_color=color),
                Sg.Column(
                    [
                        [
                            Sg.Text(
                                "Display Timer:",
                                font=(settings.FONT, top_label_size),
                                background_color=color,
                            ),
                            Sg.Spin(
                                [str(i) for i in range(1000)],
                                key=ui_keys.DISPLAY_NOT_PLAYING_TIMER,
                                enable_events=True,
                                size=(text_input_size, 1),
                                font=("Arial", text_size),
                                initial_value=str(current_settings.get("DISPLAY_NOT_PLAYING_TIMER", 0)),
                            ),
                            Sg.Text(
                                "seconds",
                                font=(settings.FONT, message_size),
                                pad=(0, 0),
                                background_color=color,
                            ),
                        ],
                        [
                            Sg.Push(background_color=color),
                            Sg.Text(
                                "How often to display each team when no team has live games",
                                key=ui_keys.DISPLAY_NOT_PLAYING_TIMER_MESSAGE,
                                font=(settings.FONT, message_size, "italic"),
                                background_color=color,
                            ),
                            Sg.Push(background_color=color),
                        ],
                    ],
                    background_color=color,
                ),
                Sg.Column(
                    [
                        [
                            Sg.Text(
                                "Display Timer (LIVE):",
                                font=(settings.FONT, top_label_size),
                                background_color=color,
                            ),
                            Sg.Spin(
                                [str(i) for i in range(1000)],
                                key=ui_keys.DISPLAY_PLAYING_TIMER,
                                enable_events=True,
                                size=(text_input_size, 1),
                                font=("Arial", text_size),
                                initial_value=str(current_settings.get("DISPLAY_PLAYING_TIMER", 0)),
                            ),
                            Sg.Text(
                                "seconds",
                                font=(settings.FONT, message_size),
                                pad=(0, 0),
                                background_color=color,
                            ),
                        ],
                        [
                            Sg.Push(background_color=color),
                            Sg.Text(
                                "How often to display each team when multiple teams have live games",
                                key=ui_keys.DISPLAY_PLAYING_TIMER_MESSAGE,
                                font=(settings.FONT, message_size, "italic"),
                                background_color=color,
                            ),
                            Sg.Push(background_color=color),
                        ],
                    ],
                    background_color=color,
                ),
                Sg.Push(background_color=color),
            ],
            [
                Sg.Push(background_color=color),
                Sg.Column(
                    [
                        [
                            Sg.Text(
                                "Live Data Delay:",
                                font=(settings.FONT, top_label_size),
                                background_color=color,
                            ),
                            Sg.Spin(
                                [str(i) for i in range(1000)],
                                key=ui_keys.LIVE_DATA_DELAY,
                                enable_events=True,
                                size=(text_input_size, 1),
                                font=("Arial", text_size),
                                initial_value=str(current_settings.get("LIVE_DATA_DELAY", 0)),
                            ),
                            Sg.Text(
                                "seconds",
                                font=(settings.FONT, message_size),
                                pad=(0, 0),
                                background_color=color,
                            ),
                        ],
                        [
                            Sg.Push(background_color=color),
                            Sg.Text(
                                "How many seconds live game updates are behind (for TV sync or spoilers)",
                                key=ui_keys.LIVE_DATA_DELAY_MESSAGE,
                                font=(settings.FONT, message_size, "italic"),
                                background_color=color,
                            ),
                            Sg.Push(background_color=color),
                        ],
                    ],
                    background_color=color,
                ),
                Sg.Column(
                    [
                        [
                            Sg.Text(
                                "Display Time:",
                                font=(settings.FONT, top_label_size),
                                background_color=color,
                            ),
                            Sg.Spin(
                                [str(i) for i in range(1000)],
                                key=ui_keys.HOW_LONG_TO_DISPLAY_TEAM,
                                enable_events=True,
                                size=(text_input_size, 1),
                                font=("Arial", text_size),
                                initial_value=str(current_settings.get("HOW_LONG_TO_DISPLAY_TEAM", 0)),
                            ),
                            Sg.Text(
                                "days",
                                font=(settings.FONT, message_size),
                                pad=(0, 0),
                                background_color=color,
                            ),
                        ],
                        [
                            Sg.Push(background_color=color),
                            Sg.Text(
                                "How long to display game info once finished (if not replaced by new game info)",
                                key=ui_keys.HOW_LONG_TO_DISPLAY_TEAM_MESSAGE,
                                background_color=color,
                                font=(settings.FONT, message_size, "italic"),
                            ),
                            Sg.Push(background_color=color),
                        ],
                    ],
                    background_color=color,
                ),
                Sg.Push(background_color=color),
            ],
            [
                Sg.Text("", font=(settings.FONT, bottom_label_size), background_color=color),
            ],
            [
                Sg.Column(
                    [
                        [
                            Sg.Checkbox(
                                messages.REDOWNLOAD_IMAGES,
                                key=ui_keys.ALWAYS_GET_LOGOS,
                                font=(settings.FONT, top_label_size),
                                background_color=color,
                                checkbox_color=colors.INFO_WHITE,
                                default=current_settings.get("always_get_logos", False),
                            ),
                        ],
                        [
                            Sg.Text(
                                "\tOnly do this only if a team's logo has changed\n",
                                font=(settings.FONT, message_size),
                                background_color=color,
                            ),
                        ],
                    ],
                    justification="left",
                    background_color=color,
                ),
            ],
            [
                Sg.Column(
                    [
                        [
                            Sg.Checkbox(
                                "Prioritize Playing Team(s)",
                                key=ui_keys.PRIORITIZE_PLAYING_TEAM,
                                font=(settings.FONT, top_label_size),
                                background_color=color,
                                checkbox_color=colors.INFO_WHITE,
                                default=current_settings.get("prioritize_playing_team", False),
                            ),
                        ],
                        [
                            Sg.Text(
                                "\tWhen enabled, displays only teams with live games.",
                                font=(settings.FONT, message_size),
                                background_color=color,
                            ),
                        ],
                        [
                            Sg.Text(
                                "\tOther teams will display once all live games are finished.\n",
                                font=(settings.FONT, message_size),
                                background_color=color,
                            ),
                        ],
                    ],
                    justification="left",
                    background_color=color,
                ),
            ],
            [
                Sg.Column(
                    [
                        [
                            Sg.Checkbox(
                                "Auto Update",
                                key=ui_keys.AUTO_UPDATE,
                                font=(settings.FONT, top_label_size),
                                background_color=color,
                                checkbox_color=colors.INFO_WHITE,
                                default=current_settings.get("auto_update", False),
                            ),
                        ],
                        [
                            Sg.Text(
                                "\tThis will automatically check for updates to always be on the latest version",
                                font=(settings.FONT, message_size),
                                background_color=color,
                            ),
                        ],
                        [
                            Sg.Text(
                                "\tYou can restore from updates via button on main screen",
                                font=(settings.FONT, message_size),
                                background_color=color,
                            ),
                        ],
                    ],
                    justification="left",
                    background_color=color,
                ),
            ],
        ],
        element_justification="center",
        expand_x=True,
        border_width=0,
        background_color=color,
    )

    general_display_layout = Sg.Frame(
        "",
        [
            [
                Sg.Text(
                    messages.CHOOSE_WHAT_DISPLAYS,
                    font=(settings.FONT, bottom_label_size, "underline"),
                    background_color=color,
                    pad=(0, button_size),
                ),
                Sg.Push(background_color=color),
            ],
            [
                Sg.Column(
                    [
                        [
                            Sg.Checkbox(
                                "Teams Win-Loss Records",
                                key=ui_keys.DISPLAY_RECORDS,
                                font=(settings.FONT, top_label_size),
                                background_color=color,
                                default=current_settings.get("display_records", False),
                                checkbox_color=colors.INFO_WHITE,
                            ),
                        ],
                        [
                            Sg.Text(
                                messages.DISPLAYED_ALWAYS,
                                font=(settings.FONT, message_size),
                                background_color=color,
                            ),
                        ],
                        [
                            Sg.Checkbox(
                                "Game Venue",
                                key=ui_keys.DISPLAY_VENUE,
                                font=(settings.FONT, top_label_size),
                                background_color=color,
                                default=current_settings.get("display_venue", False),
                                checkbox_color=colors.INFO_WHITE,
                            ),
                        ],
                        [
                            Sg.Text(
                                messages.DISPLAYED_BEFORE,
                                font=(settings.FONT, message_size),
                                background_color=color,
                            ),
                        ],
                        [
                            Sg.Checkbox(
                                "Gambling Odds",
                                key=ui_keys.DISPLAY_ODDS,
                                font=(settings.FONT, top_label_size),
                                background_color=color,
                                default=current_settings.get("display_odds", False),
                                checkbox_color=colors.INFO_WHITE,
                            ),
                        ],
                        [
                            Sg.Text(
                                messages.DISPLAYED_BEFORE,
                                font=(settings.FONT, message_size),
                                background_color=color,
                            ),
                        ],
                        [
                            Sg.Checkbox(
                                "Playoff/Championship Image",
                                key=ui_keys.DISPLAY_PLAYOFF_CHAMPIONSHIP_IMAGE,
                                font=(settings.FONT, text_size),
                                background_color=color,
                                default=current_settings.get("display_playoff_championship_image", False),
                                checkbox_color=colors.INFO_WHITE,
                            ),
                        ],
                        [
                            Sg.Text(
                                "\tDisplays special image if the game is playoff/championship",
                                font=(settings.FONT, message_size),
                                background_color=color,
                            ),
                        ],
                    ],
                    element_justification="left",
                    background_color=color,
                ),
                Sg.Column(
                    [
                        [
                            Sg.Checkbox(
                                "Series Info",
                                key=ui_keys.DISPLAY_SERIES,
                                font=(settings.FONT, top_label_size),
                                background_color=color,
                                default=current_settings.get("display_series", False),
                                checkbox_color=colors.INFO_WHITE,
                            ),
                        ],
                        [
                            Sg.Text(
                                "\tDisplays only if applicable and after game ends",
                                font=(settings.FONT, message_size),
                                background_color=color,
                            ),
                        ],
                        [
                            Sg.Checkbox(
                                "Player's Game Stats",
                                key=ui_keys.DISPLAY_PLAYER_STATS,
                                font=(settings.FONT, top_label_size),
                                background_color=color,
                                default=current_settings.get("display_player_stats", False),
                                checkbox_color=colors.INFO_WHITE,
                            ),
                        ],
                        [
                            Sg.Text(
                                "\tDisplays only after game ends",
                                font=(settings.FONT, message_size),
                                background_color=color,
                            ),
                        ],
                        [
                            Sg.Checkbox(
                                "Date Game Ended",
                                key=ui_keys.DISPLAY_DATE_ENDED,
                                font=(settings.FONT, top_label_size),
                                background_color=color,
                                default=current_settings.get("display_date_ended", False),
                                checkbox_color=colors.INFO_WHITE,
                            ),
                        ],
                        [
                            Sg.Text(
                                "\tDisplays only after game ends",
                                font=(settings.FONT, message_size),
                                background_color=color,
                            ),
                        ],
                        [
                            Sg.Checkbox(
                                "Display Broadcast",
                                key=ui_keys.DISPLAY_NETWORK,
                                font=(settings.FONT, top_label_size),
                                background_color=color,
                                default=current_settings.get("display_network", False),
                                checkbox_color=colors.INFO_WHITE,
                            ),
                        ],
                        [
                            Sg.Text(
                                messages.DISPLAYED_APPLICABLE,
                                font=(settings.FONT, message_size),
                                background_color=color,
                            ),
                        ],
                    ],
                    element_justification="left",
                    background_color=color,
                ),
            ],
        ],
        element_justification="center",
        expand_x=True,
        border_width=0,
        background_color=color,
    )

    specific_settings_layout = Sg.Frame(
        "",
        [
            [
                Sg.Text(
                    messages.CHANGE_SPORT_DISPLAY,
                    font=(settings.FONT, bottom_label_size, "underline"),
                    background_color=color,
                    pad=(0, button_size),
                ),
                Sg.Push(background_color=color),
            ],
            [
                Sg.Push(background_color=color),
                Sg.Column(
                    [
                        [
                            Sg.Push(background_color=color),
                            Sg.Text("MLB", font=(settings.FONT, bottom_label_size), background_color=color),
                            Sg.Push(background_color=color),
                        ],
                        [
                            Sg.Checkbox(
                                "Last Pitch",
                                key=ui_keys.DISPLAY_LAST_PITCH,
                                background_color=color,
                                size=(checkbox_width, checkbox_height),
                                font=(settings.FONT, checkbox_size),
                                default=current_settings.get("display_last_pitch", False),
                                checkbox_color=colors.INFO_WHITE,
                            ),
                        ],
                        [
                            Sg.Checkbox(
                                "Play Description",
                                key=ui_keys.DISPLAY_PLAY_DESCRIPTION,
                                background_color=color,
                                size=(checkbox_width, checkbox_height),
                                font=(settings.FONT, checkbox_size),
                                default=current_settings.get("display_play_description", False),
                                checkbox_color=colors.INFO_WHITE,
                            ),
                        ],
                        [
                            Sg.Checkbox(
                                "Bases",
                                key=ui_keys.DISPLAY_BASES,
                                background_color=color,
                                size=(checkbox_width, checkbox_height),
                                font=(settings.FONT, checkbox_size),
                                default=current_settings.get("display_bases", False),
                                checkbox_color=colors.INFO_WHITE,
                            ),
                        ],
                        [
                            Sg.Checkbox(
                                "Count",
                                key=ui_keys.DISPLAY_BALLS_STRIKES,
                                background_color=color,
                                size=(checkbox_width, checkbox_height),
                                font=(settings.FONT, checkbox_size),
                                default=current_settings.get("display_balls_strikes", False),
                                checkbox_color=colors.INFO_WHITE,
                            ),
                        ],
                        [
                            Sg.Checkbox(
                                "Hits/Errors",
                                key=ui_keys.DISPLAY_HITS_ERRORS,
                                background_color=color,
                                size=(checkbox_width, checkbox_height),
                                font=(settings.FONT, checkbox_size),
                                default=current_settings.get("display_hits_errors", False),
                                checkbox_color=colors.INFO_WHITE,
                            ),
                        ],
                        [
                            Sg.Checkbox(
                                "Pitcher/Batter",
                                key=ui_keys.DISPLAY_PITCHER_BATTER,
                                background_color=color,
                                size=(checkbox_width, checkbox_height),
                                font=(settings.FONT, checkbox_size),
                                default=current_settings.get("display_pitcher_batter", False),
                                checkbox_color=colors.INFO_WHITE,
                            ),
                        ],
                        [
                            Sg.Checkbox(
                                "Inning",
                                key=ui_keys.DISPLAY_INNING,
                                background_color=color,
                                size=(checkbox_width, checkbox_height),
                                font=(settings.FONT, checkbox_size),
                                default=current_settings.get("display_inning", False),
                                checkbox_color=colors.INFO_WHITE,
                            ),
                        ],
                        [
                            Sg.Checkbox(
                                "Outs",
                                key=ui_keys.DISPLAY_OUTS,
                                background_color=color,
                                size=(checkbox_width, checkbox_height),
                                font=(settings.FONT, checkbox_size),
                                default=current_settings.get("display_outs", False),
                                checkbox_color=colors.INFO_WHITE,
                            ),
                        ],
                    ],
                    vertical_alignment="top",
                    justification="center",
                    background_color=color,
                ),
                Sg.Column(
                    [
                        [
                            Sg.Push(background_color=color),
                            Sg.Text("NBA", font=(settings.FONT, bottom_label_size), background_color=color),
                            Sg.Push(background_color=color),
                        ],
                        [
                            Sg.Checkbox(
                                "Timeouts",
                                key=ui_keys.DISPLAY_NBA_TIMEOUTS,
                                size=(checkbox_width, checkbox_height),
                                font=(settings.FONT, checkbox_size),
                                background_color=color,
                                default=current_settings.get("display_nba_timeouts", False),
                                checkbox_color=colors.INFO_WHITE,
                            ),
                        ],
                        [
                            Sg.Checkbox(
                                "Bonus",
                                key=ui_keys.DISPLAY_NBA_BONUS,
                                size=(checkbox_width, checkbox_height),
                                font=(settings.FONT, checkbox_size),
                                background_color=color,
                                default=current_settings.get("display_nba_bonus", False),
                                checkbox_color=colors.INFO_WHITE,
                            ),
                        ],
                        [
                            Sg.Checkbox(
                                "Game Clock",
                                key=ui_keys.DISPLAY_NBA_CLOCK,
                                background_color=color,
                                size=(checkbox_width, checkbox_height),
                                font=(settings.FONT, checkbox_size),
                                default=current_settings.get("display_nba_clock", False),
                                checkbox_color=colors.INFO_WHITE,
                            ),
                        ],
                        [
                            Sg.Checkbox(
                                "Shooting Stats",
                                key=ui_keys.DISPLAY_NBA_SHOOTING,
                                background_color=color,
                                size=(checkbox_width, checkbox_height),
                                font=(settings.FONT, checkbox_size),
                                default=current_settings.get("display_nba_shooting", False),
                                checkbox_color=colors.INFO_WHITE,
                            ),
                        ],
                        [
                            Sg.Checkbox(
                                "Play-by-Play",
                                key=ui_keys.DISPLAY_NBA_PLAY_BY_PLAY,
                                background_color=color,
                                size=(checkbox_width, checkbox_height),
                                font=(settings.FONT, checkbox_size),
                                default=current_settings.get("display_nba_play_by_play", False),
                                checkbox_color=colors.INFO_WHITE,
                            ),
                        ],
                    ],
                    vertical_alignment="top",
                    justification="center",
                    background_color=color,
                ),
                Sg.Column(
                    [
                        [
                            Sg.Push(background_color=color),
                            Sg.Text("NHL", font=(settings.FONT, bottom_label_size), background_color=color),
                            Sg.Push(background_color=color),
                        ],
                        [
                            Sg.Checkbox(
                                "Shots On Goal",
                                key=ui_keys.DISPLAY_NHL_SOG,
                                background_color=color,
                                size=(checkbox_width, checkbox_height),
                                font=(settings.FONT, checkbox_size),
                                default=current_settings.get("display_nhl_sog", False),
                                checkbox_color=colors.INFO_WHITE,
                            ),
                        ],
                        [
                            Sg.Checkbox(
                                "Power Play",
                                key=ui_keys.DISPLAY_NHL_POWER_PLAY,
                                background_color=color,
                                size=(checkbox_width, checkbox_height),
                                font=(settings.FONT, checkbox_size),
                                default=current_settings.get("display_nhl_power_play", False),
                                checkbox_color=colors.INFO_WHITE,
                            ),
                        ],
                        [
                            Sg.Checkbox(
                                "Game Clock",
                                key=ui_keys.DISPLAY_NHL_CLOCK,
                                background_color=color,
                                size=(checkbox_width, checkbox_height),
                                font=(settings.FONT, checkbox_size),
                                default=current_settings.get("display_nhl_clock", False),
                                checkbox_color=colors.INFO_WHITE,
                            ),
                        ],
                        [
                            Sg.Checkbox(
                                "Play-by-Play",
                                key=ui_keys.DISPLAY_NHL_PLAY_BY_PLAY,
                                background_color=color,
                                size=(checkbox_width, checkbox_height),
                                font=(settings.FONT, checkbox_size),
                                default=current_settings.get("display_nhl_play_by_play", False),
                                checkbox_color=colors.INFO_WHITE,
                            ),
                        ],
                    ],
                    vertical_alignment="top",
                    justification="center",
                    background_color=color,
                ),
                Sg.Column(
                    [
                        [
                            Sg.Push(background_color=color),
                            Sg.Text("NFL", font=(settings.FONT, bottom_label_size), background_color=color),
                            Sg.Push(background_color=color),
                        ],
                        [
                            Sg.Checkbox(
                                "Timeouts",
                                key=ui_keys.DISPLAY_NFL_TIMEOUTS,
                                background_color=color,
                                size=(checkbox_width, checkbox_height),
                                font=(settings.FONT, checkbox_size),
                                default=current_settings.get("display_nfl_timeouts", False),
                                checkbox_color=colors.INFO_WHITE,
                            ),
                        ],
                        [
                            Sg.Checkbox(
                                "RedZone",
                                key=ui_keys.DISPLAY_NFL_REDZONE,
                                background_color=color,
                                size=(checkbox_width, checkbox_height),
                                font=(settings.FONT, checkbox_size),
                                default=current_settings.get("display_nfl_redzone", False),
                                checkbox_color=colors.INFO_WHITE,
                            ),
                        ],
                        [
                            Sg.Checkbox(
                                "Possession",
                                key=ui_keys.DISPLAY_NFL_POSSESSION,
                                background_color=color,
                                size=(checkbox_width, checkbox_height),
                                font=(settings.FONT, checkbox_size),
                                default=current_settings.get("display_nfl_possession", False),
                                checkbox_color=colors.INFO_WHITE,
                            ),
                        ],
                        [
                            Sg.Checkbox(
                                "Down/Yardage",
                                key=ui_keys.DISPLAY_NFL_DOWN,
                                background_color=color,
                                size=(checkbox_width, checkbox_height),
                                font=(settings.FONT, checkbox_size),
                                default=current_settings.get("display_nfl_down", False),
                                checkbox_color=colors.INFO_WHITE,
                            ),
                        ],
                        [
                            Sg.Checkbox(
                                "Game Clock",
                                key=ui_keys.DISPLAY_NFL_CLOCK,
                                background_color=color,
                                size=(checkbox_width, checkbox_height),
                                font=(settings.FONT, checkbox_size),
                                default=current_settings.get("display_nfl_clock", False),
                                checkbox_color=colors.INFO_WHITE,
                            ),
                        ],
                    ],
                    vertical_alignment="top",
                    justification="center",
                    background_color=color,
                ),
                Sg.Push(background_color=color),
            ],
        ],
        border_width=0,
        element_justification="center",
        expand_x=True,
        size=(window_width * 0.9, Sg.Window.get_screen_size()[1] * 0.7),
        background_color=color,
    )

    return [
        [
            Sg.Push(),
            Sg.Text(messages.SETTINGS_TITLE, font=(settings.FONT, title_size, "underline")),
            Sg.Push(),
        ],
        [Sg.VPush()],
        [
            Sg.Frame(
                "",
                [
                    [
                        Sg.Column(
                            [
                                [general_setting_layout],
                                [general_display_layout],
                                [specific_settings_layout],
                            ],
                            scrollable=True,
                            vertical_scroll_only=True,
                            element_justification="center",
                            background_color=color,
                            size=(window_width, int(Sg.Window.get_screen_size()[1] / 2)),
                        ),
                    ],
                ],
                border_width=2,
                relief=Sg.RELIEF_SOLID,
                background_color=color,
            ),
        ],
        [Sg.VPush()],
        [
            Sg.Push(),
            Sg.Text(
                "",
                font=(settings.FONT, button_size),
                key=ui_keys.CONFIRMATION_MESSAGE,
                text_color=colors.SUCCESS_GREEN,
            ),
            Sg.Push(),
        ],
        [Sg.VPush()],
        [
            Sg.Push(),
            Sg.Button(messages.BUTTON_SAVE, font=(settings.FONT, button_size)),
            Sg.Button(messages.BUTTON_BACK, font=(settings.FONT, button_size)),
            Sg.Push(),
        ],
        [Sg.VPush()],
    ]
