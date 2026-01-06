"""Helper functions used in main menu."""
import ast
import re
import unicodedata
from pathlib import Path
from typing import Any

import settings
from get_data.get_team_league import ALL_DIVISIONS, DIVISION_TEAMS, MLB, NBA, NFL, NHL
from helper_functions.logger_config import logger

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
    "display_date_ended", "prioritize_playing_team", "always_get_logos", "auto_update",
    "display_playoff_championship_image", "display_player_stats",
]

setting_keys_integers = ["LIVE_DATA_DELAY", "DISPLAY_NOT_PLAYING_TIMER",
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


def update_teams(selected_teams: list, league: str, specific_remove: list | None=None) -> tuple[str, str]:
    """Update settings.py teams list to contain team names user wants to display.

    :param selected_teams: teams selected by user to display
    :param league: league that team selected is in
    :param specific_remove: remove specific list of teams teams if passed in

    :return: list of strings telling what team(s) was selected and what team(s) where unselected
    """
    existing_teams = read_teams_from_file()
    teams_added: str = ""
    teams_removed: str = ""
    removed_teams: list = []

    available_checkbox_teams = {
        "MLB": MLB,
        "NHL": NHL,
        "NBA": NBA,
        "NFL": NFL,
    }.get(league, [])

    # Check to ensure selected item is valid
    for items in selected_teams:
        if items not in available_checkbox_teams and items not in ALL_DIVISIONS[league]:
            selected_teams.remove(items)

    selected_teams, existing_teams, removed_teams, = \
        update_division(league, selected_teams, existing_teams, removed_teams, available_checkbox_teams)

    untouched_teams = [team for team in existing_teams if team not in available_checkbox_teams]
    new_teams = list(dict.fromkeys(untouched_teams + selected_teams))  # Remove duplicates

    new_teams = double_check_teams(new_teams)  # Ensure all teams are valid

    # If need to remove specific team passed in such as team name no longer exists
    if specific_remove:
        for remove_team in specific_remove:
            new_teams.remove(remove_team)

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
        contents = [*contents[:start_index], teams_string, *contents[end_index + 1:]]

        with file_path.open("w", encoding="utf-8") as file:
            file.writelines(contents)

        added_teams = [team for team in new_teams if team not in existing_teams]
        removed_teams += \
            [team for team in available_checkbox_teams if team in existing_teams and team not in selected_teams]

        # Update the settings.teams list in-memory for when downloading logos later
        settings.teams.extend([[team] for team in added_teams])

        if added_teams:
            teams_added = f"Teams Added: {', '.join(added_teams)}  "
        if removed_teams:
            teams_removed = f"Teams Removed: {', '.join(removed_teams)}"
        if not added_teams and not removed_teams:
            teams_added += "No changes made."

    return teams_added, teams_removed


def update_settings(selected_items_integers: dict, selected_items_boolean: list) -> None:
    """Update settings.py with new values.

    :param live_data_delay: delay for live data in seconds
    :param fetch_timer: timer for fetching data in seconds
    :param display_timer: timer for displaying data in seconds
    :param display_time: time to display team in seconds
    :param display_timer_live: timer for displaying live data in seconds
    :param selected_items: list of selected items to update in settings

    :return: None
    """
    settings.always_get_logos = False
    with file_path.open(encoding="utf-8") as file:
        contents = file.readlines()

    for i, line in enumerate(contents):
        for key, value in selected_items_integers.items():
            if line.strip().startswith(f"{key} ="):
                contents[i] = f"{key} = {value}\n"

    for key, selected in zip(setting_keys_booleans, selected_items_boolean, strict=False):
        for i, line in enumerate(contents):
            if line.strip().startswith(f"{key} ="):
                contents[i] = f"{key} = {selected!s}\n"

        # Must do this to change settings as module won't get reloaded until scoreboard screen starts
        if key == "always_get_logos" and selected is True:
            settings.always_get_logos = True

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
        teams_string += f'    ["{team}"],\n'
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
        contents = [*contents[:start_index], teams_string, *contents[end_index + 1:]]

        # Write the updated contents back to the file
        with file_path.open("w", encoding="utf-8") as file:
            file.writelines(contents)

        logger.info("Teams Reordered: %s", ", ".join(flattened_teams))


def update_division(league: str, selected_teams: list, existing_teams: list, removed_teams: list,
                    available_checkbox_teams: list) -> tuple[list, list, list]:
    """If Division is selected or unselected remove or add teams.

    :param league: Current sports league
    :param selected_teams: Teams that should be added
    :param existing_teams: Teams where selected beforehand
    :param removed_teams: Teams that should be removed
    :param available_checkbox_teams: Possible teams that could be selected

    :return selected_teams: Teams that should be added
    :return existing_teams: Teams where selected beforehand
    :return removed_teams: Teams that should be removed
    """
    divisions = ALL_DIVISIONS.get(league, [])
    division_checked = settings.division_checked
    selected_divisions = [d for d in selected_teams if d in divisions]

    is_division_selected = bool(selected_divisions)
    should_remove_division = is_division_selected and division_checked
    should_add_division_teams = is_division_selected and not division_checked
    should_uncheck_division_teams = not is_division_selected and division_checked

    if should_remove_division:
        for team in existing_teams[:]:
            if team not in selected_teams and team in available_checkbox_teams:
                existing_teams.remove(team)
                removed_teams.append(team)
        selected_teams[:] = [t for t in selected_teams if t not in divisions]

    if should_add_division_teams:
        for division in selected_divisions:
            division_key = f"{league} {division}"
            teams = DIVISION_TEAMS.get(division_key, [])
            for team in teams:
                if team in available_checkbox_teams and team not in selected_teams:
                    selected_teams.append(team)
            selected_teams.remove(division)

    if should_uncheck_division_teams:
        for division in divisions:
            key = f"{league} {division}"
            teams = DIVISION_TEAMS.get(key, [])
            if all(t in selected_teams for t in teams):
                selected_teams[:] = [t for t in selected_teams if t not in teams]

    return selected_teams, existing_teams, removed_teams

def settings_to_json() -> dict[str, Any]:
    """Load a Python settings file and convert all its top-level variables to a dict.

    :param file_path: Path to the settings .py file
    :return: dictionary with all variables defined in the settings file
    """
    namespace: dict = {}
    with file_path.open(encoding="utf-8") as f:
        code = f.read()

    # Execute the settings file code safely in a fresh namespace
    exec(code, {}, namespace)

    # Remove built-ins and imported modules, keep only variables
    return {key: value for key, value in namespace.items() if not key.startswith("__")}


def write_settings_to_py(settings_saved: dict[Any, Any]) -> None:
    """Replace only the 'teams' block and update other settings in-place."""
    assign_pattern = re.compile(r"^(\w+)\s*=\s*(.+)$")
    lines = file_path.read_text().splitlines() if file_path.exists() else []
    updated_lines = []

    in_teams_block = False
    bracket_balance = 0
    teams_replaced = False

    for line in lines:
        if not in_teams_block and line.strip().startswith("teams") and "=" in line and "[" in line:
            in_teams_block = True
            bracket_balance = line.count("[") - line.count("]")
            # Replace this line with new teams assignment
            updated_lines.append(format_teams_block(settings_saved.get("teams", [])))
            teams_replaced = True
            continue

        if in_teams_block:
            bracket_balance += line.count("[") - line.count("]")
            if bracket_balance <= 0:
                in_teams_block = False
            continue  # Skip old lines in the block

        match = assign_pattern.match(line)
        if match:
            key, _ = match.groups()
            if key in settings_saved and key != "teams":
                value = settings_saved[key]
                formatted_value = (
                    f'"{value}"' if isinstance(value, str)
                    else repr(value)
                )
                updated_lines.append(f"{key} = {formatted_value}")
                continue

        updated_lines.append(line)

    # If teams block wasn't found, append it at the end
    if "teams" in settings_saved and not teams_replaced:
        updated_lines.append(format_teams_block(settings_saved["teams"]))

    file_path.write_text("\n".join(updated_lines) + "\n")

def format_teams_block(teams: list[list[str]]) -> str:
    """Format the 'teams' block using double quotes."""
    if isinstance(teams, list) and all(isinstance(item, list) and len(item) == 1 for item in teams):
        formatted = "teams = [\n"
        for item in teams:
            team_name = item[0].replace('"', '\\"')  # escape quotes
            formatted += f'    ["{team_name}"],\n'
        formatted += "]"
        return formatted
    return f"teams = {teams!s}"


def double_check_teams(new_teams: list[Any] | None = None) -> list[Any]:
    """Ensure all teams in settings.teams are valid teams."""
    if new_teams is not None:
        return [team for team in new_teams if team in (MLB + NBA + NFL + NHL)]
    for team in settings.teams[:]:
        if team[0] not in (MLB + NBA + NFL + NHL):
            settings.teams.remove(team)
            logger.info(f"Removed '{team}' from teams as its not a valid team.")
    return settings.teams


def remove_accents(team_names: str | list) -> str | list:
    """Normalize a string by removing accent marks (é → e, ñ → n, etc.).

    :param team_names: string or list of strings to remove accents from
    :return: string or list of strings with accents removed
    """
    if isinstance(team_names, str):
        normalized = unicodedata.normalize("NFD", team_names)
        return "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")

    cleaned_teams = []
    # Convert lists (or other iterables) to strings if needed
    for team in team_names:
        # Normalize and strip accents
        normalized = unicodedata.normalize("NFD", team)
        cleaned_teams.append("".join(ch for ch in normalized if unicodedata.category(ch) != "Mn"))
    return cleaned_teams
