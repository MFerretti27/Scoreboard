"""GUI Layout screen for main menu."""
import FreeSimpleGUI as Sg  # type: ignore

import settings


def create_main_layout(window_width: int) -> list:
    """Create main screen layout.

    :param window_width: The width of the screen being used

    :return layout: List of elements and how the should be displayed
    """
    Sg.theme("LightBlue6")  # Set theme for main screen
    text_size = max(12, window_width // 20)
    button_size = max(12, window_width // 40)
    update_button_size = max(12, window_width // 80)
    message_size = max(12, window_width // 60)
    return [
        [Sg.Push(), Sg.Text("Major League Scoreboard", font=(settings.FONT, text_size)), Sg.Push()],
        [Sg.Push(),
         Sg.Button("Restore from Version", font=(settings.FONT, update_button_size), key="restore_button"),
         Sg.Button("Check for Update", font=(settings.FONT, update_button_size), key="update_button"),
         Sg.Push(),
         ],
        [
            Sg.Push(),
            Sg.Column(
                [
                    [Sg.Combo([], key="versions", visible=False,
                              font=(settings.FONT, update_button_size), size=(20, 1))],
                ],
                element_justification="center",
                justification="center",
                expand_x=True,
            ),
            Sg.Push(),
        ],
        [Sg.Push(), Sg.Text("", font=(settings.FONT, message_size), key="update_message"), Sg.Push()],
        [Sg.VPush()],
        [
            Sg.Push(),
            Sg.Button("Set Team Order", font=(settings.FONT, button_size)),
            Sg.Push(),
        ],
        [
            Sg.Push(),
            Sg.Button("Add MLB team", font=(settings.FONT, button_size)),
            Sg.Button("Add NHL team", font=(settings.FONT, button_size)),
            Sg.Button("Add NBA team", font=(settings.FONT, button_size)),
            Sg.Button("Add NFL team", font=(settings.FONT, button_size), pad=(0, button_size)),
            Sg.Push(),
        ],
        [
            Sg.Button("Manual", font=(settings.FONT, button_size), expand_x=True),
            Sg.Button("Settings", font=(settings.FONT, button_size), expand_x=True),
        ],
        [Sg.Button("Start", font=(settings.FONT, button_size), expand_x=True)],
        [
            Sg.Push(),
            Sg.Column([
                [Sg.Multiline(size=(80, 20), key="terminal_output",
                              autoscroll=True, disabled=True,
                              background_color=Sg.theme_background_color(),
                              text_color=Sg.theme_text_color(),
                              sbar_background_color=Sg.theme_background_color(),
                              sbar_trough_color=Sg.theme_background_color(),
                              no_scrollbar=True, sbar_relief=Sg.RELIEF_FLAT,
                              expand_x=True, visible=False)],
            ], expand_x=True),
            Sg.Push(),
        ],
        [Sg.VPush()],
    ]
