"""Get new team names and divisions from API's storing results in get_team_league.py."""
import difflib
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

import FreeSimpleGUI as Sg  # type: ignore[import]
import statsapi  # type: ignore[import]
from nba_api.stats.endpoints import leaguestandings  # type: ignore[import]
from nba_api.stats.static import teams as nba_teams  # type: ignore[import]
from nhlpy.nhl_client import NHLClient  # type: ignore[import]

import get_data.get_team_league
from get_data.get_team_league import MLB, NBA, NFL, NHL
from helper_functions.logger_config import logger
from helper_functions.main_menu_helpers import read_teams_from_file, update_teams


def format_teams_block(teams: list[list[str]]) -> str:
    """Format the 'teams' block using double quotes."""
    if isinstance(teams, list) and all(isinstance(item, list) and len(item) == 1 for item in teams):
        formatted = "teams = [\n"
        for item in teams:
            team_name = item[0].replace('"', '\\"')  # escape quotes
            formatted += f'    ["{team_name}"],\n'
        formatted += "]"
        return formatted
    return f"teams = {teams!s}"

def normalize(name: str) -> str:
    """Lowercase, remove punctuation (keep spaces), collapse spaces."""
    name = name.lower()
    name = re.sub(r"[^\w\s]", "", name)        # remove punctuation
    return re.sub(r"\s+", " ", name).strip()   # collapse spaces

def split_city_nickname(name: str) -> tuple[str, str]:
    """Do a Heuristic split.

    Everything except the last token is 'city',
    last token is 'nickname'. If only one token, city="" and nickname=token.
    """
    tokens = name.split()
    if len(tokens) == 0:
        return "", ""
    if len(tokens) == 1:
        return "", tokens[0]
    return " ".join(tokens[:-1]), tokens[-1]

def similarity(a: str, b: str) -> float:
    """Construct a SequenceMatcher."""
    return difflib.SequenceMatcher(None, a, b).ratio()

def get_new_team_names(league: str) -> tuple:
    """Grab new team names from API's.

    :param league: league of which to grab names for

    :return renamed: list of tuple's showing what team names changed
    :return new_list: list of all new team names found
    :return str: message if getting new teams was successful
    """
    team_names_before = {
        "MLB": MLB,
        "NHL": NHL,
        "NBA": NBA,
        "NFL": NFL,
    }.get(league, [])

    new_list = []
    old_list = team_names_before.copy()
    renamed: list = []
    try:
        if league == "MLB":
            teams = statsapi.get("teams", {"sportIds": 1})["teams"]
            new_list.extend([team["name"] for team in teams])

        elif league == "NHL":
            client = NHLClient()
            new_list.extend([team["name"] for team in client.teams.teams()])

        elif league == "NBA":
            new_list.extend([team["full_name"] for team in nba_teams.get_teams()])
    except Exception:
        logger.exception("Getting new team names failed")
        return [], [], "Failed to Get New Team Names"

    candidates, city_count_new, city_count_old = compare_teams(old_list, new_list)
    matched_old, matched_new, renamed = greedy_matching(candidates, city_count_new, city_count_old)

    # After greedy matching, anything in new not matched is 'added', anything in old not matched is 'removed'
    added = [n for n in new_list if n not in matched_new]
    removed = [o for o in old_list if o not in matched_old]
    logger.info(f"\nNew and not matched: {added}\n")
    logger.info(f"\nOld and not matched: {removed}\n")

    renamed = []
    for new_team, old_team in zip(added, removed, strict=False):
        renamed.append((old_team, new_team))

    logger.info("Renamed Teams: %s", renamed)
    return renamed, new_list, "Getting New Team Name's Successful!"

