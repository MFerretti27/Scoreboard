"""Store team names and leagues, with a function to get the league for a given team name.

It compares the input team name with a list of known team names in various leagues (NBA, MLB, NFL, NHL).
The function returns a tuple containing the league and sport name if a match is found with a score of 70 or higher.
"""
from __future__ import annotations

from rapidfuzz import fuzz, process  # type: ignore[import]

from helper_functions.logger_config import logger

NBA = [
    "Atlanta Hawks", "Boston Celtics", "Brooklyn Nets", "Charlotte Hornets", "Chicago Bulls",
    "Cleveland Cavaliers", "Dallas Mavericks", "Denver Nuggets", "Detroit Pistons", "Golden State Warriors",
    "Houston Rockets", "Indiana Pacers", "LA Clippers", "Los Angeles Lakers", "Memphis Grizzlies",
    "Miami Heat", "Milwaukee Bucks", "Minnesota Timberwolves", "New Orleans Pelicans", "New York Knicks",
    "Oklahoma City Thunder", "Orlando Magic", "Philadelphia 76ers", "Phoenix Suns", "Portland Trail Blazers",
    "Sacramento Kings", "San Antonio Spurs", "Toronto Raptors", "Utah Jazz", "Washington Wizards",
]

MLB = [
"Arizona Diamondbacks", "Athletics", "Atlanta Braves", "Baltimore Orioles", "Boston Red Sox", "Chicago Cubs",
"Chicago White Sox", "Cincinnati Reds", "Cleveland Guardians", "Colorado Rockies", "Detroit Tigers", "Houston Astros",
"Kansas City Royals", "Los Angeles Angels", "Los Angeles Dodgers", "Miami Marlins", "Milwaukee Brewers",
"Minnesota Twins", "New York Mets", "New York Yankees", "Philadelphia Phillies", "Pittsburgh Pirates",
"San Diego Padres", "San Francisco Giants", "Seattle Mariners", "St. Louis Cardinals", "Tampa Bay Rays",
"Texas Rangers", "Toronto Blue Jays", "Washington Nationals",
]

NFL = [
    "Arizona Cardinals", "Atlanta Falcons", "Baltimore Ravens", "Buffalo Bills", "Carolina Panthers",
    "Chicago Bears", "Cincinnati Bengals", "Cleveland Browns", "Dallas Cowboys", "Denver Broncos",
    "Detroit Lions", "Green Bay Packers", "Houston Texans", "Indianapolis Colts", "Jacksonville Jaguars",
    "Kansas City Chiefs", "Las Vegas Raiders", "Los Angeles Chargers", "Los Angeles Rams", "Miami Dolphins",
    "Minnesota Vikings", "New England Patriots", "New Orleans Saints", "New York Giants", "New York Jets",
    "Philadelphia Eagles", "Pittsburgh Steelers", "San Francisco 49ers", "Seattle Seahawks", "Tampa Bay Buccaneers",
    "Tennessee Titans", "Washington Commanders",
]

NHL = [
"Anaheim Ducks", "Boston Bruins", "Buffalo Sabres", "Calgary Flames", "Carolina Hurricanes", "Chicago Blackhawks",
"Colorado Avalanche", "Columbus Blue Jackets", "Dallas Stars", "Detroit Red Wings", "Edmonton Oilers",
"Florida Panthers", "Los Angeles Kings", "Minnesota Wild", "Montreal Canadiens", "Nashville Predators",
"New Jersey Devils", "New York Islanders", "New York Rangers", "Ottawa Senators", "Philadelphia Flyers",
"Pittsburgh Penguins", "San Jose Sharks", "Seattle Kraken", "St. Louis Blues", "Tampa Bay Lightning",
"Toronto Maple Leafs", "Utah Mammoth", "Vancouver Canucks", "Vegas Golden Knights", "Washington Capitals",
"Winnipeg Jets",
]

ALL_TEAMS = {
    "NBA": NBA,
    "MLB": MLB,
    "NFL": NFL,
    "NHL": NHL,
}

