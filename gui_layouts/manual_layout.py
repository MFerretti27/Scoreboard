"""GUI Layout screen for showing instructions in main menu."""
from __future__ import annotations

import FreeSimpleGUI as Sg  # type: ignore[import]

import settings
from constants import colors, messages
from constants.sizing_utils import (
    calculate_button_size,
    calculate_message_size,
    calculate_text_size,
    calculate_title_size,
    get_responsive_scale,
)


def create_instructions_layout(window_width: int) -> list:
    """Create the layout for instructions screen with tabbed interface.

    :param window_width: The width of the screen being used

    :return layout: List of elements and how the should be displayed
    """
    _, scale = get_responsive_scale(window_width)
    title_size = calculate_title_size(scale, base_multiplier=65)
    text_size = calculate_text_size(scale, min_size=18, base_multiplier=22)
    button_size = calculate_button_size(scale, min_size=22, base_multiplier=30)
    instructions_size = calculate_message_size(scale, min_size=10, base_multiplier=20)

    instructions_font = "Consolas"

    # Define content for each tab
    getting_started_tab = [
        [Sg.Multiline(getting_started_text, size=(window_width - 20, instructions_size), disabled=True,
                      no_scrollbar=False, font=(instructions_font, text_size))],
    ]

    settings_tab = [
        [Sg.Multiline(settings_text, size=(window_width - 20, instructions_size), disabled=True,
                      no_scrollbar=False, font=(instructions_font, text_size))],
    ]

    scoreboard_tab = [
        [Sg.Multiline(scoreboard_text, size=(window_width - 20, instructions_size), disabled=True,
                      no_scrollbar=False, font=(instructions_font, text_size))],
    ]

    clock_tab = [
        [Sg.Multiline(clock_text, size=(window_width - 20, instructions_size), disabled=True,
                      no_scrollbar=False, font=(instructions_font, text_size))],
    ]

    data_sources_tab = [
        [Sg.Multiline(data_sources_text, size=(window_width - 20, instructions_size), disabled=True,
                      no_scrollbar=False, font=(instructions_font, text_size))],
    ]

    tips_tab = [
        [Sg.Multiline(tips_text, size=(window_width - 20, instructions_size), disabled=True,
                      no_scrollbar=False, font=(instructions_font, text_size))],
    ]

    # Create tab group
    tab_group = Sg.TabGroup(
        [
            [Sg.Tab("Getting Started", getting_started_tab, font=(settings.FONT, int(18 * scale))),
             Sg.Tab(messages.SETTINGS_TITLE, settings_tab, font=(settings.FONT, int(18 * scale))),
             Sg.Tab("Scoreboard", scoreboard_tab, font=(settings.FONT, int(18 * scale))),
             Sg.Tab("Clock Screen", clock_tab, font=(settings.FONT, int(18 * scale))),
             Sg.Tab("Data Sources", data_sources_tab, font=(settings.FONT, int(18 * scale))),
             Sg.Tab("Tips", tips_tab, font=(settings.FONT, int(18 * scale))),
            ],
        ],
        tab_location="top",
        selected_title_color=colors.TEXT_WHITE,
        selected_background_color=colors.ACCENT_BLUE,
    )

    return [
        [Sg.Text(messages.BUTTON_INSTRUCTIONS, font=(settings.FONT, title_size, "underline"),
                 justification="center", expand_x=True)],
        [tab_group],
        [Sg.VPush()],
        [
            Sg.Push(),
            Sg.Button(messages.BUTTON_BACK, font=(settings.FONT, button_size)),
            Sg.Push(),
        ],
        [Sg.VPush()],
    ]


# Tab content texts
getting_started_text = """
MAIN SCREEN - Getting Started
==============================

Adding Teams:
- Click "Add [LEAGUE]" button (e.g., "Add MLB", "Add NBA", "Add NFL", "Add NHL")
- Select the team(s) you want to follow from the list
- Click "Save" to add them
- Teams will appear in your follow list

Updating Team Names or Logos:
- If a sports team changes their name or logo, go to the team league tab
- Click "Update Names" to fetch the latest team information
- Logos will be automatically re-downloaded on next startup
- You can also enable "Get Logos when Starting" in Settings to force re-download

Team Order:
- Click "Set Team Order" to rearrange the order teams are displayed
- Use "Move Up" and "Move Down" buttons to reorder
- Click "Save" to apply changes

Starting the Scoreboard:
- Click "Start" to begin displaying live game scores
- The app will download team logos and display game information
"""

