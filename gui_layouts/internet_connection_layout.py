"""Internet Connection screen for main menu."""
import FreeSimpleGUI as Sg  # type: ignore[import]

import settings


def create_internet_connection_layout(window_width: int) -> list:
    """Create main screen layout.

    :param window_width: The width of the screen being used

    :return layout: List of elements and how the should be displayed
    """
    # Common base screen widths
    common_base_widths = [1366, 1920, 1440, 1280]
    # Find the largest base width that doesn't exceed the window width using `max()`
    base_width = max([width for width in common_base_widths if width <= window_width], default=1366)
    scale = window_width / base_width
    max_size = 100

    title_size = min(max_size, max(60, int(65 * scale)))
    text_size = min(max_size, max(38, int(40 * scale)))
    button_size = max(12, window_width // 40)
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
         Sg.Input("", enable_events=True, key="SSID", font=(settings.FONT, input_size), justification="left"),
         Sg.Push(),
         ],
        [Sg.Push(),
         Sg.Text("Enter Password: ", font=(settings.FONT, text_size), justification="center"),
         Sg.Input("", enable_events=True, key="password", font=(settings.FONT, input_size), justification="left"),
         Sg.Push(),
         ],
         [Sg.VPush()],
         [
          Sg.Push(), Sg.Text("", font=(settings.FONT, text_size), key="connection_message"),
          Sg.Push(),
          ],
          [Sg.VPush()],
          [Sg.Push(), Sg.Button("Open Keyboard", font=(settings.FONT, button_size), key="open_keyboard"), Sg.Push()],
          [Sg.VPush()],
         [Sg.Push(),
         Sg.Button("Save", font=(settings.FONT, button_size)),
         Sg.Button("Back", font=(settings.FONT, button_size)),
         Sg.Push(),
         ],
         [Sg.VPush()],
    ]
