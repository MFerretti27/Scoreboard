"""Get player statistics for various sports leagues."""
from __future__ import annotations

import requests  # type: ignore[import]
from nba_api.stats.endpoints import leaguedashteamstats, leaguestandingsv3

from helper_functions.api_utils.exceptions import DataValidationError
from helper_functions.api_utils.retry import retry_api_call
from helper_functions.api_utils.validators import validate_nba_standings
from helper_functions.logging.logger_config import logger


def get_team_stats(team_league: str, home_team_name: str, away_team_name: str = "") -> tuple[str, str]:
    """Get the team statistics for the current season.

    :param team_league: The league of the team (e.g., MLB, NHL, NBA, NFL)
    :param home_team_name: The name of the home team
    :param away_team_name: The name of the away team

    :return: Tuple containing team statistics strings
    """
    try:
        if "MLB" in team_league.upper():
            return "", ""
        if "NHL" in team_league.upper():
            return get_nhl_team_stats(home_team_name, away_team_name)
        if "NBA" in team_league.upper():
            return get_nba_team_stats(home_team_name, away_team_name)
        if "NFL" in team_league.upper():
            return get_nfl_team_stats(home_team_name, away_team_name)
    except Exception:
        logger.debug("Error getting team stats for %s vs %s in league %s",
                     home_team_name, away_team_name, team_league)
        return "", ""
    return "", ""

@retry_api_call
def get_nba_team_stats(home_team_name: str, away_team_name: str = "") -> tuple[str, str]:
    """Get NBA team stats for the current season including shooting and foul percentages."""
    standings = leaguestandingsv3.LeagueStandingsV3().get_dict()

    # Validate standings structure
    try:
        validate_nba_standings(standings, home_team_name)
    except DataValidationError as e:
        logger.warning(f"Invalid NBA standings data: {e!s}")

    home_stats = {}
    away_stats = {}

    away_stats_str = ""
    home_stats_str = ""

    # Get detailed team stats including shooting percentages once
    team_stats_data = leaguedashteamstats.LeagueDashTeamStats(
        measure_type_detailed_defense="Base",
        per_mode_detailed="PerGame",
        season_type_all_star="Regular Season",
    ).get_dict()

    # Validate team stats structure
    try:
        validate_nba_standings(team_stats_data, home_team_name)
    except DataValidationError as e:
        logger.warning(f"Invalid NBA team stats data: {e!s}")

    # Build the full list of team stats once
    team_stats = []
    for team in standings["resultSets"][0]["rowSet"]:
        team_id = team[2]

        # Find matching team in detailed stats
        detailed_stats = None
        for stats_team in team_stats_data["resultSets"][0]["rowSet"]:
            if stats_team[0] == team_id:
                detailed_stats = stats_team
                break

        team_stat = {
            "team_id": team[2],
            "team_name": team[3] + " " + team[4],
            "division": team[10],
            "conference": team[6],
            "home_record": team[18],
            "road_record": team[19],
            "conference_record": team[7],
            "playoff_rank": team[8],
            "division_record": team[11],
            "division_rank": team[12],
        }

        # Add detailed stats if available
        if detailed_stats:
            team_stat.update({
                "points_per_game": detailed_stats[26],
                "rebounds_per_game": detailed_stats[18],
                "assists_per_game": detailed_stats[19],
                "turnovers_per_game": detailed_stats[20],
                "steals_per_game": detailed_stats[21],
                "blocks_per_game": detailed_stats[22],
                "field_goals_made": detailed_stats[7],
                "field_goals_attempted": detailed_stats[8],
                "three_pointers_made": detailed_stats[10],
                "three_pointers_attempted": detailed_stats[11],
                "free_throws_made": detailed_stats[13],
                "free_throws_attempted": detailed_stats[14],
                "offensive_rebounds": detailed_stats[16],
                "defensive_rebounds": detailed_stats[17],
                "personal_fouls": detailed_stats[23],
            })

        team_stats.append(team_stat)

    # Look up stats for the requested teams using the prebuilt list
    for team_name in [home_team_name, away_team_name]:
        if not team_name:
            continue
        team_name_lower = str(team_name).lower()
        for team_stat in team_stats:
            if (team_name_lower in team_stat["team_name"].lower() or
                str(team_stat["team_id"]) == str(team_name)):
                if team_name.lower() == home_team_name.lower():
                    home_stats = team_stat
                    home_stats_str = f"{team_stat.get('team_name', '')} Season Stats:\n\n"
                else:
                    away_stats = team_stat
                    away_stats_str = f"{team_stat.get('team_name', '')} Season Stats:\n\n"

    home_stats.pop("team_id", None)
    away_stats.pop("team_id", None)
    home_stats.pop("team_name", None)
    away_stats.pop("team_name", None)

    if home_stats or away_stats:
        for key, value in home_stats.items():
            home_stats_str += f"{key.replace('_', ' ').title()}: {value}\n"

        for key, value in away_stats.items():
            away_stats_str += f"{key.replace('_', ' ').title()}: {value}\n"

    return home_stats_str, away_stats_str



