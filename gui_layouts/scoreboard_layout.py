"""Create layout of how Scoreboard should look."""
from __future__ import annotations

import FreeSimpleGUI as Sg  # type: ignore[import]

import settings
from constants import colors, ui_keys
from constants.file_paths import get_sport_logo_path
from get_data.get_team_logos import get_random_logo
from helper_functions.logging.logger_config import logger
from helper_functions.ui.scoreboard_helpers import resize_text
from main import set_screen


def create_scoreboard_layout() -> list:
    """Create General User Interface.

    :return layout: List of elements and how the should be displayed
    """
    Sg.theme(colors.THEME_BLACK)
    set_screen()  # Set the screen to display on
    resize_text()  # Resize text to fit screen size
    files = get_random_logo()

    # Screen sizes
    window_width, window_height = Sg.Window.get_screen_size()

    # Account for any potential window decorations or padding issues
    # Use slightly smaller width to ensure columns fit properly
    usable_width = window_width - 6  # Small adjustment for any hidden padding
    column_width = int(usable_width / 3)
    column_height = int(window_height * .75)
    info_height = int(window_height * (1 / 7))

    logger.info("\n\nWindow Width: %d, Window Height: %d", window_width, window_height)
    logger.info("Usable Width: %d", usable_width)
    logger.info("Column Width: %d (total across 3 = %d)", column_width, column_width * 3)
    logger.info("Column Height: %d, Info Height: %d", column_height, info_height)

    home_logo_layout = [
        [Sg.Push()],
        [Sg.VPush()],
        [Sg.Image(get_sport_logo_path(files[0][0], files[0][1]), key=ui_keys.HOME_LOGO,
                  pad=((0, 0), (0, 0)), enable_events=True)],
        [Sg.VPush()],
        [Sg.Push()],
    ]

    away_logo_layout = [
        [Sg.Push()],
        [Sg.VPush()],
        [Sg.Image(get_sport_logo_path(files[1][0], files[1][1]), key=ui_keys.AWAY_LOGO,
                  pad=((0, 0), (0, 0)), enable_events=True)],
        [Sg.VPush()],
        [Sg.Push()],
    ]

    away_record_layout = [
        [Sg.Push()],
        [Sg.Text("AWAY", font=(settings.FONT, settings.RECORD_TXT_SIZE), key=ui_keys.AWAY_RECORD,
                 pad=((0, 0), (0, 0)), enable_events=True)],
        [Sg.Push()],
    ]
    home_record_layout = [
        [Sg.Push()],
         [Sg.Text("HOME", font=(settings.FONT, settings.RECORD_TXT_SIZE), key=ui_keys.HOME_RECORD,
                 pad=((0, 0), (0, 0)), enable_events=True)],
        [Sg.Push()],
    ]

    above_score_layout = [
        [Sg.VPush()],
        [Sg.Push(),
         Sg.Text("", font=(settings.FONT, settings.TOP_TXT_SIZE), key=ui_keys.ABOVE_SCORE_TXT,
                 pad=((0, 0), (0, 0)), enable_events=True),
         Sg.Push()],
        [Sg.VPush()],
    ]

    score_layout = [
        [
                Sg.Text("", font=(settings.FONT, settings.SCORE_TXT_SIZE),
                    key=ui_keys.AWAY_SCORE, enable_events=True, pad=(0, 0)),
                Sg.Text("", font=(settings.FONT, settings.HYPHEN_SIZE),
                    key=ui_keys.HYPHEN, enable_events=True, pad=(0, 0)),
                Sg.Text("", font=(settings.FONT, settings.SCORE_TXT_SIZE),
                    key=ui_keys.HOME_SCORE, enable_events=True, pad=(0, 0)),
        ],
    ]

    timeout_layout =[
        [
                Sg.Text("", font=(settings.FONT, settings.TIMEOUT_SIZE),
                    expand_x=True, justification="left",
                    key=ui_keys.AWAY_TIMEOUTS, enable_events=True, pad=(0, 0)),
                Sg.Text("", font=(settings.FONT, settings.TIMEOUT_SIZE),
                    expand_x=True, justification="right",
                    key=ui_keys.HOME_TIMEOUTS, enable_events=True, pad=(0, 0)),
        ],
    ]

    if Sg.Window.get_screen_size()[0] > 1300:
        home_size=[30, 50]
        away_size=[30, 50]
    else:
        home_size=[0, 0]
        away_size=[80, 50]

    home_player_stats = [
        [Sg.Multiline("", key=ui_keys.HOME_PLAYER_STATS,
                      font=(settings.FONT, settings.PLAYER_STAT_SIZE), justification="center",
                      no_scrollbar=True, disabled=True, autoscroll=False,
                      border_width=1, background_color=colors.BACKGROUND_BLACK,
                      size=(home_size[0], home_size[1]), text_color=colors.TEXT_WHITE)],
    ]

    away_player_stats = [
        [Sg.Multiline("", key=ui_keys.AWAY_PLAYER_STATS,
                      font=(settings.FONT, settings.PLAYER_STAT_SIZE), justification="center",
                      no_scrollbar=True, disabled=True, autoscroll=False,
                      border_width=1, background_color=colors.BACKGROUND_BLACK,
                      size=(away_size[0], away_size[1]), text_color=colors.TEXT_WHITE)],
    ]


    home_team_stats = [
        [Sg.Multiline("", key=ui_keys.HOME_TEAM_STATS,
                      font=(settings.FONT, settings.TEAM_STAT_SIZE), justification="left",
                      no_scrollbar=True, disabled=True, autoscroll=False,
                      border_width=1, background_color=colors.BACKGROUND_BLACK,
                      size=(60, 50), text_color=colors.TEXT_WHITE, enable_events=True)],
    ]

    away_team_stats = [
        [Sg.Multiline("", key=ui_keys.AWAY_TEAM_STATS,
                      font=(settings.FONT, settings.TEAM_STAT_SIZE), justification="left",
                      no_scrollbar=True, disabled=True, autoscroll=False,
                      border_width=1, background_color=colors.BACKGROUND_BLACK,
                      size=(60, 50), text_color=colors.TEXT_WHITE, enable_events=True)],
    ]

    # Info layouts
    top_info_layout = [
        [Sg.VPush()],
        [Sg.Push(),
         Sg.Text("", font=(settings.FONT, settings.NOT_PLAYING_TOP_INFO_SIZE),
             key=ui_keys.TOP_INFO, enable_events=True),
         Sg.Push()],
    ]

    bottom_info_layout = [
        [Sg.VPush()],
        [Sg.Push(),
         Sg.Text("Fetching Data...", font=(settings.FONT, settings.INFO_TXT_SIZE),
             key=ui_keys.BOTTOM_INFO, enable_events=True),
         Sg.Push()],
        [Sg.VPush()],
        [Sg.Push()],
    ]

    # record height split
    away_logo_height = int(column_height * 4 / 5)
    home_logo_height = int(column_height * 4 / 5)
    away_record_height = int(column_height * 1 / 5)
    home_record_height = int(column_height * 1 / 5)

    away_logo_swap_frame = Sg.Frame(
        "",
        [
            [Sg.pin(Sg.Column(
                [
                    [Sg.Frame("", away_logo_layout, border_width=1,
                                size=(column_width, away_logo_height),
                                element_justification="center", pad=(0, 0))],
                    [Sg.Frame("", away_record_layout, border_width=1,
                                size=(column_width, away_record_height),
                                element_justification="center", pad=(0, 0))],
                ],
                    key=ui_keys.AWAY_LOGO_SECTION,
                    element_justification="center",
                    expand_x=True,
                    expand_y=True,
                    visible=True,
                    pad=(0, 0),
                ))],
                [Sg.pin(Sg.Column(
                    [
                        [Sg.Column(away_team_stats, key=ui_keys.AWAY_TEAM_STATS_COL, expand_x=True, expand_y=True,
                                   element_justification="center", pad=(0, 0)),
                        ],
                    ],
                    key=ui_keys.AWAY_STATS_SECTION,
                    element_justification="center",
                    expand_x=True,
                    expand_y=True,
                    visible=False,
                    pad=(0, 0),
                ))],
        ],
        border_width=1,
        element_justification="center",
        size=(column_width, column_height),
        pad=(0, 0),
    )

    home_logo_swap_frame = Sg.Frame(
        "",
        [
            [Sg.pin(Sg.Column(
                [
                    [Sg.Frame("", home_logo_layout, border_width=1,
                                size=(column_width, home_logo_height),
                                element_justification="center", pad=(0, 0))],
                    [Sg.Frame("", home_record_layout, border_width=1,
                                size=(column_width, home_record_height),
                                element_justification="center", pad=(0, 0))],
                ],
                    key=ui_keys.HOME_LOGO_SECTION,
                    element_justification="center",
                    expand_x=True,
                    expand_y=True,
                    visible=True,
                    pad=(0, 0),
                ))],
                [Sg.pin(Sg.Column(
                    [
                        [Sg.Column(home_team_stats, key=ui_keys.HOME_TEAM_STATS_COL, expand_x=True, expand_y=True,
                                   element_justification="center", pad=(0, 0)),
                        ],
                    ],
                    key=ui_keys.HOME_STATS_SECTION,
                    element_justification="center",
                    expand_x=True,
                    expand_y=True,
                    visible=False,
                    pad=(0, 0),
                ))],
        ],
        border_width=1,
        element_justification="center",
        size=(column_width, column_height),
        pad=(0, 0),
    )

    # ----------------------------
    # Middle fixed-size frame (under-score OR stats)
    # ----------------------------
    below_score_image = [
        [Sg.Image("", key=ui_keys.UNDER_SCORE_IMAGE, expand_x=True)],
    ]

    middle_swap_frame = Sg.Frame(
        "",
        [
            [Sg.Frame(
                "",
                above_score_layout,
                border_width=1,
                element_justification="center",
                expand_x=True,
                expand_y=False,
                pad=(0, 0),
            ),
            ],
            [Sg.VPush()],
            [Sg.Column(
                [
                    [Sg.Frame(
                        "",
                        score_layout,
                           key=ui_keys.SCORE_CONTENT,
                        border_width=1,
                        element_justification="center",
                        expand_x=True,
                        expand_y=False,
                        pad=(0, 0),
                    )],
                ],
                key=ui_keys.SCORE_SECTION,
                expand_x=True,
                expand_y=False,
                element_justification="center",
                pad=(0, 0),
            )],
            [
                Sg.pin(
                    Sg.Column(
                        [
                            [
                                Sg.Frame(
                                    "",
                                    timeout_layout,
                                    border_width=1,
                                    expand_x=True,
                                    expand_y=False,
                                    size=(column_width, settings.TIMEOUT_HEIGHT),
                                    pad=(0, 0),
                                ),
                            ],
                        ],
                        key=ui_keys.TIMEOUTS_CONTENT,
                        expand_x=True,
                        element_justification="center",
                        size=(column_width, settings.TIMEOUT_HEIGHT),
                        pad=(0, 0),
                    ),
                ),
            ],
            [Sg.VPush()],
            # Swap row: under-score image and player stats
            [
                Sg.pin(
                    Sg.Column(
                        [
                            [
                                Sg.Frame("", below_score_image,
                                    expand_x=True, expand_y=True,
                                    element_justification="center",
                                    vertical_alignment="top",
                                    border_width=1,
                                    pad=(0, 0)),
                            ],
                        ],
                        key=ui_keys.UNDER_SCORE_IMAGE_COLUMN,
                        element_justification="center",
                        vertical_alignment="top",
                        expand_x=True,
                        expand_y=True,
                        visible=False,
                        pad=(0, 0),
                    ),
                ),
                Sg.pin(
                    Sg.Column(
                        [
                            [
                                Sg.Column(away_player_stats, key=ui_keys.AWAY_PLAYER_STATS_COL,
                                          expand_x=True, expand_y=True,
                                          element_justification="center", pad=(0, 0)),
                                Sg.Column(home_player_stats, key=ui_keys.HOME_PLAYER_STATS_COL,
                                          expand_x=True, expand_y=True,
                                          element_justification="center", pad=(0, 0)),
                            ],
                        ],
                        key=ui_keys.PLAYER_STATS_CONTENT,
                        element_justification="center",
                        expand_x=True,
                        expand_y=True,
                        visible=False,
                        pad=(0, 0),
                    ),
                ),
            ],
            [Sg.VPush()],
        ],
        border_width=1,
        expand_y=True,
        element_justification="center",
        size=(column_width, column_height),
        pad=(0, 0),
    )

    # ----------------------------
    # Final layout build
    # ----------------------------
    return [
        [
            # Away column
            Sg.Column([
                [away_logo_swap_frame],
            ], pad=(0, 0), vertical_alignment="top"),

            # Middle column
            Sg.Column([
                [middle_swap_frame],
            ], pad=(0, 0), vertical_alignment="top"),

            # Home column
            Sg.Column([
                [home_logo_swap_frame],
            ], pad=(0, 0), vertical_alignment="top"),
        ],

        [Sg.Frame("", top_info_layout, border_width=1,
                  size=(window_width, int(info_height * 5 / 7)),
                  element_justification="center",
                  pad=(0, 0))],

        [Sg.Frame("", bottom_info_layout, border_width=1,
                  size=(window_width, info_height),
                  element_justification="center",
                  pad=(0, 0))],

        [Sg.Frame("", [[Sg.Push(),
                        Sg.Text("Created by: Matthew Ferretti",
                                font=(settings.FONT, settings.SIGNATURE_SIZE),
                                key=ui_keys.SIGNATURE)]],
                  border_width=1,
                  expand_x=True,
                  expand_y=True,
                  element_justification="bottom",
                  pad=(0, 0))],
    ]
