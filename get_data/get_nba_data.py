"""Get NBA from NBA specific API."""
import re
from datetime import UTC, datetime
from typing import Any

from nba_api.live.nba.endpoints import boxscore, odds, playbyplay, scoreboard  # type: ignore[import]
from nba_api.stats.endpoints import teaminfocommon  # type: ignore[import]

import settings
from get_data.get_game_type import get_game_type
from get_data.get_player_stats import get_player_stats
from get_data.get_series_data import get_series
from get_data.get_team_id import get_nba_team_id
from helper_functions.data_helpers import check_playing_each_other, get_team_logo

home_team_bonus = False
away_team_bonus = False
home_timeouts_saved = 0
away_timeouts_saved = 0


def get_all_nba_data(team_name: str) -> tuple[dict[str, Any], bool, bool]:
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

            # Get game time
            utc_time = datetime.strptime(game["gameTimeUTC"], "%Y-%m-%dT%H:%M:%S%z")
            game_time = utc_time.replace(tzinfo=UTC).astimezone().strftime("%-m/%-d - %-I:%M %p")
            team_info["bottom_info"] = game_time

            # Get above score text
            home_team_name = game["homeTeam"]["teamName"]
            away_team_name = game["awayTeam"]["teamName"]
            team_info["above_score_txt"] = f"{away_team_name} @ {home_team_name}"

            # Check if two of your teams are playing each other to not display same data twice
            if check_playing_each_other(home_team_name, away_team_name):
                team_has_data = False
                return team_info, team_has_data, currently_playing

            # Get team records
            home_team_info = teaminfocommon.TeamInfoCommon(get_nba_team_id(home_team_name)).get_dict()
            away_team_info = teaminfocommon.TeamInfoCommon(get_nba_team_id(away_team_name)).get_dict()

            team_info["home_record"] = (str(home_team_info["resultSets"][0]["rowSet"][0][9]) +
                                        "-" + str(home_team_info["resultSets"][0]["rowSet"][0][10])
                                        )
            team_info["away_record"] = (str(away_team_info["resultSets"][0]["rowSet"][0][9]) +
                                        "-" + str(away_team_info["resultSets"][0]["rowSet"][0][10])
                                        )

            # Get team logos
            team_info = get_team_logo(home_team_name, away_team_name, "NBA", team_info)

            team_info["home_score"] = game["homeTeam"]["score"]
            team_info["away_score"] = game["awayTeam"]["score"]

            # Check if game is over
            if "Final" in game["gameStatusText"]:
                team_info["bottom_info"] = game["gameStatusText"].rstrip().upper()
                team_info["top_info"] = get_series("NBA", team_name)

                if settings.display_player_stats:
                    home_player_stats, away_player_stats = get_player_stats("NBA", team_name)
                    team_info["home_player_stats"] = home_player_stats
                    team_info["away_player_stats"] = away_player_stats
                    team_info.pop("under_score_image", None)  # Remove under score image if displaying player stats

            # Check if game is currently playing
            elif " am " not in game["gameStatusText"] or " pm " not in game["gameStatusText"]:
                team_info = append_nba_data(team_info, team_name.split(" ")[-1])
                currently_playing = True

                # Re-structure clock
                if settings.display_nba_play_by_play:
                    team_info["top_info"] = restructure_clock(game)
                else:
                    team_info["bottom_info"] = restructure_clock(game)

            elif settings.display_odds:  # Game has not started yet, get odds if enabled
                home_team_abbr = game.get("homeTeam", {}).get("teamTricode", "")
                away_team_abbr = game.get("awayTeam", {}).get("teamTricode", "")
                team_info["top_info"] = get_nba_odds(game["gameId"], home_team_abbr, away_team_abbr)

            if get_game_type("NBA", team_name) != "":
                # If game type is not empty, then its the Finals, display it
                team_info["under_score_image"] = get_game_type("NBA", team_name)

    return team_info, has_data, currently_playing


