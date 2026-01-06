"""Create layout of how Scoreboard should look."""

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

    # Account for any potential window decorations or padding issues
    # Use slightly smaller width to ensure columns fit properly
    usable_width = window_width - 6  # Small adjustment for any hidden padding
    column_width = int(usable_width / 3)
    column_height = int(window_height * .68)
    info_height = int(window_height * (1 / 7))

    logger.info("\n\nWindow Width: %d, Window Height: %d", window_width, window_height)
    logger.info("Usable Width: %d", usable_width)
    logger.info("Column Width: %d (total across 3 = %d)", column_width, column_width * 3)
    logger.info("Column Height: %d, Info Height: %d", column_height, info_height)

    home_logo_layout = [
        [Sg.Push()],
        [Sg.VPush()],
        [Sg.Image(f"images/sport_logos/{files[0][0]}/{files[0][1]}.png", key="home_logo",
                  pad=((0, 0), (0, 0)), enable_events=True)],
        [Sg.VPush()],
        [Sg.Push()],
    ]

    away_logo_layout = [
        [Sg.Push()],
        [Sg.VPush()],
        [Sg.Image(f"images/sport_logos/{files[1][0]}/{files[1][1]}.png", key="away_logo",
                  pad=((0, 0), (0, 0)), enable_events=True)],
        [Sg.VPush()],
        [Sg.Push()],
    ]

    away_record_layout = [
        [Sg.Push()],
        [Sg.Text("AWAY", font=(settings.FONT, settings.RECORD_TXT_SIZE), key="away_record",
                 pad=((0, 0), (0, 0)), enable_events=True)],
        [Sg.Push()],
    ]
    home_record_layout = [
        [Sg.Push()],
        [Sg.Text("HOME", font=(settings.FONT, settings.RECORD_TXT_SIZE), key="home_record",
                 pad=((0, 0), (0, 0)), enable_events=True)],
        [Sg.Push()],
    ]

    above_score_layout = [
        [Sg.VPush()],
        [Sg.Push(),
         Sg.Text("", font=(settings.FONT, settings.TOP_TXT_SIZE), key="above_score_txt",
                 pad=((0, 0), (0, 0)), enable_events=True),
         Sg.Push()],
        [Sg.VPush()],
    ]

    score_layout = [
        [
            Sg.Text("SCO", font=(settings.FONT, settings.SCORE_TXT_SIZE),
                    key="away_score", enable_events=True, pad=(0, 0)),
            Sg.Text("", font=(settings.FONT, settings.HYPHEN_SIZE),
                    key="hyphen", enable_events=True, pad=(0, 0)),
            Sg.Text("RE", font=(settings.FONT, settings.SCORE_TXT_SIZE),
                    key="home_score", enable_events=True, pad=(0, 0)),
        ],
    ]

    timeout_layout =[
        [
            Sg.Text("", font=(settings.FONT, settings.TIMEOUT_SIZE),
                    expand_x=True, justification="left",
                    key="away_timeouts", enable_events=True, pad=(0, 0)),
            Sg.Text("", font=(settings.FONT, settings.TIMEOUT_SIZE),
                    expand_x=True, justification="right",
                    key="home_timeouts", enable_events=True, pad=(0, 0)),
        ],
    ]

    if Sg.Window.get_screen_size()[0] > 1000:
        home_size=[30, 25]
        away_size=[30, 25]
    else:
        home_size=[0, 0]
        away_size=[60, 25]

    home_player_stats = [
        [Sg.Multiline("", key="home_player_stats",
                      font=(settings.FONT, settings.PLAYER_STAT_SIZE), justification="center",
                      no_scrollbar=True, disabled=True, autoscroll=False,
                      border_width=0, background_color="black",
                      size=(home_size[0], home_size[1]), text_color="white")],
    ]

    away_player_stats = [
        [Sg.Multiline("", key="away_player_stats",
                      font=(settings.FONT, settings.PLAYER_STAT_SIZE), justification="center",
                      no_scrollbar=True, disabled=True, autoscroll=False,
                      border_width=0, background_color="black",
                      size=(away_size[0], away_size[1]), text_color="white")],
    ]


    home_team_stats = [
        [Sg.Multiline("", key="home_team_stats",
                      font=(settings.FONT, settings.PLAYER_STAT_SIZE), justification="left",
                      no_scrollbar=True, disabled=True, autoscroll=False,
                      border_width=0, background_color="black",
                      size=(60, 30), text_color="white", enable_events=True)],
    ]

    away_team_stats = [
        [Sg.Multiline("", key="away_team_stats",
                      font=(settings.FONT, settings.PLAYER_STAT_SIZE), justification="left",
                      no_scrollbar=True, disabled=True, autoscroll=False,
                      border_width=0, background_color="black",
                      size=(60, 30), text_color="white", enable_events=True)],
    ]

    # Info layouts
    top_info_layout = [
        [Sg.VPush()],
        [Sg.Push(),
         Sg.Text("", font=(settings.FONT, settings.NBA_TOP_INFO_SIZE),
                 key="top_info", enable_events=True),
         Sg.Push()],
    ]

    bottom_info_layout = [
        [Sg.VPush()],
        [Sg.Push(),
         Sg.Text("Fetching Data...", font=(settings.FONT, settings.INFO_TXT_SIZE),
                 key="bottom_info", enable_events=True),
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


    away_logo_swap_frame = Sg.Frame(
        "",
        [
            [Sg.pin(Sg.Column(
                [
                    [Sg.Frame("", away_logo_layout, border_width=0,
                                size=(column_width, away_logo_height),
                                element_justification="center", pad=(0, 0))],
                    [Sg.Frame("", away_record_layout, border_width=0,
                                size=(column_width, away_record_height),
                                element_justification="center", pad=(0, 0))],
                ],
                    key="away_logo_section",
                    element_justification="center",
                    expand_x=True,
                    expand_y=True,
                    visible=True,
                    pad=(0, 0),
                ))],
                [Sg.pin(Sg.Column(
                    [
                        [Sg.Column(away_team_stats, key="away_team_stats_col", expand_x=True, expand_y=True,
                                    element_justification="center", pad=(0, 0)),
                        ],
                    ],
                    key="away_stats_section",
                    element_justification="center",
                    expand_x=True,
                    expand_y=True,
                    visible=False,
                    pad=(0, 0),
                ))],
        ],
        border_width=0,
        element_justification="center",
        size=(column_width, column_height),
        pad=(0, 0),
    )

    home_logo_swap_frame = Sg.Frame(
        "",
        [
            [Sg.pin(Sg.Column(
                [
                    [Sg.Frame("", home_logo_layout, border_width=0,
                                size=(column_width, home_logo_height),
                                element_justification="center", pad=(0, 0))],
                    [Sg.Frame("", home_record_layout, border_width=0,
                                size=(column_width, home_record_height),
                                element_justification="center", pad=(0, 0))],
                ],
                    key="home_logo_section",
                    element_justification="center",
                    expand_x=True,
                    expand_y=True,
                    visible=True,
                    pad=(0, 0),
                ))],
                [Sg.pin(Sg.Column(
                    [
                        [Sg.Column(home_team_stats, expand_x=True, expand_y=True,
                                    element_justification="center", pad=(0, 0)),
                        ],
                    ],
                    key="home_stats_section",
                    element_justification="center",
                    expand_x=True,
                    expand_y=True,
                    visible=False,
                    pad=(0, 0),
                ))],
        ],
        border_width=0,
        element_justification="center",
        size=(column_width, column_height),
        pad=(0, 0),
    )

    # ----------------------------
    # Middle fixed-size frame (under-score OR stats)
    # ----------------------------
    fixed_middle_height = int(column_height * (4 / 5))
    timeout_height = int(max(settings.TIMEOUT_SIZE, settings.NBA_TIMEOUT_SIZE) * 2.2)

    below_score_image = [
        [Sg.Image("", key="under_score_image", expand_x=True)],
    ]

    middle_swap_frame = Sg.Frame(
        "",
        [[Sg.VPush()],
            [Sg.Column(
                [
                    [Sg.Frame(
                        "",
                        score_layout,
                        key="score_content",
                        border_width=0,
                        element_justification="center",
                        expand_x=True,
                        expand_y=False,
                        pad=(0, 0),
                    )],
                ],
                key="score_section",
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
                                    border_width=0,
                                    expand_x=True,
                                    expand_y=False,
                                    size=(column_width, timeout_height),
                                    pad=(0, 0),
                                ),
                            ],
                        ],
                        key="timeouts_content",
                        expand_x=True,
                        element_justification="center",
                        size=(column_width, timeout_height),
                        pad=(0, 0),
                    ),
                ),
            ],
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
                                    border_width=0,
                                    pad=(0, 0)),
                            ],
                        ],
                        key="under_score_image_column",
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
                                Sg.Column(away_player_stats, key="away_player_stats_col", expand_x=True, expand_y=True,
                                          element_justification="center", pad=(0, 0)),
                                Sg.Column(home_player_stats, key="home_player_stats_col", expand_x=True, expand_y=True,
                                          element_justification="center", pad=(0, 0)),
                            ],
                        ],
                        key="player_stats_content",
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
        border_width=0,
        expand_y=True,
        element_justification="center",
        size=(column_width, fixed_middle_height),
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
                [Sg.Frame("", above_score_layout, border_width=0,
                          size=(column_width, int(column_height * 1 / 5)),
                          element_justification="center", pad=(0, 0))],
                [middle_swap_frame],
            ], pad=(0, 0), vertical_alignment="top"),

            # Home column
            Sg.Column([
                [home_logo_swap_frame],
            ], pad=(0, 0), vertical_alignment="top"),
        ],

        [Sg.Frame("", top_info_layout, border_width=0,
                  size=(window_width, int(info_height * 6 / 7)),
                  element_justification="center",
                  pad=(0, 0))],

        [Sg.Frame("", bottom_info_layout, border_width=0,
                  size=(window_width, info_height),
                  element_justification="center",
                  pad=(0, 0))],

        [Sg.Frame("", [[Sg.Push(),
                        Sg.Text("Created by: Matthew Ferretti",
                                font=(settings.FONT, settings.SIGNATURE_SIZE),
                                key="signature")]],
                  border_width=0,
                  expand_x=True,
                  expand_y=True,
                  element_justification="bottom",
                  pad=(0, 0))],
    ]
