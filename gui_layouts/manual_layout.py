"""GUI Layout screen for showing instructions in main menu."""
from __future__ import annotations

import FreeSimpleGUI as Sg  # type: ignore[import]

import settings
from constants import messages
from constants.sizing_utils import (
    calculate_button_size,
    calculate_message_size,
    calculate_text_size,
    get_responsive_scale,
)


def create_instructions_layout(window_width: int) -> list:
    """Create the layout for instructions screen.

    :param window_width: The width of the screen being used

    :return layout: List of elements and how the should be displayed
    """
    _, scale = get_responsive_scale(window_width)
    title_size = min(100, max(40, int(65 * scale)))
    text_size = calculate_text_size(scale, min_size=20, base_multiplier=25)
    button_size = calculate_button_size(scale, min_size=22, base_multiplier=30)
    instructions_size = calculate_message_size(scale, min_size=10, base_multiplier=20)
    return [
        [Sg.Text("Manual", font=(settings.FONT, title_size, "underline"), justification="center", expand_x=True)],
        [Sg.Multiline(help_text, size=(window_width, instructions_size), disabled=True,
                      no_scrollbar=False, font=("Courier", text_size))],
        [Sg.VPush()],
        [
            Sg.Push(),
            Sg.Button(messages.BUTTON_BACK, font=(settings.FONT, button_size)),
            Sg.Push(),
        ],
        [Sg.VPush()],
    ]


help_text = """
Controls
---------
Escape - Return to main menu.
Caps Lock - Stay on the currently displayed team (only if multiple teams are playing).
Shift - Resume rotating between multiple teams.
Right Arrow - Turn on live data delay, this will put a delay on live data shown.
              The amount of delay is set in settings.
Left Arrow - Turn off live data delay, this will show live game info as
             soon as its available.
Up Arrow - Enter "No Spoiler Mode," hiding scores, records, and game details.
Down Arrow - Exit "No Spoiler Mode," showing scores, records, and game details.


How Data is Displayed
------------------------
- Only displays teams that have upcoming or recent games (not off-season or long gaps).
- Completed games stay visible for 7 days unless new data replaces them (can be changed in settings).
- Prioritizes displaying teams currently playing (Unless changed in settings):
    - One team playing: display only that team.
    - Multiple teams playing: rotate between them.
        - Pressing Up Arrow on keyboard stops rotating between team, pressing
          Down Arrow resumes rotation.
- Pressing Caps Lock hides game info in "No Spoiler Mode."


How Data is Collected
------------------------
- Primary source: ESPN API.
- Secondary Source: MLBStats-API (baseball), nba_api (basketball), nhlapi (hockey).
- If only primary source fails:
    - Tries backup APIs based on the sport.
- If only secondary sources fail:
    - Displays basic info from ESPN.
    - Some details (pitch count, bonus status, shots on goal, etc) might be missing.
- If all data fetching fails:
    - Shows a clock until connection/data is restored.
- Logos are gotten when first running for the first time
    - If you need to re-download logos such as if a team has updated their logo you
      can re-download logos by selecting ""Always Get Logos when Starting" in settings.


Clock Screen
--------------
- Displays a clock:
    - If data fetching fails.
    - If internet connection is lost.
    - If none of selected teams have data to display.
- Automatically returns displaying team info:
    - Once data fetching is successful.
    - Internet connection is restored.
    - One of selected teams has data to display.
- A message on clock screen will appear telling why clock is displaying.
"""
