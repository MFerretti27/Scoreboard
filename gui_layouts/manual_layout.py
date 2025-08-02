"""GUI Layout screen for showing instructions in main menu."""
import FreeSimpleGUI as Sg  # type: ignore[import]

import settings


def create_instructions_layout(window_width: int) -> list:
    """Create the layout for instructions screen.

    :param window_width: The width of the screen being used

    :return layout: List of elements and how the should be displayed
    """
    common_base_widths = [1366, 1920, 1440, 1280]
    base_width = max([width for width in common_base_widths if width <= window_width], default=1366)
    scale = window_width / base_width
    max_size = 100
    title_size = min(max_size, max(60, int(65 * scale)))
    text_size = min(max_size, max(20, int(25 * scale)))
    button_size = min(max_size, max(48, int(50 * scale)))
    instructions_size = min(max_size, max(25, int(20 * scale)))
    return [
        [Sg.Text("Manual", font=(settings.FONT, title_size, "underline"), justification="center", expand_x=True)],
        [Sg.Multiline(help_text, size=(window_width, instructions_size), disabled=True,
                      no_scrollbar=False, font=("Courier", text_size))],
        [
            [Sg.VPush()],
            Sg.Push(),
            Sg.Button("Back", font=(settings.FONT, button_size)),
            Sg.Push(),
        ],
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
