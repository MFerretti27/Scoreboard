import FreeSimpleGUI as sg # pip install FreeSimpleGUI
from constants import INFO_TXT_SIZE, SCORE_TXT_SIZE, RECORD_TXT_SIZE, HYPHEN_SIZE, FONT, TIMEOUT_SIZE
from constants import COLUMN_WIDTH, COLUMN_HIGHT, NOT_PLAYING_TOP_INFO_SIZE

def gui_setup() -> sg.Window:
    '''Create General user interface'''

    sg.theme("black")

    home_record_layout =[
        [sg.Image("sport_logos/team0_logos/DET.png", key='home_logo')],
        [sg.Text("HOME",font=(FONT, RECORD_TXT_SIZE), key='home_record')]
        ]

    away_record_layout =[
        [sg.Image("sport_logos/team0_logos/PIT.png", key='away_logo'), sg.Push()],
        [sg.Text("AWAY",font=(FONT, RECORD_TXT_SIZE), key='away_record')]
        ]

    score_layout =[[sg.Text(" ",font=(FONT, 50), key='blank_space', pad=(0,100))],
        [sg.Text("24",font=(FONT, SCORE_TXT_SIZE), key='away_score'),
        sg.Text("-",font=(FONT, HYPHEN_SIZE), key='hyphen'),
        sg.Text("24",font=(FONT, SCORE_TXT_SIZE), key='home_score')],
        [sg.Text("", font=(FONT, TIMEOUT_SIZE), key='timeouts')],
        [sg.Image("", key='network_logo', pad=(0,100))]
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
    window = sg.Window("Scoreboard", layout, no_titlebar=True, resizable=True).Finalize()
    window.Maximize()
    window.TKroot.config(cursor="none")

    return window