def format_division(league: str, division_name: str) -> str | None:
    """Return a standardized division key for a given league."""
    if league == "MLB":
        division = (
            "MLB_"
            + division_name.replace("American League", "AL")
            .replace("National League", "NL")
            .replace(" ", "_")
        )
        return division.upper()

    if league == "NHL":
        return f"NHL_{division_name.replace(' ', '_').upper()}_DIVISION"

    if league == "NBA":
        return f"NBA_{division_name.replace(' ', '_').upper()}_DIVISION"
    return None


def update_new_division(league: str) -> str:
    """Update team divisions for a league."""
    new_team_divisions: dict[str | None, list[str]] = defaultdict(list)

    try:
        if league == "MLB":
            teams = statsapi.get("teams", {"sportIds": 1})["teams"]
            for team in teams:
                division_name = team.get("division", {}).get("name", "N/A")
                division = format_division("MLB", division_name)
                new_team_divisions[division].append(team["name"])

        elif league == "NHL":
            client = NHLClient()
            for team in client.teams.teams():
                division_name = team.division.get("name") if hasattr(team, "division") else "N/A"
                division = format_division("NHL", division_name)
                new_team_divisions[division].append(team["name"])

        elif league == "NBA":
            nba_stats = leaguestandings.LeagueStandings().get_dict()
            for team in nba_stats["resultSets"][0]["rowSet"]:
                division_name = team[9] if len(team) > 9 else "N/A"
                division = format_division("NBA", division_name)
                new_team_divisions[division].append(f"{team[3]} {team[4]}")

        logger.info("New Divisions:\n %s\n", new_team_divisions)

        # Using key (list name) and value (teams in list) update division lists in get_team_league.py
        for key, value in new_team_divisions.items():
            str_key = str(key)
            update_new_names(str_key, value)

    except Exception:
        logger.exception("Failed getting/writing divisions")
        return "Updating Teams Failed"

    return "Updating Teams Successful!"


def update_new_names(list_to_update: str, new_teams: list, renamed: list | None=None) -> None:
    """Update specified list in a Python file.

    :param list_to_update: List of which to change the team names
    :param renamed: List teams and what they were renamed to
    :param new_teams: New teams that are being added to list
    """
    team_file_path = Path("get_data/get_team_league.py")
    content = team_file_path.read_text(encoding="utf-8")

    pattern = re.compile(
        rf"(^\s*{re.escape(list_to_update)}\s*=\s*\[)([\s\S]*?)(\]\s*,?)",
        re.MULTILINE,
    )

    match: re.Match[str]| None = pattern.search(content)

    if not match:
        return
    _, list_block, _ = match.group(1), match.group(2), match.group(3)

    # Sort the new team list alphabetically
    sorted_names = sorted(new_teams)

    # Build the block preserving indentation from the original
    indent_match = re.match(r"(\s*)", list_block.split("\n")[0])
    indent = indent_match.group(1) if indent_match else "    "

    # Join into wrapped lines of max ~100 chars
    formatted_lines = []
    line = indent
    for name in sorted_names:
        item = f'"{name}", '
        if len(line) + len(item) > 120:  # wrap line if too long
            formatted_lines.append(line.rstrip())
            line = indent + item
        else:
            line += item
    if line.strip():
        formatted_lines.append(line.rstrip())

    new_block = "\n".join(formatted_lines)

    new_content = content[: match.start(2)] + "\n" + new_block + "\n" + content[match.end(2):]

    team_file_path.write_text(new_content, encoding="utf-8")

    # Update current in-memory instance so changes take effect immediately
    current_list = getattr(get_data.get_team_league, list_to_update)
    current_list.clear()
    current_list.extend(sorted_names)

    # update settings.py file team name if it needs to change
    if list_to_update in ["MLB", "NFL", "NBA", "NHL"] and renamed:
        remove_specifically = []
        settings_dict = read_teams_from_file()
        for renamed_team in renamed:
            if renamed_team[0] in settings_dict:
                settings_dict[settings_dict.index(renamed_team[0])] = renamed_team[1]
                remove_specifically.append(renamed_team[0])
        update_teams(settings_dict, list_to_update, specific_remove=remove_specifically)


