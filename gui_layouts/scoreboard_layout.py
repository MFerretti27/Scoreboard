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

    window_width = Sg.Window.get_screen_size()[0]
    window_height = Sg.Window.get_screen_size()[1]

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
        [Sg.Text("SCO", font=(settings.FONT, settings.SCORE_TXT_SIZE), key="away_score",
                 pad=((0, 0), (space_between_score, 0))),
         Sg.Text("-", font=(settings.FONT, settings.HYPHEN_SIZE), key="hyphen", pad=((0, 0), (space_between_score, 0))),
         Sg.Text("RE", font=(settings.FONT, settings.SCORE_TXT_SIZE), key="home_score",
                 pad=((0, 0), (space_between_score, 0)))],
        [Sg.Text("", font=(settings.FONT, settings.TIMEOUT_SIZE), key="away_timeouts",
                 pad=((0, 50), (0, 25))),
         Sg.Text("", font=(settings.FONT, settings.TIMEOUT_SIZE), key="home_timeouts",
                 pad=((50, 0), (0, 25)))],
    ]

    below_score_image = [
        [Sg.VPush()],
        [Sg.Image("", key="under_score_image")],
        [Sg.VPush()],
    ]

    top_info_layout = [[Sg.VPush()], [Sg.Push(), Sg.Text("", font=(settings.FONT, settings.NBA_TOP_INFO_SIZE),
                                                         key="top_info"), Sg.Push()]]
    bottom_info_layout = [[Sg.VPush()],
                          [Sg.Push(),
                           Sg.Text("Fetching Data...", font=(settings.FONT, settings.INFO_TXT_SIZE), key="bottom_info"),
                           Sg.Push()],
                          [Sg.VPush()],
                          [Sg.Push()]]

    # Lower the logo images if the records are not displayed
    if settings.display_records:
        away_logo_height = column_height * (4 / 5)
        home_logo_height = column_height * (4 / 5)
        away_record_height = column_height * (1 / 5)
        home_record_height = column_height * (1 / 5)
    else:
        away_logo_height = column_height
        home_logo_height = column_height
        away_record_height = 0
        home_record_height = 0

    return [
        [
            Sg.Column([  # Vertical stack for away team
                [Sg.Frame("", away_logo_layout, element_justification="center", border_width=0,
                          size=(column_width, away_logo_height))],
                [Sg.Frame("", away_record_layout, element_justification="center", border_width=0,
                          size=(column_width, away_record_height))],
            ], element_justification="center", pad=((0, 0), (0, 0))),
            Sg.Column([  # Vertical score
                [Sg.Frame("", above_score_layout, element_justification="center", border_width=0,
                          size=(column_width, column_height * (1 / 4)))],
                [Sg.Frame("", score_layout, element_justification="center", border_width=0,
                          size=(column_width, column_height * (7 / 16)))],
                [Sg.Frame("", below_score_image, element_justification="center", border_width=0,
                          size=(column_width, column_height * (5 / 16)))],
            ], element_justification="center", pad=((0, 0), (0, 0))),
            Sg.Column([  # Vertical stack for home team
                [Sg.Frame("", home_logo_layout, element_justification="center", border_width=0,
                          size=(column_width, home_logo_height))],
                [Sg.Frame("", home_record_layout, element_justification="center", border_width=0,
                          size=(column_width, home_record_height))],
            ], element_justification="center", pad=((0, 0), (0, 0))),
        ],
        [Sg.VPush()],
        [Sg.Frame("", top_info_layout, element_justification="center", border_width=0,
                  size=(window_width, info_height * (6 / 7)))],
        [Sg.Frame("", bottom_info_layout, element_justification="center", border_width=0,
                  size=(window_width, info_height))],
        [Sg.Frame("",
                  [[Sg.Push(), Sg.Text("Created by: Matthew Ferretti", font=(settings.FONT, settings.SIGNATURE_SIZE),
                                       key="signature")]],
                  element_justification="bottom", border_width=0, size=(window_width, info_height * (1 / 7)))],
    ]
