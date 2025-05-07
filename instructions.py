

help_text = '''
Controls
---------
Escape - Return to main menu.
Up Arrow - Stay on the currently displayed team (only if multiple teams are playing).
Down Arrow - Resume rotating between multiple teams.
Left Arrow - Turn on live data delay, this will put a delay on live data shown. The amount of delay is set in settings.
Right Arrow - Turn off live data delay, this will shown live game info as soon as its available.
Caps Lock - Enter "No Spoiler Mode," hiding scores, records, and game details.
Shift - Exit "No Spoiler Mode," showing scores, records, and game details.


How Data is Displayed
------------------------
- Only displays teams that have upcoming or recent games (not offseason or long gaps).
- Completed games stay visible for 7 days unless new data replaces them (can be changed in settings).
- Prioritizes displaying teams currently playing (Unless changed in settings):
    - One team playing: display only that team.
    - Multiple teams playing: rotate between them.
- Up Arrow stops rotating between team, Down Arrow resumes rotation.
- Caps Lock hides game info in "No Spoiler Mode."


How Data is Collected
------------------------
- Primary source: ESPN API.
- Secondary Source: MLBStats-API (baseball), nba_api (basketball), nhlapi (hockey).
- If only primary source fails:
    - Tries backup APIs based on the sport.
- If only secondary sources fail:
    - Displays basic info from ESPN.
    - Some details (pitch count, bonus status, shots on goal, etc) might be missing.
- If all data fetching fails:
    - Shows a clock until connection/data is restored.


Clock Screen
--------------
- Displays a clock:
    - If data fetching fails.
    - If internet connection is lost.
    - If none of selected teams have data to display.
- Automatically returns displaying team info:
    - Once data fetching is successful.
    - Internet connection is restored.
    - One of selected teams has data to display.
- A message on clock screen will appear telling why clock is displaying.
'''