def append_nba_data(team_info: dict, team_name: str) -> dict:
    """Get information for NBA team if playing.

    :param team_info: Dictionary where data is stored to display
    :param team_name: The team name to get information for

    :return team_info: dictionary containing team information to display
    """
    # Save away @ home to display if quarter End
    saved_team_names = team_info["above_score_txt"]

    # Get timeouts and if team is in bonus from nba_api.live.nba.endpoints
    data = scoreboard.ScoreBoard().get_dict()
    for game in data["scoreboard"]["games"]:
        if game["homeTeam"]["teamName"] in team_name or game["awayTeam"]["teamName"] in team_name:
            box_score = boxscore.BoxScore(game["gameId"]).get_dict()

            # Many times bonus is None, store it so when it is None then display last known value
            if settings.display_nba_bonus:
                team_info["home_bonus"] = box_score["game"]["homeTeam"]["inBonus"] == "1"
                team_info["away_bonus"] = box_score["game"]["awayTeam"]["inBonus"] == "1"

            if settings.display_nba_timeouts:
                home_timeouts = box_score["game"]["homeTeam"]["timeoutsRemaining"]
                away_timeouts = box_score["game"]["awayTeam"]["timeoutsRemaining"]

                timeout_map = {
                    7: "\u25CF  \u25CF  \u25CF  \u25CF  \u25CF  \u25CF  \u25CF",
                    6: "\u25CF  \u25CF  \u25CF  \u25CF  \u25CF  \u25CF",
                    5: "\u25CF  \u25CF  \u25CF  \u25CF  \u25CF",
                    4: "\u25CF  \u25CF  \u25CF  \u25CF",
                    3: "\u25CF  \u25CF  \u25CF",
                    2: "\u25CF  \u25CF",
                    1: "\u25CF",
                    0: "",
                }
                team_info["away_timeouts"] = timeout_map.get(away_timeouts, "")
                team_info["home_timeouts"] = timeout_map.get(home_timeouts, "")

            if settings.display_nba_shooting:
                home_field_goal_attempt = (box_score["game"]["homeTeam"]["statistics"].get("fieldGoalsAttempted", 0))
                home_field_goal_made = (box_score["game"]["homeTeam"]["statistics"].get("fieldGoalsMade", 0))

                home_3pt_attempt = (box_score["game"]["homeTeam"]["statistics"].get("threePointersAttempted", 0))
                home_3pt_made= (box_score["game"]["homeTeam"]["statistics"].get("threePointersMade", 0))

                home_free_throw_attempt = (box_score["game"]["homeTeam"]["statistics"].get("freeThrowsAttempted", 0))
                home_free_throw_made = (box_score["game"]["homeTeam"]["statistics"].get("freeThrowsMade", 0))

                away_field_goal_attempt = (box_score["game"]["awayTeam"]["statistics"].get("fieldGoalsAttempted", 0))
                away_field_goal_made = (box_score["game"]["awayTeam"]["statistics"].get("fieldGoalsMade", 0))

                away_3pt_attempt = (box_score["game"]["awayTeam"]["statistics"].get("threePointersAttempted", 0))
                away_3pt_made = (box_score["game"]["awayTeam"]["statistics"].get("threePointersMade", 0))

                away_free_throw_attempt = (box_score["game"]["awayTeam"]["statistics"].get("freeThrowsAttempted", 0))
                away_free_throw_made = (box_score["game"]["awayTeam"]["statistics"].get("freeThrowsMade", 0))

                away_stats = (
                    f"FG:{away_field_goal_made}/{away_field_goal_attempt}  "
                    f"3PT:{away_3pt_made}/{away_3pt_attempt}  "
                    f"FT:{away_free_throw_made}/{away_free_throw_attempt}"
                )

                home_stats = (
                    f"FG:{home_field_goal_made}/{home_field_goal_attempt}  "
                    f"3PT:{home_3pt_made}/{home_3pt_attempt}  "
                    f"FT:{home_free_throw_made}/{home_free_throw_attempt}"
                )

                team_info["top_info"] = away_stats + "\t\t " + home_stats

            if settings.display_nba_play_by_play:
                team_info["above_score_txt"] = team_info["bottom_info"]  # Move clock to above score
                team_info["bottom_info"] = get_play_by_play(game["gameId"])
                if "End" in team_info["bottom_info"]:
                    team_info["bottom_info"] = team_info["above_score_txt"]
                    team_info["above_score_txt"] = saved_team_names


            break  # Found team and got data needed, dont continue loop

    return team_info