settings_text = """
SETTINGS - Customize Your Experience
======================================

FUNCTIONALITY SETTINGS:

Display Time (No Games):
- How long (in seconds) to show each team when they're not playing
- Example: 30 seconds means each team without an active game shows for 30 seconds
- Lower value = faster rotation through all teams

Display Timer (LIVE Games):
- How long (in seconds) to show each team when they ARE playing
- Example: 45 seconds means each team with an active game shows for 45 seconds
- Lower value = faster rotation between teams with live games

Live Data Delay:
- Add a delay (in seconds) to game updates
- Useful if watching on delayed broadcast or different timezone
- When enabled, new game info waits before displaying
- Toggle on/off while watching by clicking the score on the scoreboard

Display Time (Completed):
- How long (in days) to keep showing completed games
- Example: 7 days means finished games stay visible for a week

Always Get Logos:
- Re-download team logos on next startup
- Enable if a sports team changed their logo or name
- Logos are normally downloaded once and reused

Prioritize Playing Teams:
- When enabled, shows only teams with active games first
- Teams without games display after all live games are finished
- When disabled, all teams rotate equally regardless of game status

Auto Update:
- Automatically check for and apply app updates
- Updates happen at 4:30 AM when enabled
- You can manually restore to earlier versions from the main screen


WHAT TO DISPLAY:

- Teams Win-Loss Records: Show each team's season record (W-L)
- Game Venue: Display the location/stadium where the game is played
- Gambling Odds: Show betting odds for the game
- Playoff/Championship Image: Display a special badge for playoff/championship games
- Series Information: Show playoff series status (e.g., "2-0" in series)
- Player Stats: Display individual player statistics (click team logos to view)
- Sport-Specific Stats: Shows relevant stats for each sport (power plays for hockey, etc.)
"""

scoreboard_text = """
SCOREBOARD DISPLAY - While Watching Scores
=============================================

Touch/Click Screen Controls:

Score Area (center of screen):
Click the score to toggle through:
  1. Turn on No Spoiler Mode (hides scores and details)
  2. Toggle Live Data Delay on/off (delays updates by time set in Settings)
  3. Return to Main Screen (Escape key also works)

Team Logos (left and right sides):
- Click Home Team Logo (left) or Away Team Logo (right) to see season stats
- Stats display player information and team performance

Home Team Record (left record text):
- Click to rotate to the NEXT team in your follow list
- Only available when multiple teams are playing

Away Team Record (right record text):
- Click to rotate to the PREVIOUS team you were viewing
- Returns you to the last team that was displayed

Bottom of Screen (info bar):
- Click to STAY on the current team being displayed
- Stops the automatic rotation between teams
- Click again to resume automatic rotation


Display Behavior:

Team Rotation (Normal):
- App rotates between your selected teams based on game status
- Teams currently playing are prioritized (can be disabled in Settings)
- Each team displays for a set time (customizable in Settings)
- When you click the bottom info area, rotation pauses on current team

Live Data Updates:
- App fetches fresh game data every few seconds
- By default, shows data immediately
- Use Live Data Delay (click score) to add a delay for live sync with TV broadcast
"""

clock_text = """
CLOCK SCREEN - When It Appears
================================

When does the clock screen appear?

The clock screen will appear if:
1. No data is available from the sports data sources
   (ESPN, MLB Stats, NBA API, NHL API)
2. None of your selected teams have upcoming or recent games
3. Internet connection is lost

Why it happens:
- During off-season when teams don't have games
- If all data sources are temporarily unavailable
- No internet connection to fetch data
- Server maintenance or API issues


Auto-Return to Scores:

The clock will automatically disappear and return to scores when:
- Data becomes available from your selected teams
- Internet connection is restored
- A valid game for one of your teams is found

A message on the clock screen will explain why it's showing:
- "No Internet Connection" = Network is offline
- "Failed to Get Data" = Data sources are down
- "No Teams Have Data" = No active games for your teams
"""

data_sources_text = """
DATA SOURCES & RELIABILITY
============================

How the app gets game information:

Primary Source: ESPN API
- Used for all sports when available
- Most reliable and up-to-date

Backup Sources by Sport:
- Baseball (MLB): MLB Stats API
- Basketball (NBA): NBA API
- Hockey (NHL): NHL API


Fallback Behavior:

If primary source (ESPN) fails:
- Falls back to league-specific backup APIs for detailed game info
- Some specialized stats might be unavailable but basic scores work

If all sources fail:
- Clock screen displays until connection/data is restored
- Message explains what's wrong on the clock screen


Data Update Frequency:

- Game scores update every 3 seconds when games are live
- Data is refreshed automatically in the background
- No manual refresh needed


Connection Handling:

- App automatically retries if connection fails
- Reconnects to WiFi if disconnected
- Updates resume once connection is restored
"""

tips_text = """
KEY TIPS & BEST PRACTICES
==========================

General Usage:

1. Teams are displayed continuously while active games exist
2. Completed games stay visible for 7 days by default (adjustable in Settings)
3. Logos are downloaded once on first startup (re-download available in Settings)
4. All your team selections and settings are saved automatically
5. Settings persist even after app updates


Avoiding Spoilers:

- Use No Spoiler Mode to hide scores and details
- Perfect for watching delayed broadcasts or games from other timezones
- Toggle by clicking the score on the scoreboard
- Settings persist so spoiler mode stays on if you enable it


Synchronizing with TV:

- Live Data Delay helps sync the scoreboard with TV broadcast delays
- Set delay value in seconds to match your TV broadcast delay
- Common delays: 30-120 seconds depending on your broadcast provider
- Toggle delay on/off by clicking the score


Customizing Display:

- Adjust display times in Settings for faster or slower team rotation
- Enable "Prioritize Playing Teams" to focus on live games
- Toggle individual stat displays (records, odds, venue, etc.)
- Rearrange team order from the main screen


During Off-Season:

- Clock screen displays when no teams have games
- This is normal during off-season periods
- Clock updates once games resume
- Use this time to update team logos if names changed


Troubleshooting:

- If clock screen appears, check your internet connection
- Verify your selected teams are in active season
- Try updating team information if names changed
- Contact support if issues persist
"""
