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
INFO_TXT_SIZE = 96
RECORD_TXT_SIZE = 96
CLOCK_TXT_SIZE = 204
HYPHEN_SIZE = 84
TIMEOUT_SIZE = 34
NBA_TOP_INFO_SIZE = 56
PLAYING_TOP_INFO_SIZE = 76
NOT_PLAYING_TOP_INFO_SIZE = 46

# Display Spacing
COLUMN_WIDTH = 800
COLUMN_HIGHT = 1000
CHARACTERS_FIT_ON_SCREEN = 36
SPACE_BETWEEN_SCORE_AND_NETWORK_LOGO = 75
SPACE_BETWEEN_TOP_AND_SCORE = 250
SPACE_BETWEEN_TOP_AND_LOGOS = 0

# Logo Sizes
TEAM_LOGO_SIZE = 1.5
NETWORK_LOGOS_SIZE = 1

network_logos = {
    "ABC": ["Networks/ABC.png", 5],
    "CBS": ["Networks/CBS.png", 1],
    "ESPN": ["Networks/ESPN.png", 5],
    "FOX": ["Networks/FOX.png", 2],
    "MLB": ["Networks/MLB_Network.png", 3],
    "NBC": ["Networks/NBC.png", 8],
    "Prime": ["Networks/Prime.png", 10],
    "TNT": ["Networks/TNT.png", 7],
    # "NBA TV": ["Networks/NBA_TV.png", 5],
    "NBA": ["Networks/NBA_League.png", 1],
    "NFL": ["Networks/NFL_NET.png", 2],
}