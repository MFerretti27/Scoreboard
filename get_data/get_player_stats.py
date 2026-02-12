"""Get player statistics for various sports leagues."""

from datetime import datetime, timedelta

import requests  # type: ignore[import]
import statsapi  # type: ignore[import]
from nba_api.live.nba.endpoints import boxscore, scoreboard

from helper_functions.logger_config import logger

from .get_mlb_data import API_FIELDS
from .get_team_id import get_mlb_team_id, get_nhl_game_id  # type: ignore[import]


def get_player_stats(team_league: str, team_name: str) -> tuple[str, str]:
    """Get the player statistics for a specific game.

    :param team_league: The league of the team (e.g., MLB, NHL, NBA, NFL)
    :param team_name: The name of the team

    :return: Tuple containing player statistics strings
    """
    try:
        if "MLB" in team_league.upper():
            return (get_mlb_player_stats(team_name))
        if "NHL" in team_league.upper():
            return (get_nhl_player_stats(team_name))
        if "NBA" in team_league.upper():
            return (get_nba_player_stats(team_name))
        if "NFL" in team_league.upper():
            return (get_nfl_player_stats(team_name))
    except Exception:
        logger.exception("Error getting player stats for %s in league %s", team_name, team_league)
        return "", ""
    return "", ""

def get_nba_player_stats(team_name: str) -> tuple[str, str]:
    """Get NBA player statistics for the starting five players of a team.

    :param team_name: The name of the team
    :return: Tuple containing home and away player statistics strings
    """
    try:
        games = scoreboard.ScoreBoard().get_dict()
        game_id = ""
        scoreboard_data = games.get("scoreboard", {})
        games_list = scoreboard_data.get("games", [])
        
        for game in games_list:
            home_team = game.get("homeTeam", {})
            away_team = game.get("awayTeam", {})
            home_team_name = home_team.get("teamName", "")
            away_team_name = away_team.get("teamName", "")
            if home_team_name in team_name or away_team_name in team_name:
                game_id = game.get("gameId", "")
                break
        
        if not game_id:
            logger.warning("No NBA game found for team: %s", team_name)
            return "", ""

        box_score_data = boxscore.BoxScore(game_id).get_dict()
        game_data = box_score_data.get("game", {})
        home_players = game_data.get("homeTeam", {}).get("players", [])
        away_players = game_data.get("awayTeam", {}).get("players", [])
        
        if not home_players or not away_players:
            logger.warning("No player data available for NBA game: %s", game_id)
            return "", ""
            
        home_player_stats = f"{home_team_name} Players Stats:\n\n"
        away_player_stats = f"{away_team_name} Players Stats:\n\n"

        def get_starting_five(players: list) -> list:
            """Get the starting five players from the list.

            :param players: List of player dictionaries
            :return: List of starting five player dictionaries
            """
            # Filter for starters (starter == '1'), status ACTIVE, played == '1'
            starters = ([p for p in players if p.get("starter") == "1"
                         and p.get("status") == "ACTIVE" and p.get("played") == "1"])
            # If more than 5, take first 5 by 'order'
            return sorted(starters, key=lambda p: p.get("order", 0))[:5]

        for p in get_starting_five(home_players):
            stats = p.get("statistics", {})
            fg_made = stats.get("fieldGoalsMade", 0)
            three_made = stats.get("threePointersMade", 0)
            two_pt_made = fg_made - three_made
            total_points = (two_pt_made * 2) + (three_made * 3) + stats.get("freeThrowsMade", 0)
            blk = stats.get("blocks", None)
            stl = stats.get("steals", None)
            assists = stats.get("assists", None)
            
            player_name = p.get("name", "Unknown")
            position = p.get("position", "")

            home_player_stats += (f"{position} - {' '.join(player_name.split()[1:])}\nPTS: {total_points},  "
                                   f"AST: {assists}, BLK: {blk},  STL: {stl}\n\n")

        for p in get_starting_five(away_players):
            stats = p.get("statistics", {})
            fg_made = stats.get("fieldGoalsMade", 0)
            three_made = stats.get("threePointersMade", 0)
            two_pt_made = fg_made - three_made
            total_points = (two_pt_made * 2) + (three_made * 3) + stats.get("freeThrowsMade", 0)
            blk = stats.get("blocks", None)
            stl = stats.get("steals", None)
            assists = stats.get("assists", None)
            
            player_name = p.get("name", "Unknown")
            position = p.get("position", "")

            away_player_stats += (f"{position} - {' '.join(player_name.split()[1:])}\nPTS: {total_points},  "
                                   f"AST: {assists}, BLK: {blk},  STL: {stl}\n\n")

        return home_player_stats.rstrip(""), away_player_stats.rstrip("")
    except Exception as e:
        logger.exception("Error getting NBA player stats for %s: %s", team_name, str(e))
        return "", ""


