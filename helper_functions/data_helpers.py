"""Functions for helping grab data from api's."""

from pathlib import Path

import settings

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
            print(f"{home_team} is playing {away_team}, skipping to not display twice")
            should_skip = False

            # Remove the skipped team data to prevent stale display
            settings.saved_data.pop(home_team, None)
            settings.saved_data.pop(away_team, None)

            return True

        should_skip = True
        return False

    return False


def get_network_logos(broadcast: str | list) -> str:
    """Get the network logo of the broadcast game is on.

    Only supports generic networks and not local networks. All networks supported
    can be found in images/network folder.

    :param broadcast: The broadcast game is on to look to display

    :return file_path: The string location of what logo to display, return black if cannot find
    """
    # Make broadcast upper (could be list or )
    if isinstance(broadcast, str):
        broadcast = broadcast.upper()
    elif isinstance(broadcast, list):
        broadcast = [b.upper() for b in broadcast]

    file_path = ""

    folder_path = Path.cwd() / "images" / "Networks"
    file_names = [f for f in Path(folder_path).iterdir() if Path.is_file(Path.cwd() / folder_path / f)]
    for file in file_names:
        file_no_png = file.name.upper().split("/")[-1].replace(".PNG", "")
        if file_no_png.upper() in broadcast.upper() and broadcast != "":
            file_path = Path.cwd() / "images" / "Networks" / file
            break

    return file_path
