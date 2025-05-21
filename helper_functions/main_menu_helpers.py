"""Helper functions used in main menu."""
import ast
from get_data.get_team_league import MLB, NHL, NBA, NFL
import settings
import sys
import io

filename = "settings.py"

# List of setting keys to be updated
setting_keys = [
    "display_last_pitch", "display_play_description", "display_bases", "display_balls_strikes",
    "display_hits_errors", "display_pitcher_batter", "display_inning", "display_outs",

    "display_nba_timeouts", "display_nba_bonus", "display_nba_clock", "display_nba_shooting",

    "display_nhl_clock", "display_nhl_sog", "display_nhl_power_play",

    "display_nfl_clock", "display_nfl_down", "display_nfl_possession",
    "display_nfl_timeouts", "display_nfl_redzone",

    "display_records", "display_venue", "display_network", "display_series", "display_odds",
    "display_date_ended", "prioritize_playing_team", "always_get_logos"
]


def read_teams_from_file() -> list:
    """Read settings.py and get what teams are in teams list.

    :return: list of team names
    """
    teams = []
    with open(filename, "r") as file:
        lines = file.readlines()
        inside_teams = False
        for line in lines:
            if line.strip().startswith("teams = ["):
                inside_teams = True
                continue
            if inside_teams:
                if line.strip().startswith("]"):
                    break
                team_name = line.strip().strip('[],').strip('"').strip("'")
                if team_name:
                    teams.append(team_name)
    return teams


def read_settings_from_file() -> dict:
    """Read constants in settings.py to see what values are.

    :return: dictionary of values
    """
    settings = {}
    keys_to_find = [
        "FONT", "LIVE_DATA_DELAY", "FETCH_DATA_NOT_PLAYING_TIMER", "FETCH_DATA_PLAYING_TIMER",
        "DISPLAY_NOT_PLAYING_TIMER", "DISPLAY_PLAYING_TIMER", "HOW_LONG_TO_DISPLAY_TEAM",

        "display_last_pitch", "display_play_description", "display_bases", "display_balls_strikes",
        "display_hits_errors", "display_pitcher_batter", "display_inning", "display_outs",

        "display_nba_timeouts", "display_nba_bonus", "display_nba_clock", "display_nba_shooting",

        "display_nhl_clock", "display_nhl_sog", "display_nhl_power_play",

        "display_nfl_clock", "display_nfl_down", "display_nfl_possession",
        "display_nfl_timeouts", "display_nfl_redzone",

        "display_records", "display_venue", "display_network", "display_series", "display_odds",
        "display_date_ended", "prioritize_playing_team", "always_get_logos"
    ]

    with open(filename, "r") as file:
        lines = file.readlines()

    for line in lines:
        for key in keys_to_find:
            if line.strip().startswith(f"{key} ="):
                value = line.strip().split("=")[-1].strip()
                if key == "LIVE_DATA_DELAY":
                    try:
                        settings[key] = int(value)
                    except ValueError:
                        settings[key] = 0
                elif key == "FETCH_DATA_NOT_PLAYING_TIMER":
                    try:
                        settings[key] = int(value)
                    except ValueError:
                        settings[key] = 0
                elif key == "DISPLAY_NOT_PLAYING_TIMER":
                    try:
                        settings[key] = int(value)
                    except ValueError:
                        settings[key] = 0
                elif key == "DISPLAY_PLAYING_TIMER":
                    try:
                        settings[key] = int(value)
                    except ValueError:
                        settings[key] = 0
                elif key == "HOW_LONG_TO_DISPLAY_TEAM":
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


def positive_num(input: str) -> bool:
    """Check if string is a positive integer.

    :param input: string value

    :return: True if parameter passed is positive integer, False otherwise
    """
    return input.isdigit() and int(input) >= 0


def load_teams_order() -> list:
    """Read teams list in settings.py getting order of teams in list.

    :return: list of teams in order in settings.py list
    """
    with open(filename, 'r') as f:
        tree = ast.parse(f.read(), filename=filename)
    for node in tree.body:
        if isinstance(node, ast.Assign):
            if node.targets[0].id == 'teams':
                return ast.literal_eval(ast.unparse(node.value))
    return []


def update_teams(selected_teams: list, league: str) -> tuple[str, str]:
    """update settings.py teams list to contain team names user wants to display.

    :param selected_teams: teams selected by user to display
    :param league: league that team selected is in

    :return: list of strings telling what team(s) was selected and what team(s) where unselected
    """
    available_checkbox_teams = {
        "MLB": MLB,
        "NHL": NHL,
        "NBA": NBA,
        "NFL": NFL
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

    with open(filename, "r") as file:
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

        with open(filename, "w") as file:
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
    with open(filename, "r") as file:
        contents = file.readlines()

    for i, line in enumerate(contents):
        if line.strip().startswith("LIVE_DATA_DELAY ="):
            contents[i] = f"LIVE_DATA_DELAY = {live_data_delay}\n"
        if line.strip().startswith("FONT ="):
            contents[i] = f'FONT = "{font_selected}"\n'
        if line.strip().startswith("FETCH_DATA_NOT_PLAYING_TIMER ="):
            contents[i] = f'FETCH_DATA_NOT_PLAYING_TIMER = {fetch_timer}\n'
        if line.strip().startswith("FETCH_DATA_NOT_PLAYING_TIMER ="):
            contents[i] = f'FETCH_DATA_NOT_PLAYING_TIMER = {fetch_timer}\n'
        if line.strip().startswith("DISPLAY_NOT_PLAYING_TIMER ="):
            contents[i] = f'DISPLAY_NOT_PLAYING_TIMER = {display_timer}\n'
        if line.strip().startswith("DISPLAY_PLAYING_TIMER ="):
            contents[i] = f'DISPLAY_PLAYING_TIMER = {display_timer_live}\n'
        if line.strip().startswith("HOW_LONG_TO_DISPLAY_TEAM ="):
            contents[i] = f'HOW_LONG_TO_DISPLAY_TEAM = {display_time}\n'

    for key, selected in zip(setting_keys, selected_items):
        for i, line in enumerate(contents):
            if line.strip().startswith(f"{key} ="):
                contents[i] = f"{key} = {str(selected)}\n"

    # Must do this to change settings as module won't get reloaded until scoreboard screen starts
    if key == "always_get_logos" and selected is True:
        settings.always_get_logos = True
    else:
        settings.always_get_logos = False

    with open(filename, "w") as file:
        file.writelines(contents)


def save_teams_order(new_ordered_teams: list) -> str:
    """Replaces the existing teams array with a newly ordered array.

    :param new_ordered_teams: teams in settings array to reorder

    :return: str showing new order of teams
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
    with open(filename, "r") as file:
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
        with open(filename, "w") as file:
            file.writelines(contents)

        teams_reordered = f"Teams Reordered: {', '.join(flattened_teams)}"
        return teams_reordered
    else:
        return "Teams block not found in the file."


class RedirectText(io.StringIO):
    """Redirect print statements to window element."""
    def __init__(self, window):
        self.window = window
        self.original_stdout = sys.stdout  # Save the original stdout

    def write(self, string: str):
        """Override the write method to redirect output to the window."""
        try:
            if self.window is not None and not self.window.was_closed():
                current_value = self.window["terminal_output"].get()
                current_value += string + "\n"  # Append the new string
                self.window["terminal_output"].update(current_value)
                self.window["terminal_output"].set_vscroll_position(1)
        except Exception as e:
            print(e)

    def restore_stdout(self) -> None:
        """Restore the original stdout."""
        sys.stdout = self.original_stdout
