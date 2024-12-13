'''Change Sizes of all Text, logos and Spacing here for GUI'''

# The team names you want to follow, *must match* in order -> [team name, sport league, sport name]
# If you change teams you want to be displayed or change the order of the teams displayed then 
# you will have to delete the sports_logo folder and on the next run it will re-download all the logos
teams = [
    ["Detroit Lions", "nfl", "football"],
    ["Detroit Tigers", "mlb", "baseball"],
    ["Pittsburgh Steelers", "nfl", "football"],
    ["Detroit Red Wings", "nhl", "hockey"],
    ["Detroit Pistons", "nba", "basketball"]
]


FONT = "Calibri"

# Text Sizes
SCORE_TXT_SIZE = 140
INFO_TXT_SIZE = 90
RECORD_TXT_SIZE = 96
CLOCK_TXT_SIZE = 204
HYPHEN_SIZE = 84
TIMEOUT_SIZE = 34
NBA_TOP_INFO_SIZE = 56
PLAYING_TOP_INFO_SIZE = 76
NOT_PLAYING_TOP_INFO_SIZE = 46
SPACE_ONE_CHARACTER_TAKES_UP = 6

# Display Spacing
COLUMN_WIDTH = 850 # Width should split the screen in threes
COLUMN_HIGHT = 980
CHARACTERS_FIT_ON_SCREEN = 38
SPACE_BETWEEN_SCORE_AND_NETWORK_LOGO = 50
SPACE_BETWEEN_TOP_AND_SCORE = 350
SPACE_BETWEEN_TOP_AND_LOGOS = 0
INFO_SPACE_HEIGHT = 200

# Logo Sizes
TEAM_LOGO_SIZE = 1.5
NETWORK_LOGOS_SIZE = 1

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
}