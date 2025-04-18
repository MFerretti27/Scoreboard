'''Get NBA from NBA specific API'''
from nba_api.live.nba.endpoints import scoreboard


def append_nba_data(team_info: dict, team_name: str) -> dict:
    """Get information for NBA team if playing.

    Call this if ESPN fails to get MLB data as backup.
    
    :param team_info: Dictionary where data is stored to display
    :param team_name: The team name to get information for

    :return team_info: Dictionary where data is stored to display
    """
    # Get timeouts and if team is in bonus from nba_api.live.nba.endpoints
    games = scoreboard.ScoreBoard()
    data = games.get_dict()
    for game in data["scoreboard"]["games"]:
        if game["homeTeam"]["teamName"].upper() in team_name.upper() or \
            game["awayTeam"]["teamName"].upper() in team_name.upper():

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

            home_timeouts = game["homeTeam"]["timeoutsRemaining"]
            away_timeouts = game["awayTeam"]["timeoutsRemaining"]

            if game["homeTeam"]["inBonus"] is None and game["awayTeam"]["inBonus"] is None:
                home_timeouts = home_timeouts + 1
                away_timeouts = away_timeouts + 1

            timeout_map = {7: "\u25CF  \u25CF  \u25CF  \u25CF  \u25CF  \u25CF  \u25CF",
                            6: "\u25CF  \u25CF  \u25CF  \u25CF  \u25CF  \u25CF",
                            5: "\u25CF  \u25CF  \u25CF  \u25CF  \u25CF",
                            4: "\u25CF  \u25CF  \u25CF  \u25CF",
                            3: "\u25CF  \u25CF  \u25CF",
                            2: "\u25CF  \u25CF",
                            1: "\u25CF",
                            0: ""}
            team_info['away_timeouts'] = timeout_map.get(away_timeouts, "")
            team_info['home_timeouts'] = timeout_map.get(home_timeouts, "")

            break  # Found team and got data needed

    return team_info