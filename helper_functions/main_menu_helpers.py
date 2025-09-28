"""Helper functions used in main menu."""
import ast
import difflib
import io
import re
import sys
from pathlib import Path
from typing import Any

import FreeSimpleGUI as Sg  # type: ignore[import]
import statsapi  # type: ignore[import]
from nba_api.stats.endpoints import leaguestandings  # type: ignore[import]
from nba_api.stats.static import teams as nba_teams  # type: ignore[import]
from nhlpy.nhl_client import NHLClient  # type: ignore[import]

import get_data.get_team_league
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
    "display_date_ended", "prioritize_playing_team", "always_get_logos", "prioritize_playoff_championship_image",
    "display_playoff_championship_image",
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

        added_teams = [team for team in selected_teams if team not in existing_teams]
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
    settings.always_get_logos = False
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

def normalize(name: str) -> str:
    """Lowercase, remove punctuation (keep spaces), collapse spaces."""
    name = name.lower()
    name = re.sub(r"[^\w\s]", "", name)        # remove punctuation
    return re.sub(r"\s+", " ", name).strip()   # collapse spaces

def split_city_nickname(name: str) -> tuple[str, str]:
    """Do a Heuristic split.

    Everything except the last token is 'city',
    last token is 'nickname'. If only one token, city="" and nickname=token.
    """
    tokens = name.split()
    if len(tokens) == 0:
        return "", ""
    if len(tokens) == 1:
        return "", tokens[0]
    return " ".join(tokens[:-1]), tokens[-1]

def similarity(a: str, b: str) -> float:
    """Construct a SequenceMatcher."""
    return difflib.SequenceMatcher(None, a, b).ratio()

def get_new_team_names(league: str) -> tuple:
    """Grab new team names from API's.

    :param league: league of which to grab names for

    :return renamed: list of tuple's showing what team names changed
    :return new_list: list of all new team names found
    :return str: message if getting new teams was successful
    """
    team_names_before = {
        "MLB": MLB,
        "NHL": NHL,
        "NBA": NBA,
        "NFL": NFL,
    }.get(league, [])

    new_list = []
    old_list = team_names_before.copy()
    renamed: list = []
    try:
        if league == "MLB":
            teams = statsapi.get("teams", {"sportIds": 1})["teams"]
            new_list.extend([team["name"] for team in teams])

        elif league == "NHL":
            client = NHLClient()
            new_list.extend([team["name"] for team in client.teams.teams()])

        elif league == "NBA":
            new_list.extend([team["full_name"] for team in nba_teams.get_teams()])
    except Exception:
        logger.exception("Getting new team names failed")
        return [], [], "Failed to Get New Team Names"

    # normalize inputs but keep original labels for results
    old_norm = [(o, normalize(o)) for o in old_list]
    new_norm = [(n, normalize(n)) for n in new_list]

    # quick lookups
    city_count_new: dict[str, Any] = {}
    city_count_old: dict[str, Any] = {}
    old_meta: dict[str, Any] = {}
    new_meta: dict[str, Any] = {}

    for orig, norm in old_norm:
        city, nick = split_city_nickname(norm)
        old_meta[orig] = {"norm": norm, "city": city, "nick": nick}
        city_count_old[city] = city_count_old.get(city, 0) + 1

    for orig, norm in new_norm:
        city, nick = split_city_nickname(norm)
        new_meta[orig] = {"norm": norm, "city": city, "nick": nick}
        city_count_new[city] = city_count_new.get(city, 0) + 1

    # Build candidate scores for every old x new
    candidates = []
    for old_orig, old_data in old_meta.items():
        for new_orig, new_data in new_meta.items():
            full_sim = similarity(old_data["norm"], new_data["norm"])
            nick_sim = similarity(old_data["nick"], new_data["nick"])
            # Score is a weighted mix but the decision uses thresholds/extra rules
            score = 0.65 * full_sim + 0.35 * nick_sim
            candidates.append({
                "old": old_orig,
                "new": new_orig,
                "full_sim": full_sim,
                "nick_sim": nick_sim,
                "city_same": (old_data["city"] != "" and old_data["city"] == new_data["city"]),
                "score": score,
            })

    # Sort candidates high->low so greedy matching picks best pairs first
    candidates.sort(key=lambda c: c["score"], reverse=True)

    matched_old = set()
    matched_new = set()
    renamed = []

    for c in candidates:
        o = c["old"]
        n = c["new"]
        if o in matched_old or n in matched_new:
            continue

        # RULES to accept this pair as a rename:
        # 1) If nickname similarity is high enough -> accept
        if c["nick_sim"] >= 0.60 and c["full_sim"] >= 0.70:
            matched_old.add(o)
            matched_new.add(n)
            renamed.append((o, n))
            continue

        # 2) If full similarity is very high and nickname at least somewhat similar
        if c["full_sim"] >= 0.90 and c["nick_sim"] >= 0.35:
            matched_old.add(o)
            matched_new.add(n)
            renamed.append((o, n))
            continue

        # 3) City rule: same city and that city appears exactly once in new and once in old
        #    This allows "Washington Redskins" -> "Washington Commanders" detection,
        #    but prevents mapping in cities with multiple teams (LA).
        if c["city_same"]:
            old_city = split_city_nickname(normalize(o))[0]
            if city_count_new.get(old_city, 0) == 1 and city_count_old.get(old_city, 0) == 1:
                # treat as rename (even if nicknames very different), because unique city match
                matched_old.add(o)
                matched_new.add(n)
                renamed.append((o, n))
                continue

        # otherwise not confident enough -> skip

    # After greedy matching, anything in new not matched is 'added', anything in old not matched is 'removed'
    added = [n for n in new_list if n not in matched_new]
    removed = [o for o in old_list if o not in matched_old]
    logger.info(f"\nNew and not matched: {added}\n")
    logger.info(f"\nOld and not matched: {removed}\n")

    renamed = []
    for new_team, old_team in zip(added, removed, strict=False):
        renamed.append((old_team, new_team))

    return renamed, new_list, "Getting New Team Name's Successful!"

