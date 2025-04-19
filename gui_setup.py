'''Function to Create GUI using FreeSimpleGUI'''

import FreeSimpleGUI as sg  # pip install FreeSimpleGUI
from constants import *
from get_team_logos import get_random_logo
import math


def gui_setup() -> sg.Window:
    '''Create General User Interface'''

    sg.theme("black")
    files = get_random_logo()

    window_width = sg.Window.get_screen_size()[0]
    window_height = sg.Window.get_screen_size()[1]

    column_width = window_width / 3
    column_height = window_height * .66
    info_height = window_height * (1/6.75)
    space_between_score = column_width / 8

    print(f"\n\nWindow Width: {math.ceil(window_width)}, Window Height: {math.ceil(window_height)}")
    print(f"Column Width: {math.ceil(column_width)}, Column Height: {math.ceil(column_height)}")
    print(f"Info Height: {math.ceil(info_height)}")
    print(f"Space Between Score: {math.ceil(space_between_score)}\n\n")

    home_record_layout = [
        [sg.VPush()],
        [sg.Image(f"sport_logos/{files[0][0]}/{files[0][1]}.png", key='home_logo', pad=((0, 0), (0, 0)))],
        [sg.Text("HOME", font=(FONT, RECORD_TXT_SIZE), key='home_record')]
    ]

    away_record_layout = [
        [sg.VPush()],
        [sg.Image(f"sport_logos/{files[1][0]}/{files[1][1]}.png", key='away_logo', pad=((0, 0), (0, 0)))],
        [sg.Text("AWAY", font=(FONT, RECORD_TXT_SIZE), key='away_record')]
    ]

    score_layout = [
        [sg.Text("", font=(FONT, TOP_TXT_SIZE), key='baseball_inning', pad=((0, 0), (space_between_score, 0)))],
        [sg.Text("Sco", font=(FONT, SCORE_TXT_SIZE), key='away_score', pad=((0, 0), (space_between_score, 0))),
         sg.Text("-", font=(FONT, HYPHEN_SIZE), key='hyphen', pad=((0, 0), (space_between_score, 0))),
         sg.Text("re", font=(FONT, SCORE_TXT_SIZE), key='home_score', pad=((0, 0), (space_between_score , 0)))],
        [sg.Text("", font=(FONT, TIMEOUT_SIZE), key='away_timeouts', pad=((0, 50), (0 , 25))),
         sg.Text("", font=(FONT, TIMEOUT_SIZE), key='home_timeouts', pad=((50, 0), (0 , 25)))],
        [sg.Image("", key='network_logo')]
    ]

    top_info_layout = [[sg.VPush()], [sg.Push(), sg.Text("", font=(FONT, NOT_PLAYING_TOP_INFO_SIZE), key='top_info'), sg.Push()]]
    bottom_info_layout = [[sg.VPush()], [sg.Push(), sg.Text("Fetching Data...", font=(FONT, INFO_TXT_SIZE), auto_size_text=True, size=(None, None), key='bottom_info'), sg.Push()],[sg.VPush()],[sg.Push()]]

    layout = [[
        sg.Push(),
        sg.Frame("", away_record_layout, element_justification='center', border_width=0, size=(column_width, column_height)),
        sg.Frame("", score_layout, element_justification='center', border_width=0, size=(column_width, column_height)),
        sg.Frame("", home_record_layout, element_justification='center', border_width=0, size=(column_width, column_height)),
        sg.Push()
    ],
        [sg.Frame("", top_info_layout, element_justification='center', border_width=0, size=(window_width, info_height))],
        [sg.Frame("", bottom_info_layout, element_justification='center', border_width=0, size=(window_width, info_height))],
        [sg.Push(), sg.Text("Created by: Matthew Ferretti", font=(FONT, 10), key='personal')]
    ]

    # Create the window
    window = sg.Window("Scoreboard", layout, no_titlebar=False, resizable=True, return_keyboard_events=True).Finalize()
    window.Maximize()
    window.TKroot.config(cursor="none")  # Remove cursor from screen

    return window


def will_text_fit_on_screen(text: str) -> bool:
    '''Check if text will fit on screen'''
    screen_width = sg.Window.get_screen_size()[0]  # Get screen width
    char_width = INFO_TXT_SIZE * 0.6  # Approximate multiplier for Calibri font

    # Calculate text width
    text_width = len(text) * char_width

    if text_width >= screen_width:
        print(f"Bottom Text will scroll, text size: {text_width}, screen size: {screen_width}")
        return True
    else:
        return False