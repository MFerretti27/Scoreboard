

help_text = '''
Controls
---------
Escape - Return to main menu.
Up Arrow - Stay on the currently displayed team (only if multiple teams are playing).
Down Arrow - Resume rotating between multiple teams.
Caps Lock - Enter "No Spoiler Mode," hiding scores, records, and game details.
Shift - Exit "No Spoiler Mode," showing scores, records, and game details.

How Data is Displayed
------------------------
- Only displays teams that have upcoming or recent games (not offseason or long gaps).
- Completed games stay visible for up to 3 days unless new data replaces them.
- Priority to teams currently playing:
    - One team playing: display only that team.
    - Multiple teams playing: rotate between them.
- Up Arrow stops rotating (freeze), Down Arrow resumes rotation.
- Caps Lock hides game info in "No Spoiler Mode."

How Data is Collected
------------------------
- Primary source: ESPN API.
- Backup APIs: MLBStats-API (baseball), nba_api (basketball), nhlapi (hockey).
- If ESPN fails:
    - Tries backup APIs based on the sport.
- If backups fail:
    - Displays basic info from ESPN.
    - Some details (pitch count, bonus status, shots on goal, etc) might be missing.
- If all data fetching fails:
    - Shows a clock until connection/data is restored.

Clock Screen
--------------
- Displays a clock if data fetching fails or if internet connection is lost.
- Automatically returns to team info once data or connection is restored.
'''
