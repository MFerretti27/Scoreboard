"""Helper functions used in main menu."""
import ast
import io
import sys
from pathlib import Path

import FreeSimpleGUI as Sg  # type: ignore

import settings
from get_data.get_team_league import MLB, NBA, NFL, NHL

file_path = Path("settings.py")

# List of setting keys to be updated
setting_keys_booleans = [
    "display_last_pitch", "display_play_description", "display_bases", "display_balls_strikes",
    "display_hits_errors", "display_pitcher_batter", "display_inning", "display_outs",

    "display_nba_timeouts", "display_nba_bonus", "display_nba_clock", "display_nba_shooting",
    "display_nba_play_by_play",

    "display_nhl_clock", "display_nhl_sog", "display_nhl_power_play", "display_nhl_play_by_play",

    "display_nfl_clock", "display_nfl_down", "display_nfl_possession",
    "display_nfl_timeouts", "display_nfl_redzone",

    "display_records", "display_venue", "display_network", "display_series", "display_odds",
    "display_date_ended", "prioritize_playing_team", "always_get_logos",
]

setting_keys_integers = ["LIVE_DATA_DELAY", "FETCH_DATA_NOT_PLAYING_TIMER", "DISPLAY_NOT_PLAYING_TIMER",
                            "DISPLAY_PLAYING_TIMER", "HOW_LONG_TO_DISPLAY_TEAM", "FETCH_DATA_PLAYING_TIMER"]


def read_teams_from_file() -> list:
    """Read settings.py and get what teams are in teams list.

    :return: list of team names
    """
    teams = []
    with file_path.open(encoding="utf-8") as file:
        lines = file.readlines()
        inside_teams = False
        for line in lines:
            if line.strip().startswith("teams = ["):
                inside_teams = True
                continue
            if inside_teams:
                if line.strip().startswith("]"):
                    break
                team_name = line.strip().strip("[],").strip('"').strip("'")
                if team_name:
                    teams.append(team_name)
    return teams


def read_settings_from_file() -> dict[str, int | bool | str]:
    """Read constants in settings.py to see what values are.

    :return: dictionary of values
    """
    settings: dict[str, int | bool | str] = {}
    keys_to_find = ["FONT", *setting_keys_booleans, *setting_keys_integers]
    with file_path.open(encoding="utf-8") as file:
        lines = file.readlines()

    for line in lines:
        for key in keys_to_find:
            if line.strip().startswith(f"{key} ="):
                value = line.strip().split("=")[-1].strip()
                if (key in setting_keys_integers):
                    try:
                        settings[key] = int(value)
                    except ValueError:
                        settings[key] = 0
                elif key == "FONT":
                    settings[key] = value.strip('"').strip("'")
                elif value.lower() == "true":
                    settings[key] = True
                else:
                    settings[key] = False
    return settings


def positive_num(input_str: str) -> bool:
    """Check if string is a positive integer.

    :param input: string value

    :return: True if parameter passed is positive integer, False otherwise
    """
    return input_str.isdigit() and int(input_str) >= 0


def load_teams_order() -> list[str]:
    """Read teams list in settings.py getting order of teams in list.

    :return: list of teams in order in settings.py list
    """
    with file_path.open(encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename="settings.py")
    for node in tree.body:
        if isinstance(node, ast.Assign):
            target = node.targets[0]
            if isinstance(target, ast.Name) and target.id == "teams":
                return ast.literal_eval(ast.unparse(node.value))
    return []


def update_teams(selected_teams: list, league: str) -> tuple[str, str]:
    """Update settings.py teams list to contain team names user wants to display.

    :param selected_teams: teams selected by user to display
    :param league: league that team selected is in

    :return: list of strings telling what team(s) was selected and what team(s) where unselected
    """
    available_checkbox_teams = {
        "MLB": MLB,
        "NHL": NHL,
        "NBA": NBA,
        "NFL": NFL,
    }.get(league, [])

    teams_added = ""
    teams_removed = ""
    existing_teams = read_teams_from_file()
    untouched_teams = [team for team in existing_teams if team not in available_checkbox_teams]
    new_teams = sorted(set(untouched_teams + selected_teams))

    teams_string = "teams = [\n"
    for team in new_teams:
        teams_string += f'    ["{team}"],\n'
    teams_string += "]\n"

    with file_path.open(encoding="utf-8") as file:
        contents = file.readlines()

    start_index, end_index = None, None
    bracket_balance = 0
    found_teams = False

    for i, line in enumerate(contents):
        if not found_teams:
            if line.strip().startswith("teams = ["):
                start_index = i
                bracket_balance += line.count("[") - line.count("]")
                found_teams = True
        else:
            bracket_balance += line.count("[") - line.count("]")
            if bracket_balance == 0:
                end_index = i
                break

    if start_index is not None and end_index is not None:
        contents = contents[:start_index] + [teams_string] + contents[end_index + 1:]

        with file_path.open("w", encoding="utf-8") as file:
            file.writelines(contents)

        added_teams = [team for team in selected_teams if team not in existing_teams]
        removed_teams = \
            [team for team in available_checkbox_teams if team in existing_teams and team not in selected_teams]

        if added_teams:
            teams_added = f"Teams Added: {', '.join(added_teams)}  "
        if removed_teams:
            teams_removed = f"Teams Removed: {', '.join(removed_teams)}"
        if not added_teams and not removed_teams:
            teams_added += "No changes made."

    return teams_added, teams_removed