def get_nhl_player_stats(team_name: str) -> tuple[str, str]:
    """Get NHL player statistics for the starting five players of a team.

    :param team_name: The name of the team
    :return: Tuple containing home and away player statistics strings
    """
    try:
        team_id = get_nhl_game_id(team_name)
        live_data = requests.get(f"https://api-web.nhle.com/v1/gamecenter/{team_id}/boxscore", timeout=5)
        live_data.raise_for_status()
        live = live_data.json()
    except (requests.exceptions.RequestException, ValueError, IndexError) as e:
        logger.warning("Error fetching NHL player stats for %s: %s", team_name, str(e))
        return "", ""

    away_team_name = live.get("awayTeam", {}).get("commonName", {}).get("default", "")
    home_team_name = live.get("homeTeam", {}).get("commonName", {}).get("default", "")

    home_stats = f"{home_team_name} Players Stats:\n\n"
    away_stats = f"{away_team_name} Players Stats:\n\n"

    if "homeTeam" in live and "awayTeam" in live and "playerByGameStats" in live:
        home_team_stats = live["playerByGameStats"]["homeTeam"]
        away_team_stats = live["playerByGameStats"]["awayTeam"]
        for team_stats, team in [(home_team_stats, "home"), (away_team_stats, "away")]:
            # Get top starters: 1 of each forward position (C, L, R) + top 2 defensemen by TOI
            forwards = team_stats.get("forwards", [])
            defense = team_stats.get("defense", [])

            # Convert TOI to seconds for sorting
            def toi_seconds(p: dict) -> int:
                t = p.get("toi", "00:00")
                parts = t.split(":")
                return int(parts[0]) * 60 + int(parts[1]) if len(parts) == 2 else 0

            # Group forwards by position and get top player by TOI from each position
            positions_dict: dict[str, list[dict]] = {"C": [], "L": [], "R": []}
            for f in forwards:
                pos = f.get("position", "")
                if pos in positions_dict:
                    positions_dict[pos].append(f)

            # Get the player with most TOI for each position
            forward_starters = []
            for pos in ["C", "L", "R"]:
                if positions_dict[pos]:
                    top_player = sorted(positions_dict[pos], key=toi_seconds, reverse=True)[0]
                    forward_starters.append(top_player)

            # Get top 2 defensive players by TOI
            defense_sorted = sorted(defense, key=toi_seconds, reverse=True)[:2]
            starters = forward_starters + defense_sorted
            for p in starters:
                name = " ".join(p["name"]["default"].split()[1:])
                pos = p.get("position", "")
                goals = p.get("goals", 0)
                assists = p.get("assists", 0)
                sog = p.get("sog", 0)
                toi = p.get("toi", "")

                if team == "home":
                    home_stats += f"{pos} - {name}\nG:{goals}  A:{assists}  SOG:{sog}  TOI:{toi}\n\n"
                else:
                    away_stats += f"{pos} - {name}\nG:{goals}  A:{assists}  SOG:{sog}  TOI:{toi}\n\n"

    return home_stats.rstrip("\n"), away_stats.rstrip("\n")


