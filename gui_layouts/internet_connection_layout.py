"""Internet Connection screen for main menu."""
from __future__ import annotations

import FreeSimpleGUI as Sg  # type: ignore[import]

import settings
from constants import messages, ui_keys
from constants.sizing_utils import calculate_button_size, calculate_title_size, get_responsive_scale


def create_internet_connection_layout(window_width: int) -> list:
    """Create main screen layout.

    :param window_width: The width of the screen being used
    :return layout: List of elements and how the should be displayed
    """
    _, scale = get_responsive_scale(window_width)
    max_size = 100

    title_size = calculate_title_size(scale, min_size=60, base_multiplier=65)
    text_size = min(max_size, max(38, int(40 * scale)))
    button_size = calculate_button_size(scale, min_size=12, base_multiplier=34)
    input_size = min(max_size, max(20, int(24 * scale)))
    help_message = min(max_size, max(12, int(16 * scale)))
    return [
        [Sg.Push(), Sg.Text("Connect to Internet", font=(settings.FONT, title_size, "underline")), Sg.Push()],
        [Sg.Push(),
            Sg.Text("Please Enter WIFI name and Password exactly (case sensitive)", font=(settings.FONT, help_message),
                    justification="center"),
            Sg.Push(),
        ],
        [Sg.VPush()],
        [Sg.VPush()],
        [Sg.Push(),
         Sg.Text("Enter SSID: ", font=(settings.FONT, text_size), justification="center"),
         Sg.Input("", enable_events=True, key=ui_keys.SSID, font=(settings.FONT, input_size), justification="left"),
         Sg.Push(),
         ],
        [Sg.Push(),
         Sg.Text("Enter Password: ", font=(settings.FONT, text_size), justification="center"),
         Sg.Input("", enable_events=True, key=ui_keys.PASSWORD, font=(settings.FONT, input_size), justification="left"),
         Sg.Push(),
         ],
         [Sg.VPush()],
         [
          Sg.Push(), Sg.Text("", font=(settings.FONT, text_size), key=ui_keys.CONNECTION_MESSAGE),
          Sg.Push(),
          ],
         [Sg.VPush()],
          [
              Sg.Push(),
              Sg.Button(
                  "Open Keyboard",
                  font=(settings.FONT, button_size),
                  key=ui_keys.OPEN_KEYBOARD,
              ),
              Sg.Push(),
          ],
          [Sg.VPush()],
         [Sg.Push(),
         Sg.Button(messages.BUTTON_SAVE, font=(settings.FONT, button_size)),
         Sg.Button(messages.BUTTON_BACK, font=(settings.FONT, button_size)),
         Sg.Push(),
         ],
         [Sg.VPush()],
    ]
