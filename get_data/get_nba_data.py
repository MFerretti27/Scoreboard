"""Get NBA from NBA specific API."""
import os

from nba_api.live.nba.endpoints import scoreboard  # type: ignore

import settings

home_team_bonus = False
away_team_bonus = False
home_timeouts_saved = 0
away_timeouts_saved = 0


def get_all_nba_data(team_name: str) -> tuple[dict[str, str], bool, bool]:
    """Get all information for NBA team.

    Call this if ESPN fails to get MLB data as backup.

    :param team_name: The team name to get information for

    :return team_info: dictionary containing team information to display
    """
    currently_playing = False
    has_data = False
    team_info = {}

    # Today's Score Board
    games = scoreboard.ScoreBoard()
    live = games.get_dict()

    # Find team
    for game in live["scoreboard"]["games"]:
        if game["homeTeam"]["teamName"] in team_name or game["awayTeam"]["teamName"] in team_name:
            has_data = True

            # Can't get network image so display nothing
            team_info["under_score_image"] = ""

            # Get Bottom Info
            team_info["bottom_info"] = game["gameStatusText"]

            # Get above score text
            home_team = game["homeTeam"]["teamName"]
            away_team = game["awayTeam"]["teamName"]
            team_info["above_score_txt"] = f"{away_team} @ {home_team}"

            # Get team logos
            folder_path = os.getcwd() + '/images/sport_logos/NBA/'
            file_names = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
            for file in file_names:
                if home_team.upper() in file:
                    home_team = file
                if away_team.upper() in file:
                    away_team = file

            team_info["away_logo"] = (f"{os.getcwd()}/images/sport_logos/NBA/{away_team}")
            team_info["home_logo"] = (f"{os.getcwd()}/images/sport_logos/NBA/{home_team}")

            team_info["home_score"] = "0"
            team_info["away_score"] = "0"

    return team_info, has_data, currently_playing


def append_nba_data(team_info: dict, team_name: str) -> dict:
    """Get information for NBA team if playing.

    :param team_info: Dictionary where data is stored to display
    :param team_name: The team name to get information for

    :return team_info: dictionary containing team information to display
    """
    global home_team_bonus, away_team_bonus, home_timeouts_saved, away_timeouts_saved

    def handle_bonus(team: dict, backup: bool) -> bool:
        if team["inBonus"] == "1":
            return True
        if team["inBonus"] == "0":
            return False
        if team["inBonus"] is None:
            return backup
        return False

    def format_timeouts(timeout_count: int) -> str:
        dots = "\u25CF  "
        return dots * timeout_count if 0 <= timeout_count <= 7 else ""

    games = scoreboard.ScoreBoard().get_dict()["scoreboard"]["games"]
    for game in games:
        home = game["homeTeam"]
        away = game["awayTeam"]
        if team_name.upper() in (home["teamName"].upper(), away["teamName"].upper()):
            if settings.display_nba_bonus:
                home_bonus = handle_bonus(home, home_team_bonus)
                away_bonus = handle_bonus(away, away_team_bonus)

                team_info["home_bonus"] = home_bonus
                team_info["away_bonus"] = away_bonus

                home_team_bonus = home_bonus
                away_team_bonus = away_bonus

            if settings.display_nba_timeouts:
                home_timeouts = home["timeoutsRemaining"]
                away_timeouts = away["timeoutsRemaining"]

                if home["inBonus"] is None and away["inBonus"] is None:
                    home_timeouts = home_timeouts_saved
                    away_timeouts = away_timeouts_saved
                else:
                    home_timeouts_saved = home_timeouts
                    away_timeouts_saved = away_timeouts

                team_info["home_timeouts"] = format_timeouts(home_timeouts)
                team_info["away_timeouts"] = format_timeouts(away_timeouts)

            break  # Found matching game, exit loop

    return team_info
