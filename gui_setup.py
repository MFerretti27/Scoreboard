'''Function to Create GUI using FreeSimpleGUI'''

import FreeSimpleGUI as sg  # pip install FreeSimpleGUI
from constants import *
from get_team_logos import get_random_logo


def gui_setup() -> sg.Window:
    '''Create General User Interface'''

    sg.theme("black")
    files = get_random_logo()

    home_record_layout = [
        [sg.Image(f"sport_logos/{files[0][0]}/{files[0][1]}.png", key='home_logo', pad=((0, 0), (SPACE_BETWEEN_TOP_AND_LOGOS, 0)))],
        [sg.Text("HOME", font=(FONT, RECORD_TXT_SIZE), key='home_record')]
    ]

    away_record_layout = [
        [sg.Image(f"sport_logos/{files[1][0]}/{files[1][1]}.png", key='away_logo', pad=((0, 0), (SPACE_BETWEEN_TOP_AND_LOGOS, 0)))],
        [sg.Text("AWAY", font=(FONT, RECORD_TXT_SIZE), key='away_record')]
    ]

    score_layout = [
        [sg.Text("", font=(FONT, TOP_TXT_SIZE), key='baseball_inning', pad=((0, 0), (SPACE_BETWEEN_TOP_TXT_AND_SCORE, 0)))],
        [sg.Text("Sco", font=(FONT, SCORE_TXT_SIZE), key='away_score', pad=((0, 0), (SPACE_BETWEEN_TOP_TXT_AND_SCORE, 0))),
         sg.Text("-", font=(FONT, HYPHEN_SIZE), key='hyphen', pad=((0, 0), (SPACE_BETWEEN_TOP_TXT_AND_SCORE, 0))),
         sg.Text("re", font=(FONT, SCORE_TXT_SIZE), key='home_score', pad=((0, 0), (SPACE_BETWEEN_TOP_TXT_AND_SCORE , 0)))],
        [sg.Text("", font=(FONT, TIMEOUT_SIZE), key='timeouts')],
        [sg.Image("", key='network_logo', pad=((0, 0), (SPACE_BETWEEN_TOP_AND_LOGOS, 0)))]
    ]

    top_info_layout = [[sg.VPush()], [sg.Push(), sg.Text("Top Info", font=(FONT, NOT_PLAYING_TOP_INFO_SIZE), key='top_info'), sg.Push()]]
    bottom_info_layout = [[sg.VPush()], [sg.Push(), sg.Text("Bottom Info", font=(FONT, INFO_TXT_SIZE), auto_size_text=True, size=(None, None), key='bottom_info'), sg.Push()],[sg.VPush()],[sg.Push()]]

    layout = [[
        sg.Push(),
        sg.Frame("", away_record_layout, element_justification='center', border_width=0, size=(COLUMN_WIDTH, COLUMN_HEIGHT)),
        sg.Frame("", score_layout, element_justification='center', border_width=0, size=(COLUMN_WIDTH, COLUMN_HEIGHT)),
        sg.Frame("", home_record_layout, element_justification='center', border_width=0, size=(COLUMN_WIDTH, COLUMN_HEIGHT)),
        sg.Push()
    ],
        [sg.Frame("", top_info_layout, element_justification='center', border_width=0, size=(COLUMN_WIDTH * 3, INFO_SPACE_HEIGHT))],
        [sg.Frame("", bottom_info_layout, element_justification='center', border_width=0, size=(COLUMN_WIDTH * 3, INFO_SPACE_HEIGHT))],
        [sg.Push(), sg.Text("Created by: Matthew Ferretti", font=(FONT, 10), key='personal')]
    ]

    # Create the window
    window = sg.Window("Scoreboard", layout, no_titlebar=True, resizable=True, return_keyboard_events=True).Finalize()
    window.Maximize()
    window.TKroot.config(cursor="none")  # Remove cursor from screen

    print(f"Screen Width: {sg.Window.get_screen_size()[0]}")
    print(f"Screen Height: {sg.Window.get_screen_size()[1]}")

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