#################
# MLB Divisions #
#################
# American League:
MLB_AL_EAST = [
"Baltimore Orioles", "Boston Red Sox", "New York Yankees", "Toronto Blue Jays",
]
MLB_AL_CENTRAL = [
"Chicago White Sox", "Cleveland Guardians", "Detroit Tigers", "Kansas City Royals",
]
MLB_AL_WEST = [
"Houston Astros", "Los Angeles Angels", "Seattle Mariners", "Texas Rangers",
]
# National League:
MLB_NL_EAST = [
"Atlanta Braves", "Miami Marlins", "New York Mets", "Washington Nationals",
]
MLB_NL_CENTRAL = [
"Chicago Cubs", "Cincinnati Reds", "Milwaukee Brewers", "St. Louis Cardinals",
]
MLB_NL_WEST = [
"Arizona Diamondbacks", "Colorado Rockies", "Los Angeles Dodgers", "San Francisco Giants",
]

#################
# NFL Divisions #
#################
NFL_AFC_EAST = ["Buffalo Bills", "Miami Dolphins", "New England Patriots", "New York Jets"]
NFL_AFC_NORTH = ["Cincinnati Bengals", "Cleveland Browns", "Baltimore Ravens", "Pittsburgh Steelers"]
NFL_AFC_SOUTH = ["Indianapolis Colts", "Jacksonville Jaguars", "Houston Texans", "Tennessee Titans"]
NFL_AFC_WEST = ["Denver Broncos", "Kansas City Chiefs", "Las Vegas Raiders", "Los Angeles Chargers"]
NFL_NFC_EAST = ["Dallas Cowboys", "New York Giants", "Philadelphia Eagles", "Washington Commanders"]
NFL_NFC_NORTH = ["Chicago Bears", "Detroit Lions", "Green Bay Packers", "Minnesota Vikings"]
NFL_NFC_SOUTH = ["Atlanta Falcons", "Carolina Panthers", "New Orleans Saints", "Tampa Bay Buccaneers"]
NFL_NFC_WEST = ["Arizona Cardinals", "Los Angeles Rams", "San Francisco 49ers", "Seattle Seahawks"]

#################
# NBA Divisions #
#################
# Eastern Conference:
NBA_ATLANTIC_DIVISION = ["Boston Celtics", "Brooklyn Nets", "New York Knicks", "Philadelphia 76ers", "Toronto Raptors"]
NBA_CENTRAL_DIVISION = ["Chicago Bulls", "Cleveland Cavaliers", "Detroit Pistons", "Indiana Pacers", "Milwaukee Bucks"]
NBA_SOUTHEAST_DIVISION = ["Atlanta Hawks", "Charlotte Hornets", "Miami Heat", "Orlando Magic", "Washington Wizards"]
# Western Conference:
NBA_NORTHWEST_DIVISION = ["Denver Nuggets", "Minnesota Timberwolves", "Oklahoma City Thunder", "Portland Trail Blazers",
                      "Utah Jazz"]
NBA_PACIFIC_DIVISION = ["Golden State Warriors", "LA Clippers", "Los Angeles Lakers", "Phoenix Suns",
                        "Sacramento Kings"]
NBA_SOUTHWEST_DIVISION = ["Dallas Mavericks", "Houston Rockets", "Memphis Grizzlies", "New Orleans Pelicans",
                      "San Antonio Spurs"]

#################
# NHL Divisions #
#################
# Eastern Conference:
NHL_ATLANTIC_DIVISION = [
"Boston Bruins", "Buffalo Sabres", "Detroit Red Wings", "Florida Panthers", "Montréal Canadiens", "Ottawa Senators",
"Tampa Bay Lightning",
]
NHL_METROPOLITAN_DIVISION = [
"Carolina Hurricanes", "Columbus Blue Jackets", "New Jersey Devils", "New York Islanders", "New York Rangers",
"Philadelphia Flyers", "Pittsburgh Penguins",
]
# Western Conference:
NHL_CENTRAL_DIVISION = [
"Chicago Blackhawks", "Colorado Avalanche", "Dallas Stars", "Minnesota Wild", "Nashville Predators", "St. Louis Blues",
"Utah Hockey Club",
]
NHL_PACIFIC_DIVISION = [
"Anaheim Ducks", "Calgary Flames", "Edmonton Oilers", "Los Angeles Kings", "San Jose Sharks", "Seattle Kraken",
"Vancouver Canucks",
]

