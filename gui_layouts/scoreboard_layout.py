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
                    key="away_score", pad=((0, 0), (space_between_score, 0))),
            Sg.Text("-", font=(settings.FONT, settings.HYPHEN_SIZE),
                    key="hyphen", pad=((0, 0), (space_between_score, 0))),
            Sg.Text("RE", font=(settings.FONT, settings.SCORE_TXT_SIZE),
                    key="home_score", pad=((0, 0), (space_between_score, 0))),
        ],
        [
            Sg.Text("", font=(settings.FONT, settings.TIMEOUT_SIZE),
                    key="away_timeouts", pad=((0, 50), (0, 25))),
            Sg.Text("", font=(settings.FONT, settings.TIMEOUT_SIZE),
                    key="home_timeouts", pad=((50, 0), (0, 25))),
        ],
    ]

    under_score_image = [
        [Sg.VPush()],
        [Sg.Image("", key="under_score_image")],
        [Sg.VPush()],
    ]

    home_player_stats = [
        [Sg.Push(),
         Sg.Multiline("", key="home_player_stats",
                      font=(settings.FONT, 12), justification="center",
                      no_scrollbar=True, disabled=True, autoscroll=False,
                      border_width=0, background_color="black",
                      size=(30, 20), text_color="white"),
         Sg.Push()],
        [Sg.VPush()],
    ]

    away_player_stats = [
        [Sg.Push(),
         Sg.Multiline("", key="away_player_stats",
                      font=(settings.FONT, 12), justification="center",
                      no_scrollbar=True, disabled=True, autoscroll=False,
                      border_width=0, background_color="black",
                      size=(30, 30), text_color="white"),
         Sg.Push()],
        [Sg.VPush()],
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

    fixed_middle_height = int(column_height * (5 / 16))

    middle_swap_frame = Sg.Frame(
        "",
        [[Sg.VPush()],
            # under-score image (visible first)
            [Sg.Push(),
                Sg.Frame("",
                    under_score_image,
                    key="under_score_image_content",
                    visible=True,
                    expand_x=True,
                    expand_y=True,
                    element_justification="center",
                ),
            Sg.Push(),
            ],
            [Sg.VPush()],

            # player stats (hidden)
            [
                Sg.Column(
                    [
                        [
                            Sg.Frame("", away_player_stats,
                                    border_width=0,
                                    size=(column_width/2, fixed_middle_height),
                                    element_justification="center"),
                            Sg.Frame("", home_player_stats,
                                    border_width=0,
                                    size=(column_width/2, fixed_middle_height),
                                    element_justification="center"),
                        ],
                    ],
                    key="player_stats_content",
                    element_justification="center",
                    visible=False,
                    expand_x=True,
                    expand_y=True,
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
                          size=(column_width, int(column_height * 7 / 16)),
                          element_justification="center")],
                [middle_swap_frame],
            ]),

            # Home column
            Sg.Column([
                [Sg.Frame("", home_logo_layout, border_width=0,
                          size=(column_width, home_logo_height),
                          element_justification="center")],
                [Sg.Frame("", home_record_layout, border_width=0,
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
