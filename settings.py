"""Settings used to tell what to display and variable used in multiple files."""
from typing import Any

#####################################
# Settings for what teams to display
#####################################

teams = [
    ["Detroit Lions"],
    ["Detroit Tigers"],
    ["Pittsburgh Steelers"],
    ["Detroit Red Wings"],
    ["Detroit Pistons"],
]


###############################
# Settings for displaying Text
###############################

FONT = "Helvetica"
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
SIGNATURE_SIZE = 8


#########################################
# Timers for getting and displaying data
#########################################

# Delay in getting live data
LIVE_DATA_DELAY = 0

FETCH_DATA_NOT_PLAYING_TIMER = 180

DISPLAY_NOT_PLAYING_TIMER = 25
DISPLAY_PLAYING_TIMER = 25

HOW_LONG_TO_DISPLAY_TEAM = 7

###################################
# Settings telling what to display
###################################

# MLB
display_last_pitch = True
display_play_description = True
display_bases = True
display_balls_strikes = True
display_hits_errors = True
display_pitcher_batter = True
display_inning = True
display_outs = True

# NBA
display_nba_timeouts = True
display_nba_bonus = True
display_nba_clock = True
display_nba_shooting = True
display_nba_play_by_play = True

# NHL
display_nhl_sog = True
display_nhl_power_play = True
display_nhl_clock = True
display_nhl_play_by_play = True

# NFL
display_nfl_timeouts = True
display_nfl_redzone = True
display_nfl_clock = True
display_nfl_down = True
display_nfl_possession = True

# General
display_records = True
display_venue = True
display_network = True
display_series = True
display_odds = True
display_date_ended = True
always_get_logos = False
prioritize_playing_team = True
prioritize_playoff_championship_image = True
display_playoff_championship_image = True

############################################
# Variables to to keep track of key presses
############################################
no_spoiler_mode = False
stay_on_team = False
delay = False

###########################################################
# Variables used in multiple files (avoid circular import)
###########################################################
saved_data: Any = {}
division_checked: bool = False  # Used to check if a division was checked when the screen was opened
