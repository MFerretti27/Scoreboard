"""GUI Layout screen for setting team display order in main menu."""
import FreeSimpleGUI as sg  # type: ignore
from helper_functions.main_menu_helpers import load_teams_order
import settings


def create_order_teams_layout(window_width: int) -> list:
    # Common base screen widths
    common_base_widths = [1366, 1920, 1440, 1280]
    # Find the largest base width that doesn't exceed the window width using `max()`
    base_width = max([width for width in common_base_widths if width <= window_width], default=1366)
    scale = window_width / base_width

    max_size = 100
    title_size = min(max_size, max(60, int(65 * scale)))
    button_size = min(max_size, max(38, int(40 * scale)))
    list_box_size_height = min(max_size, max(10, int(15 * scale)))
    list_box_size_width = min(max_size, max(18, int(40 * scale)))
    list_box_txt_size = min(max_size, max(18, int(24 * scale)))
    message_size = min(max_size, max(6, int(22 * scale)))
    move_button_size = min(max_size, max(38, int(20 * scale)))

    teams = load_teams_order()
    team_names = [team[0] for team in teams]

    layout = [
        [sg.Push(), sg.Text("Reorder Teams", font=(settings.FONT, title_size, "underline")), sg.Push()],
        [sg.Push(),
         sg.Text("The order here will be the order teams are displayed in", font=(settings.FONT, message_size)),
         sg.Push()],
        [sg.Push(),
         sg.Listbox(team_names, size=(list_box_size_width, list_box_size_height),
                    font=(settings.FONT, list_box_txt_size),
                    key='TEAM_ORDER', enable_events=True,
                    ),
         sg.Push(),
         [sg.VPush()],
         ],
        [sg.Push(),
         sg.Button('Move Up', font=(settings.FONT, move_button_size), pad=(10, button_size)),
         sg.Button('Move Down', font=(settings.FONT, move_button_size), pad=(10, button_size)),
         sg.Push(),
         ],
        [sg.Push(),
         sg.Text("", font=(settings.FONT, button_size), key="order_message", text_color='Green'),
         sg.Push()
         ],
        [[sg.VPush()],
         sg.Push(),
         sg.Button("Save", font=(settings.FONT, button_size)),
         sg.Button("Back", font=(settings.FONT, button_size)),
         sg.Push(),
         ],
    ]
    return layout
