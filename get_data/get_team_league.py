'''This function uses the RapidFuzz library to find the best match for the team name.
It compares the input team name with a list of known team names in various leagues (NBA, MLB, NFL, NHL).
The function returns a tuple containing the league and sport name if a match is found with a score of 70 or higher.
'''

from rapidfuzz import process, fuzz

NBA = [
    "Atlanta Hawks", "Boston Celtics", "Brooklyn Nets", "Charlotte Hornets", "Chicago Bulls",
    "Cleveland Cavaliers", "Dallas Mavericks", "Denver Nuggets", "Detroit Pistons", "Golden State Warriors",
    "Houston Rockets", "Indiana Pacers", "LA Clippers", "Los Angeles Lakers", "Memphis Grizzlies",
    "Miami Heat", "Milwaukee Bucks", "Minnesota Timberwolves", "New Orleans Pelicans", "New York Knicks",
    "Oklahoma City Thunder", "Orlando Magic", "Philadelphia 76ers", "Phoenix Suns", "Portland Trail Blazers",
    "Sacramento Kings", "San Antonio Spurs", "Toronto Raptors", "Utah Jazz", "Washington Wizards"
]

MLB = [
    "Arizona Diamondbacks", "Atlanta Braves", "Baltimore Orioles", "Boston Red Sox", "Chicago White Sox",
    "Chicago Cubs", "Cincinnati Reds", "Cleveland Guardians", "Colorado Rockies", "Detroit Tigers",
    "Houston Astros", "Kansas City Royals", "Los Angeles Angels", "Los Angeles Dodgers", "Miami Marlins",
    "Milwaukee Brewers", "Minnesota Twins", "New York Yankees", "New York Mets", "Oakland Athletics",
    "Philadelphia Phillies", "Pittsburgh Pirates", "San Diego Padres", "San Francisco Giants", "Seattle Mariners",
    "St. Louis Cardinals", "Tampa Bay Rays", "Texas Rangers", "Toronto Blue Jays", "Washington Nationals"
]

NFL = [
    "Arizona Cardinals", "Atlanta Falcons", "Baltimore Ravens", "Buffalo Bills", "Carolina Panthers",
    "Chicago Bears", "Cincinnati Bengals", "Cleveland Browns", "Dallas Cowboys", "Denver Broncos",
    "Detroit Lions", "Green Bay Packers", "Houston Texans", "Indianapolis Colts", "Jacksonville Jaguars",
    "Kansas City Chiefs", "Las Vegas Raiders", "Los Angeles Chargers", "Los Angeles Rams", "Miami Dolphins",
    "Minnesota Vikings", "New England Patriots", "New Orleans Saints", "New York Giants", "New York Jets",
    "Philadelphia Eagles", "Pittsburgh Steelers", "San Francisco 49ers", "Seattle Seahawks", "Tampa Bay Buccaneers",
    "Tennessee Titans", "Washington Commanders"
]

NHL = [
    "Anaheim Ducks", "Arizona Coyotes", "Boston Bruins", "Buffalo Sabres", "Calgary Flames",
    "Carolina Hurricanes", "Chicago Blackhawks", "Colorado Avalanche", "Columbus Blue Jackets", "Dallas Stars",
    "Detroit Red Wings", "Edmonton Oilers", "Florida Panthers", "Los Angeles Kings", "Minnesota Wild",
    "Montreal Canadiens", "Nashville Predators", "New Jersey Devils", "New York Islanders", "New York Rangers",
    "Ottawa Senators", "Philadelphia Flyers", "Pittsburgh Penguins", "San Jose Sharks", "Seattle Kraken",
    "St. Louis Blues", "Tampa Bay Lightning", "Toronto Maple Leafs", "Vancouver Canucks", "Vegas Golden Knights",
    "Washington Capitals", "Winnipeg Jets"
]

ALL_TEAMS = {
    "NBA": NBA,
    "MLB": MLB,
    "NFL": NFL,
    "NHL": NHL
}


def get_team_league(team__name: str) -> tuple:
    '''Get the league and sport name for a given team name.

    :param team__name: The name of the team to search for.

    :return: A tuple containing the league and sport name.
    '''
    team__name_capitalized = team__name.strip().upper()
    best_match = ("", 0, "Unknown")

    for league, teams in ALL_TEAMS.items():
        upper_teams = [team.upper() for team in teams]
        _, score, index = process.extractOne(team__name_capitalized, upper_teams, scorer=fuzz.WRatio)
        if score > best_match[1]:
            best_match = (teams[index], score, league)

    print(f"Team Name: {team__name} Best Match: {best_match[0]}, Score: {best_match[1]}, League: {best_match[2]}")

    if best_match[2].upper() == "NFL":
        matched_team = (best_match[2], "football")
    elif best_match[2].upper() == "MLB":
        matched_team = (best_match[2], "baseball")
    elif best_match[2].upper() == "NHL":
        matched_team = (best_match[2], "hockey")
    elif best_match[2].upper() == "NBA":
        matched_team = (best_match[2], "basketball")

    if best_match[1] >= 70:
        return matched_team
    else:
        raise ValueError(f"Team '{team__name}' not found in any league.")


# Get Team league and sport name, needed for various functions later in script
def append_team_array(teams) -> None:
    """Get the team league and sport name from the team list.

    :param teams: List of teams
    """
    for i in range(len(teams)):
        league, sports_name = get_team_league(teams[i][0])  # Get the team league and sport name
        teams[i].append(league)  # Add the league to the teams list
        teams[i].append(sports_name)  # Add the sport name to the teams lists
