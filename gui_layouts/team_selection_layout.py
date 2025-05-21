"""GUI Layout for selecting teams in main menu."""
import FreeSimpleGUI as sg  # type: ignore import warning
from get_data.get_team_league import MLB, NHL, NBA, NFL
import settings
from helper_functions.main_menu_helpers import read_teams_from_file


def create_team_selection_layout(window_width: int, league: str) -> list:
    checkboxes_per_column = 8
    selected_teams = read_teams_from_file()

    team_names = {
        "MLB": MLB,
        "NHL": NHL,
        "NBA": NBA,
        "NFL": NFL
    }.get(league, [])

    # Common base screen widths
    common_base_widths = [1366, 1920, 1440, 1280]

    # Find the largest base width that doesn't exceed the window width using `max()`
    base_width = max([width for width in common_base_widths if width <= window_width], default=1366)
    scale = window_width / base_width

    max_size = 100
    text_size = min(max_size, max(60, int(65 * scale)))
    checkbox_width = min(max_size, max(10, int(20 * scale)))
    checkbox_height = min(max_size, max(2, int(2 * scale)))
    checkbox_txt_size = min(max_size, max(20, int(22 * scale)))
    button_size = min(max_size, max(48, int(50 * scale)))
    confirmation_txt_size = min(max_size, max(10, int(24 * scale)))

    team_checkboxes = [
        sg.Checkbox(team, key=f"{team}", size=(checkbox_width, checkbox_height),
                    font=(settings.FONT, checkbox_txt_size), pad=(0, 0), default=(team in selected_teams))
        for team in team_names
    ]

    columns = [
        team_checkboxes[i:i + checkboxes_per_column]
        for i in range(0, len(team_checkboxes), checkboxes_per_column)
    ]

    column_layouts = [
        sg.Column([[cb] for cb in col], pad=(0, 0), element_justification='Center') for col in columns
    ]

    layout = [
        [sg.VPush()],
        [sg.Push(), sg.Text(f"Choose {league} Team to Add", font=(settings.FONT, text_size, "underline")), sg.Push()],
        [sg.VPush()],
        [[sg.VPush()],
         sg.Push(), *column_layouts, sg.Push(),
         [sg.VPush()],],
        [sg.VPush()],
        [[sg.VPush()],
         sg.Push(),
         sg.Text("", font=(settings.FONT, confirmation_txt_size), key="teams_added", text_color='green'),
         sg.Push(),
         [sg.VPush()],
         ],
        [[sg.VPush()],
         sg.Push(),
         sg.Text("", font=(settings.FONT, confirmation_txt_size), key="teams_removed", text_color='red'),
         sg.Push(),
         [sg.VPush()],
         ],
        [sg.Push(),
         sg.Button("Save", font=(settings.FONT, button_size)), sg.Button("Back", font=(settings.FONT, button_size)),
         sg.Push()
         ],
        [sg.VPush()],
    ]
    return layout
