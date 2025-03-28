'''Change Sizes of all Text, logos and Spacing here for GUI'''

# The team names you want to follow, *MUST MATCH* in order -> [team name, sport league, sport name]
# If you add a new league then you will have to delete the sports_logo folder and then the next time it runs
# the logos will be re-downloaded
teams = [
    ["Detroit Lions", "nfl", "football"],
    ["Detroit Tigers", "mlb", "baseball"],
    ["Pittsburgh Steelers", "nfl", "football"],
    ["Detroit Red Wings", "nhl", "hockey"],
    ["Detroit Pistons", "nba", "basketball"]
]


FONT = "Calibri"

# Text Sizes
SCORE_TXT_SIZE = 150
INFO_TXT_SIZE = 90
RECORD_TXT_SIZE = 96
CLOCK_TXT_SIZE = 204
HYPHEN_SIZE = 84
TIMEOUT_SIZE = 34
NBA_TOP_INFO_SIZE = 56
MLB_BOTTOM_INFO_SIZE = 80
PLAYING_TOP_INFO_SIZE = 76
NOT_PLAYING_TOP_INFO_SIZE = 46
SPACE_ONE_CHARACTER_TAKES_UP = 6
TOP_TXT_SIZE = 80

# Display Spacing
COLUMN_WIDTH = 850  # Width should split the screen in threes
COLUMN_HEIGHT = 980
CHARACTERS_FIT_ON_SCREEN = 38
SPACE_BETWEEN_SCORE_AND_NETWORK_LOGO = 50
SPACE_BETWEEN_TOP_TXT_AND_SCORE = 100
SPACE_BETWEEN_TOP_AND_LOGOS = 0
INFO_SPACE_HEIGHT = 200

# Logo Sizes, times amount to decrease size, 1 is the original size
TEAM_LOGO_SIZE = 1.5
NETWORK_LOGOS_SIZE = 1
BASES_SIZE = 3

# Network Logo File Locations
network_logos = {
    "ABC": "Networks/ABC.png",
    "CBS": "Networks/CBS.png",
    "ESPN": "Networks/ESPN.png",
    "FOX": "Networks/FOX.png",
    "MLB": "Networks/MLB_Network.png",
    "NBC": "Networks/NBC.png",
    "Prime": "Networks/Prime.png",
    "TNT": "Networks/TNT.png",
    "NBA": "Networks/NBA_League.png",
    "NFL": "Networks/NFL_NET.png",
    "NHL": "Networks/NHL_Network.png",
    "Netflix": "Networks/Netflix.png",
}
