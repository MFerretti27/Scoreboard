"""GUI Layout for selecting teams in main menu."""
import FreeSimpleGUI as Sg  # ignore

import settings
from get_data.get_team_league import ALL_DIVISIONS, DIVISION_TEAMS, MLB, NBA, NFL, NHL
from helper_functions.main_menu_helpers import read_teams_from_file


def create_team_selection_layout(window_width: int, league: str) -> list:
    """Create General User Interface for selecting teams to add.

    :param window_width: The width of the screen being used
    "param league: The sports league of the team that the user wants to add
    :return layout: List of elements and how the should be displayed
    """
    checkboxes_per_column = 8
    selected_teams = read_teams_from_file()

    team_names = {
        "MLB": MLB,
        "NHL": NHL,
        "NBA": NBA,
        "NFL": NFL,
    }.get(league, [])

    division_names = ALL_DIVISIONS.get(league, [])

    division_checkboxes_per_column: int = {
        "MLB": 2,
        "NHL": 2,
        "NBA": 2,
        "NFL": 2,
    }.get(league, 2)

    # Common base screen widths
    common_base_widths = [1366, 1920, 1440, 1280]

    # Find the largest base width that doesn't exceed the window width using `max()`
    base_width = max([width for width in common_base_widths if width <= window_width], default=1366)
    scale = window_width / base_width

    max_size = 100
    text_size = min(max_size, max(30, int(50 * scale)))
    bottom_title_txt_size = min(max_size, max(20, int(40 * scale)))
    checkbox_width = min(max_size, max(20, int(20 * scale)))
    checkbox_height = min(max_size, max(2, int(2 * scale)))
    checkbox_txt_size = min(max_size, max(8, int(16 * scale)))
    button_size = min(max_size, max(22, int(30 * scale)))
    update_names_button_size = min(max_size, max(10, int(18 * scale)))
    confirmation_txt_size = min(max_size, max(10, int(24 * scale)))

    team_checkboxes = [
        Sg.Checkbox(team, key=f"{team}", size=(checkbox_width, checkbox_height),
                    font=(settings.FONT, checkbox_txt_size), pad=(0, 0), default=(team in selected_teams))
        for team in team_names
    ]

    # Get whether divisions are already checked by seeing if all teams in the division are selected
    divisions_already_checked = []
    for division in ALL_DIVISIONS.get(league, []):
        if all(team in selected_teams for team in DIVISION_TEAMS[league + " " + division]):
            divisions_already_checked.append(division)
            settings.division_checked = True

    division_checkboxes = [
        Sg.Checkbox(division_name, key=division_name,
                    font=(settings.FONT, checkbox_txt_size), pad=(0, 0),
                    default=division_name in divisions_already_checked)
        for division_name in division_names
    ]

    columns = [
        team_checkboxes[i:i + checkboxes_per_column]
        for i in range(0, len(team_checkboxes), checkboxes_per_column)
    ]

    column_layouts = [
        Sg.Column([[cb] for cb in col], pad=(0, 0), element_justification="Center") for col in columns
    ]

    division_columns = [
        division_checkboxes[i:i + division_checkboxes_per_column]
        for i in range(0, len(division_checkboxes), division_checkboxes_per_column)
    ]

    division_column_layouts = [
        Sg.Column([[cb] for cb in col], pad=(0, 0), element_justification="Center") for col in division_columns
    ]

    return [
        [Sg.Push(), Sg.Text(f"Choose {league} Team to Add", font=(settings.FONT, text_size, "underline")), Sg.Push()],
         [Sg.Push(),
          Sg.Button("Update Names", font=(settings.FONT, update_names_button_size)),
         Sg.Push(),
         ],
        [Sg.VPush()],
        [
         Sg.Push(), *column_layouts, Sg.Push(),
         ],
        [Sg.VPush()],
        [Sg.Push(),
         Sg.Text("Select Division to Add", font=(settings.FONT, bottom_title_txt_size, "underline")),
         Sg.Push(),
         ],
        [
         Sg.Push(), *division_column_layouts, Sg.Push(),
        ],
        [Sg.VPush()],
        [
         Sg.Push(),
         Sg.Text("", font=(settings.FONT, confirmation_txt_size), key="teams_added", text_color="green"),
         Sg.Push(),
         ],
        [
         Sg.Push(),
         Sg.Text("", font=(settings.FONT, confirmation_txt_size), key="teams_removed", text_color="red"),
         Sg.Push(),
         ],
         [Sg.VPush()],
        [Sg.Push(),
         Sg.Button("Save", font=(settings.FONT, button_size)), Sg.Button("Back", font=(settings.FONT, button_size)),
         Sg.Push(),
         ],
        [Sg.VPush()],
    ]
