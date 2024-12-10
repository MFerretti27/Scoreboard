'''Function to Create GUI using FreeSimpleGUI'''

import FreeSimpleGUI as sg # pip install FreeSimpleGUI
from constants import *
from constants import COLUMN_WIDTH, COLUMN_HIGHT, NOT_PLAYING_TOP_INFO_SIZE
from constants import SPACE_BETWEEN_SCORE_AND_NETWORK_LOGO, SPACE_BETWEEN_TOP_AND_LOGOS, SPACE_BETWEEN_TOP_AND_SCORE

def gui_setup() -> sg.Window:
    '''Create General User Interface'''

    sg.theme("black")

    home_record_layout =[
        [sg.Image("sport_logos/team0_logos/DET.png", key='home_logo', pad=(0, SPACE_BETWEEN_TOP_AND_LOGOS, 0, 0))],
        [sg.Text("HOME",font=(FONT, RECORD_TXT_SIZE), key='home_record')]
        ]

    away_record_layout =[
        [sg.Image("sport_logos/team0_logos/PIT.png", key='away_logo', pad=(0, SPACE_BETWEEN_TOP_AND_LOGOS, 0, 0)), sg.Push()],
        [sg.Text("AWAY",font=(FONT, RECORD_TXT_SIZE), key='away_record')]
        ]

    score_layout =[
        [sg.Text("24",font=(FONT, SCORE_TXT_SIZE), key='away_score', pad=(0, SPACE_BETWEEN_TOP_AND_SCORE, 0, 0)),
        sg.Text("-",font=(FONT, HYPHEN_SIZE), key='hyphen'),
        sg.Text("24",font=(FONT, SCORE_TXT_SIZE), key='home_score')],
        [sg.Text("", font=(FONT, TIMEOUT_SIZE), key='timeouts')],
        [sg.Image("", key='network_logo', pad=(0, SPACE_BETWEEN_SCORE_AND_NETWORK_LOGO, 0, 0))]
        ]

    layout = [[
        sg.Push(),
        sg.Column(away_record_layout, element_justification='center', size=(COLUMN_WIDTH,COLUMN_HIGHT)),
        sg.Frame("",score_layout, element_justification='center', border_width=0, size=(COLUMN_WIDTH,COLUMN_HIGHT)),
        sg.Column(home_record_layout, element_justification='center', size=(COLUMN_WIDTH,COLUMN_HIGHT)),
        sg.Push()
        ],
        [sg.VPush()],[sg.Push(), sg.Text("Top Info",font=(FONT, NOT_PLAYING_TOP_INFO_SIZE), key='top_info'), sg.Push()],
        [sg.VPush()],[sg.Push(), sg.Text("Bottom Info",font=(FONT, INFO_TXT_SIZE), auto_size_text= True, size=(None,None), key='bottom_info'), sg.Push()],[sg.VPush()],[sg.Push()],
        [sg.Push(), sg.Text("Created by: Matthew Ferretti",font=(FONT, 10), key='personal')]
        ]

    # Create the window
    window = sg.Window("Scoreboard", layout, no_titlebar=True, resizable=True, return_keyboard_events=True).Finalize()
    window.Maximize()
    window.TKroot.config(cursor="none")

    return window
