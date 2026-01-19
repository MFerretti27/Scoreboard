"""GUI Layout screen for setting team display order in main menu."""
from __future__ import annotations

import FreeSimpleGUI as Sg  # type: ignore[import]

import settings
from constants import colors, messages, ui_keys
from constants.sizing_utils import calculate_title_size, get_responsive_scale


def create_order_teams_layout(window_width: int) -> list:
    """Create the layout for screen allowing user to change order of teams displayed.

    :param window_width: The width of the screen being used
    :return layout: List of elements and how the should be displayed
    """
    _, scale = get_responsive_scale(window_width)

    max_size = 100
    title_size = calculate_title_size(scale)
    button_size = min(max_size, max(22, int(30 * scale)))
    list_box_size_height = min(max_size, max(10, int(15 * scale)))
    list_box_size_width = min(max_size, max(18, int(40 * scale)))
    list_box_txt_size = min(max_size, max(16, int(22 * scale)))
    message_size = min(max_size, max(6, int(22 * scale)))
    move_button_size = min(max_size, max(12, int(20 * scale)))

    teams = settings.read_settings().get("teams", [])
    team_names = [team[0] for team in teams]

    return [
        [Sg.Push(), Sg.Text("Set Team Display Order", font=(settings.FONT, title_size, "underline")), Sg.Push()],
        [Sg.Push(),
         Sg.Text("The order here will be the order teams are displayed in (top to bottom), select team to move",
                 font=(settings.FONT, message_size)),
         Sg.Push()],
        [Sg.Push(),
         Sg.Listbox(team_names, size=(list_box_size_width, list_box_size_height),
                    font=(settings.FONT, list_box_txt_size),
                    key=ui_keys.TEAM_ORDER, enable_events=True,
                    ),
         Sg.Push(),
         ],
        [Sg.Push(),
         Sg.Button(messages.BUTTON_MOVE_UP, font=(settings.FONT, move_button_size)),
         Sg.Button(messages.BUTTON_MOVE_DOWN, font=(settings.FONT, move_button_size)),
         Sg.Push(),
         ],
        [Sg.Push(),
         Sg.Text("", font=(settings.FONT, button_size), key=ui_keys.ORDER_MESSAGE, text_color=colors.SUCCESS_GREEN),
         Sg.Push(),
         ],
         [Sg.VPush()],
        [
         Sg.Push(),
         Sg.Button(messages.BUTTON_SAVE, font=(settings.FONT, button_size)),
         Sg.Button(messages.BUTTON_BACK, font=(settings.FONT, button_size)),
         Sg.Push(),
         ],
         [Sg.VPush()],
    ]
