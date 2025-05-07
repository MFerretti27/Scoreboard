'''Module to Create and modify scoreboard GUI using FreeSimpleGUI'''

import FreeSimpleGUI as sg  # type: ignore
from settings import *
from get_data.get_team_logos import get_random_logo
import math
import settings
import time
import platform
from get_data.get_team_league import append_team_array
from main import set_screen
import subprocess
import sys
import gc


def gui_setup() -> sg.Window:
    '''Create General User Interface'''

    sg.theme("black")
    set_screen()  # Set the screen to display on
    append_team_array(settings.teams)  # Get the team league and sport name
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

    home_logo_layout = [
        [sg.Push()],
        [sg.VPush()],
        [sg.Image(f"images/sport_logos/{files[0][0]}/{files[0][1]}.png", key='home_logo', pad=((0, 0), (0, 0)))],
        [sg.VPush()],
        [sg.Push()],
    ]

    away_logo_layout = [
        [sg.Push()],
        [sg.VPush()],
        [sg.Image(f"images/sport_logos/{files[1][0]}/{files[1][1]}.png", key='away_logo', pad=((0, 0), (0, 0)))],
        [sg.VPush()],
        [sg.Push()],
    ]

    away_record_layout = [
        [sg.Push()],
        [sg.Text("AWAY", font=(FONT, RECORD_TXT_SIZE), key='away_record', pad=((0, 0), (0, 0)))],
        [sg.Push()],
    ]
    home_record_layout = [
        [sg.VPush()],
        [sg.Push()],
        [sg.Text("HOME", font=(FONT, RECORD_TXT_SIZE), key='home_record', pad=((0, 0), (0, 0)))],
        [sg.Push()],
    ]

    above_score_layout = [
        [sg.VPush()],
        [sg.Push()],
        [sg.Text("", font=(FONT, TOP_TXT_SIZE), key='above_score_txt', pad=((0, 0), (space_between_score, 0)))],
        [sg.Push()],
    ]

    score_layout = [
        [sg.Text("Sco", font=(FONT, SCORE_TXT_SIZE), key='away_score', pad=((0, 0), (space_between_score, 0))),
         sg.Text("-", font=(FONT, HYPHEN_SIZE), key='hyphen', pad=((0, 0), (space_between_score, 0))),
         sg.Text("re", font=(FONT, SCORE_TXT_SIZE), key='home_score', pad=((0, 0), (space_between_score , 0)))],
        [sg.Text("", font=(FONT, TIMEOUT_SIZE), key='away_timeouts', pad=((0, 50), (0 , 25))),
         sg.Text("", font=(FONT, TIMEOUT_SIZE), key='home_timeouts', pad=((50, 0), (0 , 25)))],
    ]

    below_score_image = [
        [sg.VPush()],
        [sg.Image("", key='under_score_image')],
        [sg.VPush()],
    ]

    top_info_layout = [[sg.VPush()], [sg.Push(), sg.Text("", font=(FONT, NOT_PLAYING_TOP_INFO_SIZE), key='top_info'), sg.Push()]]
    bottom_info_layout = [[sg.VPush()], [sg.Push(), sg.Text("Fetching Data...", font=(FONT, INFO_TXT_SIZE), auto_size_text=True, size=(None, None), key='bottom_info'), sg.Push()],[sg.VPush()],[sg.Push()]]

    layout = [
    [
        sg.Column([  # Vertical stack for away team
            [sg.Frame("", away_logo_layout, element_justification='center', border_width=0, size=(column_width, column_height * (4/5)))],
            [sg.Frame("", away_record_layout, element_justification='center', border_width=0, size=(column_width, column_height * (1/5)))]
        ], element_justification='center', pad=((0, 0), (0, 0))),
        sg.Column([  # Vertical score
            [sg.Frame("", above_score_layout, element_justification='center', border_width=0, size=(column_width, column_height * (1/4)))],
            [sg.Frame("", score_layout, element_justification='center', border_width=0, size=(column_width, column_height * (7/16)))],
            [sg.Frame("", below_score_image, element_justification='center', border_width=0, size=(column_width, column_height * (5/16)))]
        ], element_justification='center', pad=((0, 0), (0, 0))),
        sg.Column([  # Vertical stack for home team
            [sg.Frame("", home_logo_layout, element_justification='center', border_width=0, size=(column_width, column_height * (4/5)))],
            [sg.Frame("", home_record_layout, element_justification='center', border_width=0, size=(column_width, column_height * (1/5)))]
        ], element_justification='center', pad=((0, 0), (0, 0))),
    ],
        [sg.Frame("", top_info_layout, element_justification='center', border_width=0, size=(window_width, info_height))],
        [sg.Frame("", bottom_info_layout, element_justification='center', border_width=0, size=(window_width, info_height))],
        [sg.Push(), sg.Text("Created by: Matthew Ferretti", font=(FONT, 10), key='personal')]
    ]

    # Create the window
    window = sg.Window("Scoreboard", layout, no_titlebar=False, resizable=True, return_keyboard_events=True).Finalize()
    
    # Maximize does not work on MacOS, so we use attributes to set fullscreen
    if platform.system() == 'Darwin':
        window.TKroot.attributes('-fullscreen', True)
    else:
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

