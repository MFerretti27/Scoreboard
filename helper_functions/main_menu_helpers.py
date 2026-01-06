"""Helper functions used in main menu."""
import unicodedata
from typing import Any

import settings
from get_data.get_team_league import ALL_DIVISIONS, DIVISION_TEAMS, MLB, NBA, NFL, NHL
from helper_functions.logger_config import logger

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

setting_keys_integers = [
    "LIVE_DATA_DELAY",
    "DISPLAY_NOT_PLAYING_TIMER",
    "DISPLAY_PLAYING_TIMER",
    "HOW_LONG_TO_DISPLAY_TEAM",
    "FETCH_DATA_PLAYING_TIMER",
]


def positive_num(input_str: str) -> bool:
    """Check if string is a positive integer.

    :param input: string value

    :return: True if parameter passed is positive integer, False otherwise
    """
    return input_str.isdigit() and int(input_str) >= 0


def update_teams(selected_teams: list, league: str, specific_remove: list | None=None) -> tuple[str, str]:
    """Update settings.py teams list to contain team names user wants to display.

    :param selected_teams: teams selected by user to display
    :param league: league that team selected is in
    :param specific_remove: remove specific list of teams teams if passed in

    :return: list of strings telling what team(s) was selected and what team(s) where unselected
    """
    current_settings = settings.read_settings()
    existing_teams = [team[0] for team in current_settings.get("teams", [])]
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

    settings.write_settings({"teams": [[team] for team in new_teams]})

    added_teams = [team for team in new_teams if team not in existing_teams]
    removed_teams += [team for team in available_checkbox_teams if (team in existing_teams
                                                                    and team not in selected_teams)]

    if added_teams:
        teams_added = f"Teams Added: {', '.join(added_teams)}  "
    if removed_teams:
        teams_removed = f"Teams Removed: {', '.join(removed_teams)}"
    if not added_teams and not removed_teams:
        teams_added += "No changes made."

    return teams_added, teams_removed


def update_settings(selected_items_integers: dict, selected_items_boolean: list) -> None:
    """Update settings.py with new values.

    :param selected_items: list of selected items to update in settings
    :param selected_items_boolean: list of boolean selected items to update in settings

    :return: None
    """
    settings.always_get_logos = False

    updates = {key: int(value) for key, value in selected_items_integers.items()}
    for key, selected in zip(setting_keys_booleans, selected_items_boolean, strict=False):
        updates[key] = bool(selected)
        if key == "always_get_logos" and selected is True:
            settings.always_get_logos = True

    settings.write_settings(updates)


def save_teams_order(new_ordered_teams: list) -> None:
    """Replace the existing teams array with a newly ordered array.

    :param new_ordered_teams: teams in settings array to reorder

    :return: None
    """
    flattened_teams = ([team[0] for team in new_ordered_teams] if
                       isinstance(new_ordered_teams[0], list) else new_ordered_teams)
    settings.write_settings({"teams": [[team] for team in flattened_teams]})
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
