"""GUI Layout screen for main menu."""
import FreeSimpleGUI as Sg  # type: ignore[import]

import settings
from get_data.get_team_league import MLB, NBA, NFL, NHL


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
    count = int(len(MLB) + len(NFL) + len(NBA) + len(NHL))
    return [
        [Sg.Push(), Sg.Text("Major League Scoreboard", font=(settings.FONT, text_size)), Sg.Push()],
        [Sg.Push(),
         Sg.Button("Restore from Version", font=(settings.FONT, update_button_size), key="restore_button"),
         Sg.Button("Check for Update", font=(settings.FONT, update_button_size), key="update_button"),
         Sg.Button("Connect to Internet", font=(settings.FONT, update_button_size)),
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
        [Sg.VPush()],
        [Sg.Push(),
         Sg.Text("", font=(settings.FONT, message_size), key="download_message"),
         Sg.Push()],
        [Sg.Push(),
         Sg.ProgressBar(count, key="PROGRESS_BAR", size=(window_width, message_size),
                        bar_color=("green", "white"), visible=False),
         Sg.Push()],
        [Sg.VPush()],
    ]