ALL_DIVISIONS = {
    "MLB": ["American League East", "American League Central", "American League West", "National League East",
            "National League Central", "National League West"],
    "NFL": ["AFC East", "AFC North", "AFC South", "AFC West", "NFC East", "NFC North", "NFC South", "NFC West"],
    "NBA": ["Atlantic Division", "Central Division", "Southeast Division", "Northwest Division", "Pacific Division",
            "Southwest Division"],
    "NHL": ["Atlantic Division", "Metropolitan Division", "Central Division", "Pacific Division"],
}

DIVISION_TEAMS = {
    "MLB American League East": MLB_AL_EAST,
    "MLB American League Central": MLB_AL_CENTRAL,
    "MLB American League West": MLB_AL_WEST,
    "MLB National League East": MLB_NL_EAST,
    "MLB National League Central": MLB_NL_CENTRAL,
    "MLB National League West": MLB_NL_WEST,

    "NFL AFC East": NFL_AFC_EAST,
    "NFL AFC North": NFL_AFC_NORTH,
    "NFL AFC South": NFL_AFC_SOUTH,
    "NFL AFC West": NFL_AFC_WEST,
    "NFL NFC East": NFL_NFC_EAST,
    "NFL NFC North": NFL_NFC_NORTH,
    "NFL NFC South": NFL_NFC_SOUTH,
    "NFL NFC West": NFL_NFC_WEST,

    "NHL Atlantic Division": NHL_ATLANTIC_DIVISION,
    "NHL Central Division": NHL_CENTRAL_DIVISION,
    "NHL Pacific Division": NHL_PACIFIC_DIVISION,
    "NHL Metropolitan Division": NHL_METROPOLITAN_DIVISION,

    "NBA Southeast Division": NBA_SOUTHEAST_DIVISION,
    "NBA Northwest Division": NBA_NORTHWEST_DIVISION,
    "NBA Southwest Division": NBA_SOUTHWEST_DIVISION,
    "NBA Pacific Division": NBA_PACIFIC_DIVISION,
    "NBA Central Division": NBA_CENTRAL_DIVISION,
    "NBA Atlantic Division": NBA_ATLANTIC_DIVISION,
}

def get_team_league(team_name: str) -> tuple:
    """Get the league and sport name for a given team name.

    :param team_name: The name of the team to search for.

    :return: A tuple containing the league and sport name.
    """
    team_name_capitalized = team_name.strip().upper()
    best_match = ("", 0.0, "Unknown")

    # Find what array team name is in to determine league
    for league, teams in ALL_TEAMS.items():
        upper_teams = [team.upper() for team in teams]
        matched = process.extractOne(team_name_capitalized, upper_teams, scorer=fuzz.WRatio)

        if matched is None:
            continue  # no matches in this league, skip

        _, score, index = matched
        if score > best_match[1]:
            best_match = (teams[index], score, league)

    logger.info(
        "Team Name: %s Best Match: %s, Score: %s, League: %s",
        team_name, best_match[0], best_match[1], best_match[2],
    )

    if best_match[2].upper() == "NFL":
        matched_team = (best_match[2], "football")
    elif best_match[2].upper() == "MLB":
        matched_team = (best_match[2], "baseball")
    elif best_match[2].upper() == "NHL":
        matched_team = (best_match[2], "hockey")
    elif best_match[2].upper() == "NBA":
        matched_team = (best_match[2], "basketball")

    if best_match[1] >= 70:
        return matched_team  # return tuple of league and sport name

    # If no match found, raise an error
    msg = f"Team '{team_name}' not found in any league."
    raise ValueError(msg)


# Get Team league and sport name, needed for various functions later in script
def append_team_array(teams: list) -> None:
    """Get the team league and sport name from the team list.

    :param teams: List of teams
    """
    for i in range(len(teams)):
        league, sports_name = get_team_league(teams[i][0])  # Get the team league and sport name
        teams[i].append(league)  # Add the league to the teams list
        teams[i].append(sports_name)  # Add the sport name to the teams lists
