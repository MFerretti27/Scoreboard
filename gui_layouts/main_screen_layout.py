
import FreeSimpleGUI as sg  # type: ignore import warning
import settings


# List of previous versions for the restore button
pervious_versions = []


def create_main_layout(window_width: int) -> list:
    sg.theme("LightBlue6")  # Set theme for main screen
    text_size = max(12, window_width // 20)
    button_size = max(12, window_width // 40)
    update_button_size = max(12, window_width // 80)
    message_size = max(12, window_width // 60)
    layout = [
        [sg.Push(), sg.Text("Major League Scoreboard", font=(settings.FONT, text_size)), sg.Push()],
        [sg.Push(),
         sg.Button("Restore from Version", font=(settings.FONT, update_button_size), key="restore_button"),
         sg.Button("Check for Update", font=(settings.FONT, update_button_size), key="update_button"),
         sg.Push()
         ],
        [
            sg.Push(),
            sg.Column(
                [
                    [sg.Combo(pervious_versions, key="versions", visible=False,
                              font=(settings.FONT, update_button_size), size=(20, 1))]
                ],
                element_justification="center",
                justification="center",
                expand_x=True
            ),
            sg.Push()
        ],
        [sg.Push(), sg.Text("", font=(settings.FONT, message_size), key="update_message"), sg.Push()],
        [sg.VPush()],
        [
            sg.Push(),
            sg.Button("Set Team Order", font=(settings.FONT, button_size)),
            sg.Push(),
        ],
        [
            sg.Push(),
            sg.Button("Add MLB team", font=(settings.FONT, button_size)),
            sg.Button("Add NHL team", font=(settings.FONT, button_size)),
            sg.Button("Add NBA team", font=(settings.FONT, button_size)),
            sg.Button("Add NFL team", font=(settings.FONT, button_size), pad=(0, button_size)),
            sg.Push(),
        ],
        [
            sg.Button("Manual", font=(settings.FONT, button_size), expand_x=True),
            sg.Button("Settings", font=(settings.FONT, button_size), expand_x=True),
        ],
        [sg.Button("Start", font=(settings.FONT, button_size), expand_x=True)],
        [
            sg.Push(),
            sg.Column([
                [sg.Multiline(size=(80, 20), key="terminal_output",
                              autoscroll=True, disabled=True,
                              background_color=sg.theme_background_color(),
                              text_color=sg.theme_text_color(),
                              sbar_background_color=sg.theme_background_color(),
                              sbar_trough_color=sg.theme_background_color(),
                              no_scrollbar=True, sbar_relief=sg.RELIEF_FLAT,
                              expand_x=True, visible=False)]
            ], expand_x=True),
            sg.Push(),
        ],
        [sg.VPush()],
    ]
    return layout