def reset_window_elements(window: sg.Window) -> None:
    '''Reset window elements to default values'''
    window['top_info'].update(value='', font=(FONT, settings.NOT_PLAYING_TOP_INFO_SIZE), text_color='white')
    window['bottom_info'].update(value='', font=(FONT, settings.INFO_TXT_SIZE), text_color='white')
    window['home_timeouts'].update(value='', font=(FONT, settings.TIMEOUT_SIZE), text_color='white')
    window['away_timeouts'].update(value='', font=(FONT, settings.TIMEOUT_SIZE), text_color='white')
    window['home_record'].update(value='', font=(FONT, settings.RECORD_TXT_SIZE), text_color='white')
    window['away_record'].update(value='', font=(FONT, settings.RECORD_TXT_SIZE), text_color='white')
    window['home_score'].update(value='', font=(FONT, settings.SCORE_TXT_SIZE), text_color='white')
    window['away_score'].update(value='', font=(FONT, settings.SCORE_TXT_SIZE), text_color='white')
    window['above_score_txt'].update(value='', font=(FONT, settings.NOT_PLAYING_TOP_INFO_SIZE), text_color='white')
    window["hyphen"].update(value='-', font=(FONT, settings.HYPHEN_SIZE), text_color='white')


def check_events(window: sg.Window, events, currently_playing=False) -> None:
    '''Check for events in the window'''
    if events[0] == sg.WIN_CLOSED or 'Escape' in events[0]:
        window.close()
        gc.collect()  # Clean up memory
        time.sleep(0.5)  # Give OS time to destroy the window
        subprocess.Popen([sys.executable, "-m", "screens.main_screen", *sys.argv[1:]])
        sys.exit()

    elif ('Up' in events[0]):
        settings.no_spoiler_mode = True
    elif ('Down' in events[0]):
        settings.no_spoiler_mode = False

    if currently_playing:
        if 'Caps_Lock' in events[0] and not settings.stay_on_team:
            print("Caps Lock key pressed, Staying on team")
            settings.stay_on_team = True
            window["bottom_info"].update(value="Staying on Team")
            window.refresh()
            time.sleep(5)
        elif ('Shift_L' in events[0] or 'Shift_R' in events[0]) and settings.stay_on_team:
            print("shift key pressed, Rotating teams")
            settings.stay_on_team = False
            window["bottom_info"].update(value="Rotating Teams")
            window.refresh()
            time.sleep(5)
        elif 'Left' in events[0]:
            print("left key pressed, delay off")
            settings.delay = False
            window["bottom_info"].update(value="Turning delay OFF")
            window.refresh()
            time.sleep(5)
        elif 'Right' in events[0]:
            print("Right key pressed, delay on")
            settings.delay = True
            window["bottom_info"].update(value="Turning delay ON")
            window.refresh()
            time.sleep(5)


def set_spoiler_mode(window: sg.Window, currently_playing: bool, team_info: dict) -> sg.Window:
    if currently_playing:
        window["top_info"].update(value="Game Currently Playing")
    else:
        window["top_info"].update(value="Will Not Display Game Info")
    window['bottom_info'].update(value="No Spoiler Mode On")
    window["under_score_image"].update(filename='')
    if "@" not in team_info["above_score_txt"]: # Only remove if text doesn't contain team names
        window["above_score_txt"].update(value='')
    window["home_score"].update(value='0', text_color='white')
    window["away_score"].update(value='0', text_color='white')
    window['home_timeouts'].update(value='')
    window['away_timeouts'].update(value='')
    window['home_record'].update(value='')
    window['away_record'].update(value='')

    return window


def resize_text():
    window_width = sg.Window.get_screen_size()[0]
    # window_height = sg.Window.get_screen_size()[1]

    # Common base screen widths
    common_base_widths = [1366, 1920, 1440, 1280]
    # Find the largest base width that doesn't exceed the window width using `max()`
    base_width = max([width for width in common_base_widths if width <= window_width], default=1366)
    scale = window_width / base_width

    print(scale)
    print(base_width)

    max_size = 200
    settings.SCORE_TXT_SIZE = min(max_size, max(60, int(150 * scale)))
    settings.INFO_TXT_SIZE = min(max_size, max(60, int(90 * scale)))
    settings.RECORD_TXT_SIZE = min(max_size, max(60, int(96 * scale)))
    settings.CLOCK_TXT_SIZE = min(max_size, max(60, int(204 * scale)))
    settings.HYPHEN_SIZE = min(max_size, max(60, int(84 * scale)))
    settings.TIMEOUT_SIZE = min(max_size, max(24, int(34 * scale)))
    settings.NBA_TOP_INFO_SIZE = min(max_size, max(50, int(56 * scale)))
    settings.MLB_BOTTOM_INFO_SIZE = min(max_size, max(60, int(80 * scale)))
    settings.PLAYING_TOP_INFO_SIZE = min(max_size, max(60, int(76 * scale)))
    settings.NOT_PLAYING_TOP_INFO_SIZE = min(max_size, max(30, int(30 * scale)))
    settings.TOP_TXT_SIZE = min(max_size, max(60, int(80 * scale)))

    print(f"score txt size:{settings.SCORE_TXT_SIZE}")
    print(f"info txt size:{settings.INFO_TXT_SIZE}")
    print(f"record txt size:{settings.RECORD_TXT_SIZE}")
    print(f"clock txt size:{settings.CLOCK_TXT_SIZE}")
    print(f"hyphen txt size:{settings.HYPHEN_SIZE}")
    print(f"timeout txt size:{settings.TIMEOUT_SIZE}")
    print(f"nba top txt size:{settings.NBA_TOP_INFO_SIZE}")
    print(f"mlb bottom txt size:{settings.MLB_BOTTOM_INFO_SIZE}")
    print(f"playing txt size:{settings.PLAYING_TOP_INFO_SIZE}")
    print(f"not playing top txt size:{settings.NOT_PLAYING_TOP_INFO_SIZE}")
    print(f"top txt size:{settings.TOP_TXT_SIZE}")
