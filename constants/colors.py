"""Color constants for UI styling."""

# === Semantic Color Names ===
# These provide context-specific naming for better code clarity

# Status/Feedback colors
# Used for: error messages, validation failures, warnings
ERROR_RED = "red"

# Used for: success messages, confirmations, positive feedback
SUCCESS_GREEN = "green"

# Used for: neutral/informational text, default messages
NEUTRAL_BLACK = "black"

# Used for: informational text on dark backgrounds
INFO_WHITE = "white"

# Sports-specific indicator colors
# Used for: NFL redzone indicator, signature field highlighting
SPORTS_RED = "red"

# Used for: hockey/basketball power play indicator
POWER_PLAY_BLUE = "blue"

# Used for: basketball bonus indicator
BONUS_ORANGE = "orange"

# Used for: timeout indicators in sports display
TIMEOUT_YELLOW = "yellow"

# UI element colors
# Used for: backgrounds, borders, and layout elements
BACKGROUND_BLACK = "black"
TEXT_WHITE = "white"
ACCENT_BLUE = "blue"



# === Button Color Tuples ===
# Button color tuples (text, background)
# Used in: screens/main_screen.py (update and restore buttons)
BUTTON_SUCCESS = ("white", "green")
BUTTON_ERROR = ("white", "red")

# Common aliases for backward compatibility
BUTTON_GREEN = BUTTON_SUCCESS
BUTTON_RED = BUTTON_ERROR

# === Progress Bar Colors ===
# Progress bar colors (bar, background)
# Used in: gui_layouts/main_screen_layout.py
PROGRESS_GREEN_WHITE = ("green", "white")

# === Theme Names ===
# Used in: gui_layouts/main_screen_layout.py, gui_layouts/change_functionality_popup.py
THEME_LIGHT_BLUE = "LightBlue6"

# Used in: gui_layouts/scoreboard_layout.py
THEME_BLACK = "black"