def compare_teams(old_list: list[str],
                  new_list: list[str]) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    """Compare old team names to new team names to see if any changed.

    :param old_list: list of old team names
    :param new_list: list of new team names
    :return: list of dictionaries containing old and new team names
    """
    # normalize inputs but keep original labels for results
    old_norm = [(o, normalize(o)) for o in old_list]
    new_norm = [(n, normalize(n)) for n in new_list]

    # quick lookups
    city_count_new: dict[str, Any] = {}
    city_count_old: dict[str, Any] = {}
    old_meta: dict[str, Any] = {}
    new_meta: dict[str, Any] = {}

    for orig, norm in old_norm:
        city, nick = split_city_nickname(norm)
        old_meta[orig] = {"norm": norm, "city": city, "nick": nick}
        city_count_old[city] = city_count_old.get(city, 0) + 1

    for orig, norm in new_norm:
        city, nick = split_city_nickname(norm)
        new_meta[orig] = {"norm": norm, "city": city, "nick": nick}
        city_count_new[city] = city_count_new.get(city, 0) + 1

    # Build candidate scores for every old x new
    candidates = []
    for old_orig, old_data in old_meta.items():
        for new_orig, new_data in new_meta.items():
            full_sim = similarity(old_data["norm"], new_data["norm"])
            nick_sim = similarity(old_data["nick"], new_data["nick"])
            # Score is a weighted mix but the decision uses thresholds/extra rules
            score = 0.65 * full_sim + 0.35 * nick_sim
            candidates.append({
                "old": old_orig,
                "new": new_orig,
                "full_sim": full_sim,
                "nick_sim": nick_sim,
                "city_same": (old_data["city"] != "" and old_data["city"] == new_data["city"]),
                "score": score,
            })

    # Sort candidates high->low so greedy matching picks best pairs first
    candidates.sort(key=lambda c: c["score"], reverse=True)
    return candidates, city_count_new, city_count_old

def greedy_matching(candidates: list[dict[str, Any]], city_count_new: dict[str, Any],
                    city_count_old: dict[str, Any]) -> tuple[set, set, list[tuple[str, str]]]:
    """Greedily match old and new team names based on similarity scores and rules.

    :param candidates: list of candidate old-new pairs with similarity scores
    :param city_count_new: count of how many teams are in each city in new list
    :param city_count_old: count of how many teams are in each city in old list

    :return: sets of matched old and new names, and list of renamed pairs
    """
    matched_old = set()
    matched_new = set()
    renamed = []

    for c in candidates:
        o = c["old"]
        n = c["new"]
        if o in matched_old or n in matched_new:
            continue

        # RULES to accept this pair as a rename:
        # 1) If nickname similarity is high enough -> accept
        if c["nick_sim"] >= 0.60 and c["full_sim"] >= 0.70:
            matched_old.add(o)
            matched_new.add(n)
            renamed.append((o, n))
            continue

        # 2) If full similarity is very high and nickname at least somewhat similar
        if c["full_sim"] >= 0.90 and c["nick_sim"] >= 0.35:
            matched_old.add(o)
            matched_new.add(n)
            renamed.append((o, n))
            continue

        # 3) City rule: same city and that city appears exactly once in new and once in old
        #    This allows "Washington Redskins" -> "Washington Commanders" detection,
        #    but prevents mapping in cities with multiple teams (LA).
        if c["city_same"]:
            old_city = split_city_nickname(normalize(o))[0]
            if city_count_new.get(old_city, 0) == 1 and city_count_old.get(old_city, 0) == 1:
                # treat as rename (even if nicknames very different), because unique city match
                matched_old.add(o)
                matched_new.add(n)
                renamed.append((o, n))

        # otherwise not confident enough -> skip
    return matched_old, matched_new, renamed
