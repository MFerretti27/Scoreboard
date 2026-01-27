"""Functions for helping grab data from api's."""
from __future__ import annotations

from pathlib import Path

import settings
from constants.file_paths import NETWORKS_DIR, get_network_image_path
from get_data.get_team_league import get_team_league
from helper_functions.logging.logger_config import logger
from helper_functions.ui.main_menu_helpers import remove_accents
from screens import main_screen

should_skip = False

def check_playing_each_other(home_team: str, away_team: str) -> bool:
    """Check if the two teams are playing each other.

    :param home_team: Name of home team
    :param away_team: Name of away team
    :return: Boolean indicating whether to skip displaying the matchup (already shown once)
    """
    global should_skip

    # Create a set of uppercase team names for faster lookups
    team_names = {team[0].upper() for team in settings.teams}

    if home_team.upper() in team_names and away_team.upper() in team_names:
        if should_skip:
            logger.info("%s is playing %s, skipping to not display twice", home_team, away_team)
            should_skip = False

            # Remove the skipped team data to prevent stale display
            settings.saved_data.pop(home_team, None)
            settings.saved_data.pop(away_team, None)

            return True

        should_skip = True
        return False

    return False


def get_network_logos(broadcast: str | list, league: str) -> Path | str:
    """Get the network logo of the broadcast game is on.

    Only supports generic networks and not local networks. All networks supported
    can be found in images/network folder.

    :param broadcast: The broadcast game is on to look to display

    :return file_path: The string location of what logo to display, return black if cannot find
    """
    if settings.display_network:
        # Make broadcast upper (could be list or )
        if isinstance(broadcast, str):
            broadcast = broadcast.upper()
        elif isinstance(broadcast, list):
            broadcast = [b.upper() for b in broadcast]

        file_path: Path | str = ""

        folder_path = Path.cwd() / NETWORKS_DIR
        file_names = [f for f in Path(folder_path).iterdir() if Path.is_file(Path.cwd() / folder_path / f)]
        for file in file_names:
            file_no_png = file.name.upper().split("/")[-1].replace(".PNG", "")
            if file_no_png in broadcast and broadcast != "":
                file_path = Path.cwd() / NETWORKS_DIR / file
                break

        # Display Thursday Night Football logo for Prime games if football
        if "Prime" in str(file_path) and league.upper() == "NFL":
            file_path = get_network_image_path("Prime_TNF.png")

        return file_path
    return ""

def get_team_logo(home_team_name: str, away_team_name: str, league: str, team_info: dict) -> dict:
    """Get the team logo for the given team name.

    THIS FUNCTION CANNOT FAIL. MUST RETURN A VALID FILEPATH TO A PNG.

    :param home_team_name: Name of the home team
    :param away_team_name: Name of the away team
    :param league: League of the teams (e.g., MLB)
    :param team_info: Dictionary to store team logo paths

    :return team_info: Updated dictionary all data to display for the team
    """
    # Find closest matching team names in local files so logos can be found
    home_team_name, away_team_name = validate_team_names(home_team_name, away_team_name, league)

    folder_path = Path.cwd() / "images" / "sport_logos" / league
    file_names = [f for f in Path(folder_path).iterdir() if Path.is_file(Path.cwd() / folder_path / f)]

    # More Thorough check if team names exist in local files, this will error more gracefully than giving invalid path
    available_teams = {str(remove_accents(f.stem)).upper() for f in file_names}
    if away_team_name.upper() not in available_teams and not any(away_team_name.upper() in team
                                                                 for team in available_teams):
        logger.warning("Away team name %s not found in %s folder", away_team_name, league)
        msg = f"Could not find {away_team_name} logo, please re-download logos"
        raise RuntimeError(msg)
    if home_team_name.upper() not in available_teams and not any(home_team_name.upper() in team
                                                                 for team in available_teams):
        logger.warning("Home team name %s not found in %s folder", home_team_name, league)
        msg = f"Could not find {home_team_name} logo, please re-download logos"
        raise RuntimeError(msg)

    # File exists, get the logo path
    for file in file_names:
        filename = file.name.upper()
        filename = str(remove_accents(filename))
        if home_team_name.upper() in filename:
            home_team = filename
        if away_team_name.upper() in filename:
            away_team = filename

    team_info["away_logo"] = Path.cwd() / "images" / "sport_logos" / league / away_team.replace("PNG", "png")
    team_info["home_logo"] = Path.cwd() / "images" / "sport_logos" / league / home_team.replace("PNG", "png")

    return team_info


def check_for_doubleheader(response_as_json: dict, team_name: str) -> bool:
    """Check to see if MLB game is doubleheader."""
    count = 0

    # Get how many games is team in today
    for event in response_as_json["events"]:
            if team_name.upper() in event["name"].upper():
                count += 1

    return count == 2


def validate_team_names(away_team_name: str, home_team_name: str, league: str) -> tuple[str, str]:
    """Validate that the team name exists in the given league.

    :param away_team_name: Name of the away team
    :param home_team_name: Name of the home team
    :param league: League of the teams (e.g., MLB)

    :return: Tuple containing validated away and home team names
    """
    folder_path = Path.cwd() / "images" / "sport_logos" / league
    file_names = [f for f in Path(folder_path).iterdir() if Path.is_file(Path.cwd() / folder_path / f)]
    available_teams = {str(remove_accents(f.stem)).upper() for f in file_names}


    # Check if Team names from API exist in available teams
    home_valid = home_team_name.upper() in available_teams or any(home_team_name.upper() in team
                                                                  for team in available_teams)
    away_valid = away_team_name.upper() in available_teams or any(away_team_name.upper() in team
                                                                  for team in available_teams)

    # Teams are not valid but try to continue with closest match
    if not home_valid or not away_valid:
        # Get the closest matching team name in local files
        # This prevents crashes due to misnamed teams
        found_home_team = get_team_league(home_team_name)
        found_away_team = get_team_league(away_team_name)

        # Use name in local files
        home_team_name = found_home_team[0]
        away_team_name = found_away_team[0]

        if not home_valid:
            logger.exception("Local files have: %s but API gave: %s", found_home_team[0], home_team_name)
        if not away_valid:
            logger.exception("Local files have: %s but API gave: %s", found_away_team[0], away_team_name)

        main_screen.starting_message = f"Please Update {league} team names from their respective 'add screen'"

    return away_team_name, home_team_name
