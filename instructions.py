

help_text = """
Controls
---------
Escape - Return to main menu.
Caps Lock - Stay on the currently displayed team (only if multiple teams are playing).
Shift - Resume rotating between multiple teams.
Right Arrow - Turn on live data delay, this will put a delay on live data shown.
              The amount of delay is set in settings.
Left Arrow - Turn off live data delay, this will shown live game info as
             soon as its available.
Up Arrow - Enter "No Spoiler Mode," hiding scores, records, and game details.
Down Arrow - Exit "No Spoiler Mode," showing scores, records, and game details.


How Data is Displayed
------------------------
- Only displays teams that have upcoming or recent games (not offseason or long gaps).
- Completed games stay visible for 7 days unless new data replaces them (can be changed in settings).
- Prioritizes displaying teams currently playing (Unless changed in settings):
    - One team playing: display only that team.
    - Multiple teams playing: rotate between them.
        - Pressing Up Arrow on keyboard stops rotating between team, pressing
          Down Arrow resumes rotation.
- Pressing Caps Lock hides game info in "No Spoiler Mode."


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
- Logos are gotten when first running for the first time
    - If you need to re-download logos such as if a team has updated their logo you
      can re-download logos by selecting ""Always Get Logos when Starting" in settings.


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
"""