def update_settings(live_data_delay: int, fetch_timer: int, display_timer: int, display_time: int,
                    display_timer_live: int, font_selected: str, selected_items: list) -> None:
    """Update settings.py with new values.

    :param live_data_delay: delay for live data in seconds
    :param fetch_timer: timer for fetching data in seconds
    :param display_timer: timer for displaying data in seconds
    :param display_time: time to display team in seconds
    :param display_timer_live: timer for displaying live data in seconds
    :param font_selected: font selected by user
    :param selected_items: list of selected items to update in settings

    :return: None
    """
    with file_path.open(encoding="utf-8") as file:
        contents = file.readlines()

    for i, line in enumerate(contents):
        if line.strip().startswith("LIVE_DATA_DELAY ="):
            contents[i] = f"LIVE_DATA_DELAY = {live_data_delay}\n"
        if line.strip().startswith("FONT ="):
            contents[i] = f'FONT = "{font_selected}"\n'
        if line.strip().startswith("FETCH_DATA_NOT_PLAYING_TIMER ="):
            contents[i] = f"FETCH_DATA_NOT_PLAYING_TIMER = {fetch_timer}\n"
        if line.strip().startswith("FETCH_DATA_PLAYING_TIMER ="):
            contents[i] = f"FETCH_DATA_PLAYING_TIMER = {fetch_timer}\n"
        if line.strip().startswith("DISPLAY_NOT_PLAYING_TIMER ="):
            contents[i] = f"DISPLAY_NOT_PLAYING_TIMER = {display_timer}\n"
        if line.strip().startswith("DISPLAY_PLAYING_TIMER ="):
            contents[i] = f"DISPLAY_PLAYING_TIMER = {display_timer_live}\n"
        if line.strip().startswith("HOW_LONG_TO_DISPLAY_TEAM ="):
            contents[i] = f"HOW_LONG_TO_DISPLAY_TEAM = {display_time}\n"

    for key, selected in zip(setting_keys_booleans, selected_items, strict=False):
        for i, line in enumerate(contents):
            if line.strip().startswith(f"{key} ="):
                contents[i] = f"{key} = {selected!s}\n"

    # Must do this to change settings as module won't get reloaded until scoreboard screen starts
    if key == "always_get_logos" and selected is True:
        settings.always_get_logos = True
    else:
        settings.always_get_logos = False

    with file_path.open("w", encoding="utf-8") as file:
        file.writelines(contents)


def save_teams_order(new_ordered_teams: list) -> None:
    """Replace the existing teams array with a newly ordered array.

    :param new_ordered_teams: teams in settings array to reorder

    :return: None
    """
    # Flatten the list of teams in case it's a list of lists
    flattened_teams = [team[0] for team in new_ordered_teams] \
        if isinstance(new_ordered_teams[0], list) else new_ordered_teams

    # Create the string representation of the teams array to insert into the file
    teams_string = "teams = [\n"
    for team in flattened_teams:
        teams_string += f"    ['{team}'],\n"
    teams_string += "]\n"

    # Read the file and find the teams section to update
    with file_path.open(encoding="utf-8") as file:
        contents = file.readlines()

    start_index, end_index = None, None
    bracket_balance = 0
    found_teams = False

    for i, line in enumerate(contents):
        if not found_teams:
            if line.strip().startswith("teams = ["):
                start_index = i
                bracket_balance += line.count("[") - line.count("]")
                found_teams = True
        else:
            bracket_balance += line.count("[") - line.count("]")
            if bracket_balance == 0:
                end_index = i
                break

    # If teams block is found, replace it with the new reordered list
    if start_index is not None and end_index is not None:
        contents = contents[:start_index] + [teams_string] + contents[end_index + 1:]

        # Write the updated contents back to the file
        with file_path.open("w", encoding="utf-8") as file:
            file.writelines(contents)

        print(f"Teams Reordered: {', '.join(flattened_teams)}")


class RedirectText(io.StringIO):
    """Redirect print statements to window element."""

    def __init__(self, window: Sg.Window) -> None:
        """Initialize the RedirectText class.

        :param window: PySimpleGUI window to redirect output to
        """
        self.window = window
        self.original_stdout = sys.stdout  # Save the original stdout

    def write(self, string: str) -> int:
        """Override the write method to redirect output to the window.

        :param string: string to write to the window
        """
        try:
            if self.window is not None and not self.window.was_closed():
                current_value = self.window["terminal_output"].get()
                current_value += string + "\n"  # Append the new string
                self.window["terminal_output"].update(current_value)
                self.window["terminal_output"].set_vscroll_position(1)
        except (KeyError, AttributeError, RuntimeError) as e:
            print(e)

    def restore_stdout(self) -> None:
        """Restore the original stdout."""
        sys.stdout = self.original_stdout