def restructure_clock(game: dict) -> str:
    """Restructure game clock to get quarter and time left."""
    match = re.match(r"PT(\d+)M(\d+)", game.get("gameClock", ""))
    if not match:
        return ""

    minutes = int(match.group(1))
    seconds = int(float(match.group(2)))
    time_str = f"{minutes}:{seconds:02}"

    quarter = {
        1: "1st",
        2: "2nd",
        3: "3rd",
        4: "4th",
    }.get(game.get("period", 0), "Overtime")

    if time_str == "0:00":
        return {
            "1st": "End of 1st",
            "2nd": "Halftime",
            "3rd": "End of 3rd",
            "4th": "End of 4th",
        }.get(quarter, f"End of {quarter}")

    return f"{time_str} - {quarter}"

def get_play_by_play(game_id: int) -> str:
    """Get play by play information."""
    pbp = playbyplay.PlayByPlay(game_id)
    actions = pbp.get_dict()["game"]["actions"]  # plays are referred to in the live data as `actions`
    last_action = actions[-1]

    return " " + str(last_action["description"])



def _nba_spread_line(market: dict, home_abbr: str, away_abbr: str) -> str:
    home_spread = None
    away_spread = None
    for book in market.get("books", []):
        if book.get("name") == "FanDuel":
            for outcome in book.get("outcomes", []):
                if outcome["type"] == "home":
                    home_spread = float(outcome["spread"])
                elif outcome["type"] == "away":
                    away_spread = float(outcome["spread"])
    if home_spread is not None and away_spread is not None:
        if home_spread < away_spread:
            return f"Spread: {home_abbr} {home_spread} \t "
        return f"Spread: {away_abbr} {away_spread} \t "
    return "Spread: N/A \t "

def _nba_moneyline(market: dict, home_abbr: str, away_abbr: str) -> str:
    home_decimal = None
    away_decimal = None
    for book in market.get("books", []):
        if book.get("name") == "FanDuel":
            for outcome in book.get("outcomes", []):
                if outcome["type"] == "home":
                    home_decimal = float(outcome["odds"])
                elif outcome["type"] == "away":
                    away_decimal = float(outcome["odds"])
    if home_decimal is not None and away_decimal is not None:
        home_moneyline = f"+{int((home_decimal - 1) * 100)}"
        away_moneyline = f"-{int((1 / away_decimal - 1) * 100)}"
        if home_decimal > away_decimal:
            return f"MoneyLine: {home_abbr} {home_moneyline}".replace("--", "-")

        return f"MoneyLine: {away_abbr} {away_moneyline}".replace("--", "-")
    return "MoneyLine: N/A"

def get_nba_odds(game_id: int, home_abbr: str, away_abbr: str) -> str:
    """Get NBA odds information.

    :param game_id: The game ID to get odds for
    :param home_abbr: The home team abbreviation
    :param away_abbr: The away team abbreviation

    :return: string containing betting lines
    """
    games_list = odds.Odds().get_dict()["games"]
    betting_lines = ""
    for game in games_list:
        if game.get("gameId") != game_id:
            continue
        for market in game.get("markets", []):
            if market.get("name") == "spread":
                betting_lines = _nba_spread_line(market, home_abbr, away_abbr)
            elif market.get("name") == "2way":
                betting_lines += _nba_moneyline(market, home_abbr, away_abbr)
        break
    return betting_lines
