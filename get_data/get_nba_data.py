"""Get NBA from NBA specific API."""
from nba_api.live.nba.endpoints import scoreboard  # type: ignore import warning
import os
import settings

home_team_bonus = False
away_team_bonus = False
home_timeouts_saved = 0
away_timeouts_saved = 0


def get_all_nba_data(team_name: str) -> dict:
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

            # Cant get network image so display nothing
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
    # Get timeouts and if team is in bonus from nba_api.live.nba.endpoints
    games = scoreboard.ScoreBoard()
    data = games.get_dict()
    for game in data["scoreboard"]["games"]:
        if game["homeTeam"]["teamName"].upper() in team_name.upper() or \
                game["awayTeam"]["teamName"].upper() in team_name.upper():

            # Many times bonus is None, store it so when it is None then display last known value
            if settings.display_nba_bonus:
                if game["homeTeam"]["inBonus"] == "1":
                    team_info['home_bonus'] = True
                    home_team_bonus = True
                elif game["homeTeam"]["inBonus"] == "0":
                    team_info['home_bonus'] = False
                    home_team_bonus = False
                elif game["homeTeam"]["inBonus"] is None:
                    team_info['home_bonus'] = home_team_bonus
                else:
                    team_info['home_bonus'] = False

                if game["awayTeam"]["inBonus"] == "1":
                    team_info['away_bonus'] = True
                    away_team_bonus = True
                elif game["awayTeam"]["inBonus"] == "0":
                    team_info['away_bonus'] = False
                    away_team_bonus = False
                elif game["awayTeam"]["inBonus"] is None:
                    team_info['away_bonus'] = away_team_bonus
                else:
                    team_info['away_bonus'] = False

            if settings.display_nba_timeouts:
                home_timeouts = game["homeTeam"]["timeoutsRemaining"]
                away_timeouts = game["awayTeam"]["timeoutsRemaining"]

                # When "inBonus" is None timeouts have wrong data store them to display last known good value
                if game["homeTeam"]["inBonus"] is None and game["awayTeam"]["inBonus"] is None:
                    home_timeouts = home_timeouts_saved
                    away_timeouts = away_timeouts_saved
                else:
                    home_timeouts_saved = home_timeouts
                    away_timeouts_saved = away_timeouts

                timeout_map = {
                    7: "\u25CF  \u25CF  \u25CF  \u25CF  \u25CF  \u25CF  \u25CF",
                    6: "\u25CF  \u25CF  \u25CF  \u25CF  \u25CF  \u25CF",
                    5: "\u25CF  \u25CF  \u25CF  \u25CF  \u25CF",
                    4: "\u25CF  \u25CF  \u25CF  \u25CF",
                    3: "\u25CF  \u25CF  \u25CF",
                    2: "\u25CF  \u25CF",
                    1: "\u25CF",
                    0: ""
                }
                team_info['away_timeouts'] = timeout_map.get(away_timeouts, "")
                team_info['home_timeouts'] = timeout_map.get(home_timeouts, "")

            break  # Found team and got data needed, dont continue loop

    return team_info
