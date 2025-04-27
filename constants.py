'''Change Sizes of all Text, logos sizing here for GUI'''

teams = [
    ["Detroit Lions"],
    ["Detroit Tigers"],
    ["Pittsburgh Steelers"],
    ["Detroit Red Wings"],
    ["Detroit Pistons"]
]


FONT = "Arial"

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
TOP_TXT_SIZE = 80

# Delay in getting live data
LIVE_DATA_DELAY = 0

FETCH_DATA_NOT_PLAYING_TIMER = "0"
FETCH_DATA_PLAYING_TIMER = "0"

DISPLAY_NOT_PLAYING_TIMER = "0"
DISPLAY_PLAYING_TIMER = "0"

###################################
# Settings telling what to display
###################################

# MLB
display_last_pitch = False
display_play_description = False
display_bases = False
display_balls_strikes = False
display_hits_errors = False
display_pitcher_batter = False
display_inning = False
display_outs = False

# NBA
display_nba_timeouts = False
display_nba_bonus = False
display_nba_clock = False
display_nba_shooting = False

# NHL
display_nhl_sog = False
display_nhl_power_play = False
display_nhl_clock = False

# NFL
display_nfl_timeouts = False
display_nfl_redzone = False
display_nfl_clock = False
display_nfl_down = False
display_nfl_possession = False

# General
display_records = False
display_venue = False
display_network = False
display_series = False
display_odds = False

no_spoiler_mode = False
stay_on_team = False
