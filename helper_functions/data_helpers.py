"""Functions for helping grab data from api's."""

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