def get_mlb_player_stats(team_name: str) -> tuple[str, str]:
    """Get MLB player statistics for the starting five players of a team.

    :param team_name: The name of the team
    :return: Tuple containing home and away player statistics strings
    """
    home_player_stats = ""
    away_player_stats = ""

    try:
        today = (datetime.now()).strftime("%Y-%m-%d")
        three_days_later = (datetime.now() + timedelta(days=-90)).strftime("%Y-%m-%d")
        data = statsapi.schedule(
                team=get_mlb_team_id(team_name), include_series_status=True, start_date=today, end_date=three_days_later,
            )
        game_pk = statsapi.get("game", {"gamePk": data, "fields": API_FIELDS})
        
        if not game_pk:
            logger.warning("No MLB game found for team: %s", team_name)
            return "", ""
            
        game_id = game_pk[-1].get("game_id")
        if not game_id:
            logger.warning("No game ID found for MLB team: %s", team_name)
            return "", ""

        url = f"https://statsapi.mlb.com/api/v1.1/game/{game_id}/feed/live"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data1 = response.json()

        live_data = data1.get("liveData", {})
        boxscore = live_data.get("boxscore", {})
        teams = boxscore.get("teams", {})
        
        if not teams:
            logger.warning("No team data in MLB boxscore")
            return "", ""

        for team_type in ["home", "away"]:
            team_data = teams.get(team_type, {})
            team_players = team_data.get("players", {})

            # Get the 9 starters from battingOrder
            batting_order = team_data.get("battingOrder", [])
            for pid in batting_order:
                pid_str = f"ID{pid}"
                player = team_players.get(pid_str)
                if not player:
                    continue
                name = " ".join(player["person"]["fullName"].split()[1:])
                position = player.get("position", {}).get("abbreviation", "-")
                if position == "C":
                    position = position.replace("C", "C ") # Make catcher position two characters for alignment
                game_bat = player.get("stats", {}).get("batting", None)
                season_bat = player.get("seasonStats", {}).get("batting", None)
                if game_bat:
                    rbi = game_bat.get("rbi", 0)
                    rbi = ", " + str(rbi) + " RBI" if rbi > 0 else ""

                    hits = game_bat.get("hits", 0)
                    at_bats = game_bat.get("atBats", 0)

                    summary = f"{hits}/{at_bats}"
                    avg = season_bat.get("avg") if season_bat else "-"
                    if avg == ".000":
                        continue  # Skip players with .000 average

                    # Print all plate appearance outcomes for this player
                    pa_outcomes = []
                    plays = live_data.get("plays", {}).get("allPlays", [])
                    for play in plays:
                        matchup = play.get("matchup", {})
                        batter = matchup.get("batter", {})
                        if batter.get("id") == pid:
                            result = play.get("result", {})
                            desc = result.get("description", "")
                            pa_outcomes.append(desc)
                    # Map eventType to short codes
                    event_map = {
                        "Home Run": "HR",
                        "Walk": "BB",
                        "Strikeout": "K",
                        "Single": "1B",
                        "Double": "2B",
                        "Triple": "3B",
                        "Hit By Pitch": "HBP",
                        "Sac Fly": "SF",
                        "Sac Bunt": "SH",
                        "Groundout": "GO",
                        "Flyout": "FO",
                        "Lineout": "LO",
                        "Pop Out": "PO",
                        "Bunt Groundout": "BGO",
                        "Bunt Pop Out": "BPO",
                        "Foul Out": "FO",
                        "Fielders Choice": "FC",
                        "Field Out": "OUT",
                        "Forceout": "OUT",
                        "Grounded Into DP": "GIDP",
                        "Intent Walk": "IBB",
                        "Catcher Interference": "CI",
                        "Error": "E",
                        "Strikeout Double Play": "KDP",
                    }
                    # For each play, print only the event code, numbered
                    pa_events: list[str] = []
                    for p in plays:
                        matchup = p.get("matchup", {})
                        batter = matchup.get("batter", {})
                        if batter.get("id") == pid:
                            result = p.get("result", {})
                            event = result.get("event", "")
                            event_code = event_map.get(event, event.upper() if event else event)
                            pa_events.append(event_code)
                    short = " ".join(pa_events)
                    if team_type == "home":
                        home_player_stats += f"{position} {name}: AVG {avg} H/AB: {summary} | {short}{rbi}\n\n"
                    else:
                        away_player_stats += f"{position} {name}: AVG {avg} H/AB: {summary} | {short}{rbi}\n\n"

        return home_player_stats.rstrip("\n"), away_player_stats.rstrip("\n")
    except Exception as e:
        logger.exception("Error getting MLB player stats for %s: %s", team_name, str(e))
        return "", ""


def get_nfl_player_stats(team_name: str) -> tuple[str, str]:
    """Get NFL player statistics for the starting players of a team.

    :param team_name: The name of the team
    :return: Tuple containing home and away player statistics strings
    """
    home_player_stats = ""
    away_player_stats = ""
    
    try:
        nfl = requests.get("https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard", timeout=5)
        nfl.raise_for_status()
        nfl_data = nfl.json()
        
        index = 0
        for event in nfl_data.get("events", []):
            if team_name not in event.get("name", ""):
                index += 1
                continue

            events = nfl_data.get("events", [])
            if index >= len(events):
                logger.warning("Event index out of range for NFL team: %s", team_name)
                return "", ""
                
            competition = events[index].get("competitions", [{}])[0]
            leaders = competition.get("leaders", [])
            
            if len(leaders) < 3:
                logger.warning("Insufficient leader data for NFL team: %s", team_name)
                return "", ""
            
            # Passing leader
            passing_leaders = leaders[0].get("leaders", [])
            if passing_leaders:
                qb = passing_leaders[0].get("displayValue", "N/A")
                qb_athlete = passing_leaders[0].get("athlete", {})
                qb_name = " ".join(qb_athlete.get("shortName", "Unknown").split()[1:])
            else:
                qb, qb_name = "N/A", "Unknown"

            # Rushing leader
            rushing_leaders = leaders[1].get("leaders", [])
            if rushing_leaders:
                rush = rushing_leaders[0].get("displayValue", "N/A")
                rush_athlete = rushing_leaders[0].get("athlete", {})
                rush_name = " ".join(rush_athlete.get("shortName", "Unknown").split()[1:])
            else:
                rush, rush_name = "N/A", "Unknown"

            # Receiving leader
            receiving_leaders = leaders[2].get("leaders", [])
            if receiving_leaders:
                receiving = receiving_leaders[0].get("displayValue", "N/A")
                receiving_athlete = receiving_leaders[0].get("athlete", {})
                receiving_name = " ".join(receiving_athlete.get("shortName", "Unknown").split()[1:])
            else:
                receiving, receiving_name = "N/A", "Unknown"

            # There is only one set of leaders for the entire game, only put in one column
            away_player_stats = f"Passing Leader\n {qb_name}: {qb}\n\nRushing Leader\n{rush_name}: {rush}"
            away_player_stats += "\n\n" + f"Receiving Leader\n{receiving_name}: {receiving}"
            break  # Found the game, exit loop

        return home_player_stats, away_player_stats
    except Exception as e:
        logger.exception("Error getting NFL player stats for %s: %s", team_name, str(e))
        return "", ""
