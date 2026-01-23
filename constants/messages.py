"""Message strings for UI notifications and multi-word messages.

Organized by:
1. Button labels (UI navigation)
2. Settings layout & configuration
3. Spoiler mode & delay settings
4. Team management
5. Connection & internet
6. Version management
7. Confirmation messages

Simple sport labels (one-word or sport-specific) are inlined where used.
"""

# ============================================================================
# BUTTON LABELS - Used across multiple files for UI navigation
# ============================================================================

# Core action buttons (used in multiple screens)
BUTTON_SAVE = "Save"  # Used in team_selection, reorder_teams, settings, internet layouts
BUTTON_BACK = "Back"  # Used in all screens for navigation back
BUTTON_UPDATE = "Update"  # Used in update_name_popup for fetching team names
BUTTON_CONFIRM = "Confirm"  # Used in update_name_popup to confirm changes
BUTTON_CANCEL = "Cancel"  # Used in update_name_popup to cancel operation

# Main menu navigation buttons (main_screen_layout.py)
BUTTON_START = "Start"  # Main menu: start scoreboard display
BUTTON_INSTRUCTIONS = "Instructions"  # Main menu: show instructions
SETTINGS_TITLE = "Settings"  # Main menu: open settings screen
BUTTON_SET_TEAM_ORDER = "Set Team Order"  # Main menu: reorder team display

# Team management buttons (main_screen_layout.py, team_selection_layout.py)
BUTTON_ADD_MLB = "Add MLB team"  # Add teams from MLB
BUTTON_ADD_NHL = "Add NHL team"  # Add teams from NHL
BUTTON_ADD_NBA = "Add NBA team"  # Add teams from NBA
BUTTON_ADD_NFL = "Add NFL team"  # Add teams from NFL
BUTTON_UPDATE_NAMES = "Update Names"  # Fetch latest team name information

# Team reordering buttons (reorder_teams_layout.py)
BUTTON_MOVE_UP = "Move Up"  # Move selected team up in display order
BUTTON_MOVE_DOWN = "Move Down"  # Move selected team down in display order

# Update/restore buttons (main_screen_layout.py)
BUTTON_CHECK_FOR_UPDATE = "Check for Update"  # Check for app updates
BUTTON_RESTORE_FROM_VERSION = "Restore from Version"  # Restore from previous version
BUTTON_CONNECT_TO_INTERNET = "Connect to Internet"  # Manual internet connection attempt

# Return buttons (change_functionality_popup.py)
BUTTON_RETURN_MAIN = "Return to Main Menu"  # Return from settings to main menu
BUTTON_RETURN_SCOREBOARD = "Return to Scoreboard"  # Return to live scoreboard display

# ============================================================================
# SETTINGS LAYOUT & CONFIGURATION - gui_layouts/settings_layout.py
# ============================================================================

# Settings section titles
CHANGE_FUNCTIONALITY = "Change Functionality of Scoreboard:"  # Section header for feature toggles
CHOOSE_WHAT_DISPLAYS = "Choose What Gets Displayed:"  # Section header for display options
CHANGE_SPORT_DISPLAY = "Change What Displays for Specific Sport:"  # Section header for sport-specific settings

# Settings helper/instruction text
DISPLAYED_ALWAYS = "\tDisplayed always if enabled"  # Help text explaining constant display behavior
DISPLAYED_BEFORE = "\tDisplayed only before game starts"  # Help text explaining pre-game display behavior
DISPLAYED_APPLICABLE = "\tDisplayed only if applicable"  # Help text explaining conditional display behavior

# ============================================================================
# SPOILER MODE & DELAY SETTINGS - change_functionality_popup.py
# ============================================================================

# Spoiler mode toggle states
SPOILER_MODE_ON = "No Spoiler Mode: ON"  # Feature enabled: hide game results
SPOILER_MODE_OFF = "No Spoiler Mode: OFF"  # Feature disabled: show all game info

# Delay mode toggle states
DELAY_ON = "Delay: ON"  # Delay enabled: show delayed broadcast
DELAY_OFF = "Delay: OFF"  # Delay disabled: show live feed
DELAY_TURNING_ON = "Turning delay ON"  # Status message when enabling delay
DELAY_TURNING_OFF = "Turning delay OFF"  # Status message when disabling delay
SETTING_DELAY = "Setting delay of"  # Prefix for delay duration setting

# Team rotation settings
STAYING_ON_TEAM = "Staying on current Team"  # Keep displaying selected team
ROTATING_TEAMS = "Rotating Teams every"  # Rotate through teams at interval

# Spoiler mode status messages
NO_SPOILER_ON = "No Spoiler Mode On"  # Status: spoiler mode is active
WILL_NOT_DISPLAY = "Will Not Display Game Info"  # Status: hiding game results
EXITING_SPOILER = "Exiting No Spoiler Mode"  # Status message when exiting spoiler mode
ENTERING_SPOILER = "Entering No Spoiler Mode"  # Status message when entering spoiler mode

# ============================================================================
# TEAM MANAGEMENT - gui_layouts/team_selection_layout.py, update_name_popup.py, screens/main_screen.py
# ============================================================================

# Team name update messages
TEAM_NAMES_UPDATED = "Found New Team Names, Press Confirm to Update"  # Confirm new team names found
NO_NEW_TEAM_NAMES = "No New Team Names Found"  # No name changes detected
FETCH_NEW_TEAM_NAMES = "This will fetch new team names"  # Description of action
ONLY_IF_CHANGED = "Only do this if a team has changed their name"  # Usage instruction
IF_TEAMS_UPDATED = "\nIf Team's are updated logo's will be re-downloaded when starting"  # Info about side effects

# Startup validation
ADD_AT_LEAST_ONE = "Please add at least one team to start"  # Error: no teams selected

# ============================================================================
# CONNECTION & INTERNET - screens/main_screen.py, gui_layouts/internet_connection_layout.py
# ============================================================================

CONNECTED = "Connected!"  # Success: internet connection established
COULD_NOT_CONNECT = "Could not connect"  # Error: connection failed
ALREADY_CONNECTED = "Already connected to internet"  # Info: already online
TRYING_TO_CONNECT = "Trying to Connect..."  # Status: connection attempt in progress

# ============================================================================
# VERSION MANAGEMENT - screens/main_screen.py
# ============================================================================

NO_PREVIOUS_VERSIONS = "No Previous Versions Found"  # No restore points available
SELECT_VERSION_RESTORE = "Select Version to Restore, then press Restore"  # Instruction for restore process
UPDATING = "Updating..."  # Status: update in progress

# ============================================================================
# CONFIRMATION MESSAGES - screens/main_screen.py
# ============================================================================

SETTINGS_SAVED = "Settings saved successfully!"  # Success: settings persist
ORDER_SAVED = "Order Saved Successfully!"  # Success: team order updated

REDOWNLOAD_IMAGES = "Re-downloaded all of the team logos when starting"  # Info: logos refreshed on start