def update_new_division(league: str) -> str:
    """Find the division a team is in to change their name there.

    :param league: league of which to find divisions and teams in division

    :return: Message if updating was successful
    """
    new_team_divisions: dict[str, list] = {}

    try:
        if league == "MLB":
            teams = statsapi.get("teams", {"sportIds": 1})["teams"]
            for team in teams:
                # Ensure key in dictionary matches list name in get_team_league
                division = "MLB_" + team["division"]["name"]
                division = division.replace("American League", "AL").replace("National League", "NL").replace(" ", "_")
                division = division.upper()
                if division in new_team_divisions:
                    new_team_divisions[division].append(team["name"])
                else:
                    new_team_divisions[division] = []

        elif league == "NHL":
            client = NHLClient()
            for team in client.teams.teams():
                # Ensure key in dictionary matches list name in get_team_league
                division = "NHL_" + team["division"]["name"].replace(" ", "_").upper() + "_DIVISION"
                if division in new_team_divisions:
                    new_team_divisions[division].append(team["name"])
                else:
                    new_team_divisions[division] = []

        elif league == "NBA":
            nba_stats = leaguestandings.LeagueStandings().get_dict()
            for team in nba_stats["resultSets"][0]["rowSet"]:
                # Ensure key in dictionary matches list name in get_team_league
                division = "NBA_" + team[9].replace(" ", "_").upper() + "_DIVISION"
                if division in new_team_divisions:
                    new_team_divisions[division].append(team[3] + " " + team[4])
                else:
                    new_team_divisions[division] = []

        logger.info("New Divisions:\n %s\n", new_team_divisions)

        # Using key (list name) and value (teams in list) update division lists in get_team_league.py
        for key, value in new_team_divisions.items():
            update_new_names(key, value)

    except Exception:
        logger.exception("Failed Getting writing divisions")
        return "Updating Teams Failed"

    return "Updating Team's Successful!"


def update_new_names(list_to_update: str, new_teams: list, renamed: list | None=None) -> None:
    """Update specified list in a Python file.

    :param list_to_update: List of which to change the team names
    :param renamed: List teams and what they were renamed to
    :param new_teams: New teams that are being added to list
    """
    team_file_path = Path("get_data/get_team_league.py")
    content = team_file_path.read_text(encoding="utf-8")

    pattern = re.compile(
        rf"(^\s*{re.escape(list_to_update)}\s*=\s*\[)([\s\S]*?)(\]\s*,?)",
        re.MULTILINE,
    )

    match: re.Match[str]| None = pattern.search(content)

    if not match:
        return
    _, list_block, _ = match.group(1), match.group(2), match.group(3)

    # Sort the new team list alphabetically
    sorted_names = sorted(new_teams)

    # Build the block preserving indentation from the original
    indent_match = re.match(r"(\s*)", list_block.split("\n")[0])
    indent = indent_match.group(1) if indent_match else "    "

    # Join into wrapped lines of max ~100 chars
    formatted_lines = []
    line = indent
    for name in sorted_names:
        item = f'"{name}", '
        if len(line) + len(item) > 120:  # wrap line if too long
            formatted_lines.append(line.rstrip())
            line = indent + item
        else:
            line += item
    if line.strip():
        formatted_lines.append(line.rstrip())

    new_block = "\n".join(formatted_lines)

    new_content = content[: match.start(2)] + "\n" + new_block + "\n" + content[match.end(2):]

    team_file_path.write_text(new_content, encoding="utf-8")

    # Update current in-memory instance so changes take effect immediately
    current_list = getattr(get_data.get_team_league, list_to_update)
    current_list.clear()
    current_list.extend(sorted_names)

    # update settings.py file team name if it needs to change
    if list_to_update in ["MLB", "NFL", "NBA", "NHL"] and renamed:
        remove_specifically = []
        settings_dict = read_teams_from_file()
        for renamed_team in renamed:
            if renamed_team[0] in settings_dict:
                settings_dict[settings_dict.index(renamed_team[0])] = renamed_team[1]
                remove_specifically.append(renamed_team[0])
        update_teams(settings_dict, list_to_update, specific_remove=remove_specifically)

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
        except (KeyError, AttributeError, RuntimeError):
            logger.exception("Failed to write output to window")

        return len(string)

    def restore_stdout(self) -> None:
        """Restore the original stdout."""
        sys.stdout = self.original_stdout