def get_nhl_team_stats(home_team_name: str, away_team_name: str = "") -> tuple[str, str]:
    """Get NHL team stats for the current season including shooting and efficiency stats.

    :param home_team_name: The name of the home team
    :param away_team_name: The name of the away team

    :return: Tuple containing player statistics strings
    """
    # Get standings data
    record_data = requests.get("https://api-web.nhle.com/v1/standings/now", timeout=10)
    standings = record_data.json()

    team_stats = []
    home_stats = {}
    away_stats = {}

    # Build full team_stats list once from standings
    for team in standings["standings"]:
        team_name_full = team["teamName"]["default"]

        team_stat = {
            "team_name": team_name_full,
            "division": team.get("divisionName", ""),
            "conference": team.get("conferenceName", ""),
            "home_record": f"{team.get('homeWins', 0)}-{team.get('homeLosses', 0)}-{team.get('homeTies', 0)}",
            "road_record": f"{team.get('roadWins', 0)}-{team.get('roadLosses', 0)}-{team.get('roadTies', 0)}",
            "goals_for": team.get("goalFor", 0),
            "goals_against": team.get("goalAgainst", 0),
            "goal_diff": team.get("goalDifferential", 0),
            "points": team.get("points", 0),
            "wins_in_ot": team.get("otLosses", 0),
            "streak": f"{team.get('streakCode', '')}{team.get('streakCount', 0)}",
        }

        team_stats.append(team_stat)

    # Filter for the requested home and away teams using the prebuilt team_stats list
    for team_name in [home_team_name, away_team_name]:
        if not team_name:
            continue
        team_name_lower = str(team_name).lower()
        for team_stat in team_stats:
            if team_name_lower in team_stat["team_name"].lower():
                if team_name == home_team_name:
                    home_stats = team_stat
                else:
                    away_stats = team_stat

    away_stats_str = f"{away_team_name} Season Stats:\n\n"
    home_stats_str = f"{home_team_name} Season Stats:\n\n"

    home_stats.pop("team_name", None)
    away_stats.pop("team_name", None)
    if home_stats or away_stats:
        for key, value in home_stats.items():
            home_stats_str += f"{key.replace('_', ' ').title()}: {value}\n\n"

        for key, value in away_stats.items():
            away_stats_str += f"{key.replace('_', ' ').title()}: {value}\n\n"

    return home_stats_str, away_stats_str


@retry_api_call
def get_nfl_team_stats(home_abbr: str, away_abbr: str = "") -> tuple[str, str]:
    """Get comprehensive team stats from ESPN teams API.

    :param home_abbr: Home team abbreviation (e.g., 'DET', 'MIN')
    :param away_abbr: Away team abbreviation (e.g., 'DET', 'MIN')
    :return: Tuple containing home and away team stats strings.
    """
    home_team_stats = ""
    away_team_stats = ""

    for team_abbr in [home_abbr, away_abbr]:
        team_url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams/{team_abbr}"
        team_resp = requests.get(team_url, timeout=10)
        team_data = team_resp.json()

        team_name = team_data.get("team", {}).get("displayName", "")
        team_stat = f"{team_name} Season Stats:\n\n"

        # Basic team info
        team = team_data.get("team", {})

        # Records with home/road splits
        record_items = team.get("record", {}).get("items", [])
        for record in record_items:
            record_type = record.get("type", "")
            summary = record.get("summary", "")

            if record_type == "home":
                team_stat += "Home Record: " + summary + "\n\n"
            elif record_type == "road":
                team_stat += "Road Record: " + summary + "\n\n"
            elif record_type == "total":

                # Extract detailed stats from total record
                stat_map = {
                    "divisionWins": ("DivisionWins", int),
                    "divisionLosses": ("DivisionLosses", int),
                    "divisionTies": ("DivisionTies", int),
                    "divisionWinPercent": ("DivisionWinPercent", str),
                    "avgPointsFor": ("AvgPointsFor", str),
                    "avgPointsAgainst": ("AvgPointsAgainst", str),
                    "pointsFor": ("PointsFor", int),
                    "pointsAgainst": ("PointsAgainst", int),
                    "playoffSeed": ("PlayoffSeed", int),
                    "streak": ("Streak", int),
                }

                stats = record.get("stats", [])
                for stat in stats:
                    stat_name = stat.get("name", "")
                    stat_value = stat.get("value", "")

                    if stat_name in stat_map:
                        label, caster = stat_map[stat_name]
                        try:
                            value_str = str(caster(stat_value))
                        except Exception:
                            value_str = str(stat_value)
                        team_stat += f"{label}: {value_str}\n\n"
        # Standing summary
        team_stat += team_data.get("standingSummary", "")

        # Next event info
        next_events = team_data.get("nextEvent", [])
        if next_events:
            next_game = next_events[0]
            team_stat += next_game.get("shortName", "")
            team_stat += next_game.get("date", "")

        if team_abbr == home_abbr:
            home_team_stats = team_stat
        else:
            away_team_stats = team_stat

    return home_team_stats, away_team_stats
