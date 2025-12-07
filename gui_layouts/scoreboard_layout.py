"""Create layout of how Scoreboard should look."""
import math

import FreeSimpleGUI as Sg  # type: ignore[import]

import settings
from get_data.get_team_league import append_team_array
from get_data.get_team_logos import get_random_logo
from helper_functions.logger_config import logger
from helper_functions.scoreboard_helpers import resize_text
from main import set_screen


def create_scoreboard_layout() -> list:
    """Create General User Interface.

    :return layout: List of elements and how the should be displayed
    """
    Sg.theme("black")
    set_screen()  # Set the screen to display on
    append_team_array(settings.teams)  # Get the team league and sport name
    resize_text()  # Resize text to fit screen size
    files = get_random_logo()

    # Screen sizes
    window_width, window_height = Sg.Window.get_screen_size()

    column_width = window_width / 3
    column_height = window_height * .66
    info_height = window_height * (1 / 6.75)
    space_between_score = column_width / 8

    logger.info("\n\nWindow Width: %d, Window Height: %d", math.ceil(window_width), math.ceil(window_height))
    logger.info("Column Width: %d, Column Height: %d", math.ceil(column_width), math.ceil(column_height))
    logger.info("Info Height: %d", math.ceil(info_height))
    logger.info("Space Between Score: %d", math.ceil(space_between_score))

    home_logo_layout = [
        [Sg.Push()],
        [Sg.VPush()],
        [Sg.Image(f"images/sport_logos/{files[0][0]}/{files[0][1]}.png", key="home_logo", pad=((0, 0), (0, 0)))],
        [Sg.VPush()],
        [Sg.Push()],
    ]

    away_logo_layout = [
        [Sg.Push()],
        [Sg.VPush()],
        [Sg.Image(f"images/sport_logos/{files[1][0]}/{files[1][1]}.png", key="away_logo", pad=((0, 0), (0, 0)))],
        [Sg.VPush()],
        [Sg.Push()],
    ]

    away_record_layout = [
        [Sg.Push()],
        [Sg.Text("AWAY", font=(settings.FONT, settings.RECORD_TXT_SIZE), key="away_record", pad=((0, 0), (0, 0)))],
        [Sg.Push()],
    ]
    home_record_layout = [
        [Sg.Push()],
        [Sg.Text("HOME", font=(settings.FONT, settings.RECORD_TXT_SIZE), key="home_record", pad=((0, 0), (0, 0)))],
        [Sg.Push()],
    ]

    above_score_layout = [
        [Sg.VPush()],
        [Sg.Push(),
         Sg.Text("", font=(settings.FONT, settings.TOP_TXT_SIZE), key="above_score_txt",
                 pad=((0, 0), (space_between_score, 0))),
         Sg.Push()],
        [Sg.VPush()],
    ]

    score_layout = [
    [
        Sg.Text("SCO", font=(settings.FONT, settings.SCORE_TXT_SIZE),
            key="away_score"),
        Sg.Text("-", font=(settings.FONT, settings.HYPHEN_SIZE),
            key="hyphen"),
        Sg.Text("RE", font=(settings.FONT, settings.SCORE_TXT_SIZE),
            key="home_score"),
    ],
    ]

    home_player_stats = [
        [Sg.Multiline("", key="home_player_stats",
                      font=(settings.FONT, 14), justification="center",
                      no_scrollbar=True, disabled=True, autoscroll=False,
                      border_width=0, background_color="black",
                      size=(30, 20), text_color="white")],
    ]

    away_player_stats = [
        [Sg.Multiline("", key="away_player_stats",
                      font=(settings.FONT, 14), justification="center",
                      no_scrollbar=True, disabled=True, autoscroll=False,
                      border_width=0, background_color="black",
                      size=(30, 30), text_color="white")],
    ]

    # Info layouts
    top_info_layout = [
        [Sg.VPush()],
        [Sg.Push(),
         Sg.Text("", font=(settings.FONT, settings.NBA_TOP_INFO_SIZE),
                 key="top_info"),
         Sg.Push()],
    ]

    bottom_info_layout = [
        [Sg.VPush()],
        [Sg.Push(),
         Sg.Text("Fetching Data...", font=(settings.FONT, settings.INFO_TXT_SIZE),
                 key="bottom_info"),
         Sg.Push()],
        [Sg.VPush()],
        [Sg.Push()],
    ]

    # record height split
    if settings.display_records:
        away_logo_height = int(column_height * 4 / 5)
        home_logo_height = int(column_height * 4 / 5)
        away_record_height = int(column_height * 1 / 5)
        home_record_height = int(column_height * 1 / 5)
    else:
        away_logo_height = home_logo_height = column_height
        away_record_height = home_record_height = 0

    # ----------------------------
    # Middle fixed-size frame (under-score OR stats)
    # ----------------------------
    fixed_middle_height = int(column_height * (8 / 16))

    middle_swap_frame = Sg.Frame(
        "",
        [
            # Timeouts row (toggle visibility)
            [Sg.Push(),
                Sg.Column(
                    [
                        [Sg.Push(),
                            Sg.Text("", font=(settings.FONT, settings.TIMEOUT_SIZE),
                                    expand_x=True, expand_y=True, justification="center",
                                    key="away_timeouts"),
                                    Sg.Push(),
                            Sg.Text("", font=(settings.FONT, settings.TIMEOUT_SIZE),
                                    expand_x=True, expand_y=True, justification="center",
                                    key="home_timeouts"),
                                    Sg.Push(),
                        ],
                    ],
                    key="timeouts_content",
                    element_justification="center",
                    expand_x=True,
                    expand_y=True,
                    visible=True,
                ),
                Sg.Push(),
            ],
            # Swap row: under-score image and player stats
            [
                Sg.Column(
                    [[Sg.Image("", key="under_score_image")]],
                    key="under_score_image_column",
                    element_justification="center",
                    expand_x=True,
                    expand_y=True,
                    visible=True,
                ),
                Sg.Column(
                    [
                        [
                            Sg.Column(away_player_stats, key="away_player_stats_col", expand_x=True, expand_y=True,
                                      element_justification="center"),
                            Sg.Column(home_player_stats, key="home_player_stats_col", expand_x=True, expand_y=True,
                                      element_justification="center"),
                        ],
                    ],
                    key="player_stats_content",
                    element_justification="center",
                    expand_x=True,
                    expand_y=True,
                    visible=False,
                ),
            ],
        ],
        border_width=0,
        element_justification="center",
        size=(column_width, fixed_middle_height),
    )

    # ----------------------------
    # Final layout build
    # ----------------------------
    return [
        [
            # Away column
            Sg.Column([
                [Sg.Frame("", away_logo_layout, border_width=0,
                          size=(column_width, away_logo_height),
                          element_justification="center")],
                [Sg.Frame("", away_record_layout, border_width=0,
                          size=(column_width, away_record_height),
                          element_justification="center")],
            ], pad=(0, 0)),

            # Middle column
            Sg.Column([
                [Sg.Frame("", above_score_layout, border_width=0,
                          size=(column_width, int(column_height * 1 / 4)),
                          element_justification="center")],
                [Sg.Frame("", score_layout, border_width=0,
                          size=(column_width, int(column_height * 3.1 / 16)),
                          element_justification="center")],
                [middle_swap_frame],
            ]),

            # Home column
            Sg.Column([
                [Sg.Frame("", home_logo_layout, border_width=1,
                          size=(column_width, home_logo_height),
                          element_justification="center")],
                [Sg.Frame("", home_record_layout, border_width=1,
                          size=(column_width, home_record_height),
                          element_justification="center")],
            ], pad=(0, 0)),
        ],

        [Sg.VPush()],

        [Sg.Frame("", top_info_layout, border_width=0,
                  size=(window_width, int(info_height * 6 / 7)),
                  element_justification="center")],

        [Sg.Frame("", bottom_info_layout, border_width=0,
                  size=(window_width, info_height),
                  element_justification="center")],

        [Sg.Frame("", [[Sg.Push(),
                        Sg.Text("Created by: Matthew Ferretti",
                                font=(settings.FONT, settings.SIGNATURE_SIZE),
                                key="signature")]],
                  border_width=0,
                  size=(window_width, int(info_height / 7)),
                  element_justification="bottom")],
    ]
