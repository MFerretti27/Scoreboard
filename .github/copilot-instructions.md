<!-- Copilot / AI agent instructions for the Scoreboard project -->
# Quick orientation

This repository is a Python-based scoreboard app. Key runtime pieces:
- Entrypoint: `main.py` (creates venv, installs dependencies, starts UI)
- Central config: `settings.py` (team list, display timers, feature flags)
- Data fetch layer: `get_data/` (sport-specific fetchers; primary entry `get_data/get_espn_data.py`)
- UI layout & controllers: `gui_layouts/` and `screens/` (visual elements and runtime display loops)
- Helpers: `helper_functions/` (logging, scoreboard logic, connection checks)

Work quickly by reading these files first: `main.py`, `settings.py`, `get_data/get_espn_data.py`,
`screens/currently_playing_screen.py`, and `helper_functions/scoreboard_helpers.py`.

## Primary concepts an AI agent must know

- Teams are defined in `settings.teams` as a list of lists (e.g. [team_name, league]). Many screens
  iterate that list to fetch and display data.
- Data flow: screen controller -> call into `get_data` -> returns (info, data_available, currently_playing).
  Example: see `screens/currently_playing_screen.py:get_display_data()` which coordinates fetch timing,
  delay buffering (saved_data), and returns the team_info list used by `team_currently_playing()`.
- Live-delay behavior: the code supports an optional delay (flag `settings.delay` and `settings.LIVE_DATA_DELAY`) where
  `saved_data` holds delayed snapshots. See `set_delay_display()` and `get_display_data()`.
- GUI conventions: FreeSimpleGUI element keys are used consistently (e.g. `top_info`, `home_score`, `away_score`,
  `above_score_txt`, `under_score_image`). `screens/*` call `update_display()` which maps team_info dict keys
  to window element updates.
- Naming patterns: team data keys commonly start with `home_` or `away_`. Sport-specific flags include
  `home_bonus`, `home_power_play`, `home_redzone`, `home_possession`.

## Run / dev workflow (discovered from README and files)

1. Create environment & install deps: the project automates this when running `python main.py` (it creates a venv
   and installs `requirements.txt`). You can also manually run `pip install -r requirements.txt` in the venv.
2. Launch UI: `python main.py` (main menu appears; add teams in the UI then press Start).
3. Logging: use `helper_functions/logger_config.py` — runtime debug statements call `logger.info()` and `logger.debug()`.

Notes: pyc files indicate development on Python 3.12. The app targets Raspberry Pi / Linux and macOS/Windows.

## Useful patterns & examples to reference

- Updating display based on sport: `screens/currently_playing_screen.py:update_display()` branches on league
  (NFL/NBA/MLB/NHL) and calls `display_*_info()` helpers to set fonts/colors/timeouts.
- Timing utilities: code uses `adafruit_ticks` (`ticks_ms`, `ticks_add`, `ticks_diff`) for non-blocking timers.
- UI state reset and scrolling: `helper_functions/scoreboard_helpers.py` contains `reset_window_elements()`,
  `scroll()` and `set_spoiler_mode()` used across multiple screens.
- Data fetch fallbacks: README documents ESPN as primary and league-specific APIs as backups (MLB-StatsAPI, nba_api,
  nhl-api-py). See `get_data/` modules for implementation details.

## When editing or generating code for this repo

- Prefer modifying `screens/*` or `helper_functions/*` when changing display behavior — those are the UI/control layers.
- Change feature flags and timing in `settings.py` (e.g. `delay`, `LIVE_DATA_DELAY`, `prioritize_playing_team`,
  `stay_on_team`, `no_spoiler_mode`, `DISPLAY_PLAYING_TIMER`). Tests and code assume these runtime flags exist.
- Use existing logger calls (`logger`) rather than printing. Many code paths rely on `logger.info()` for diagnosis.
- When touching data parsing, update the sport-specific file in `get_data/` and ensure it returns the tuple
  `(info_dict, data_available_bool, currently_playing_bool)` — other modules rely on that contract.

## Quick checklist for PRs / agent actions

- Read `settings.py` to understand default flags and team list.
- If changing UI keys, update all `screens/*` and `gui_layouts/*` where keys are referenced.
- Preserve the `home_` / `away_` naming convention and sport-specific boolean flags.

---

If any section needs more detail (e.g., exact shape of a team_info dict, or where to patch image/logo handling), tell me which area you want expanded and I will update this file.

## Collaborative update workflow (user-driven)

Per your request: on every message you send to the assistant, the agent will analyze repository changes and update this instruction file as needed. The intended lightweight workflow:

- When you send an update, patch, or PR description, the assistant will inspect workspace files referenced in your message and surface a short proposed edit to this document.
- For small, mechanical updates (typos, adding references to newly modified files), the assistant will apply the change directly and report back with a 1-line summary and list of files changed.
- For behavioral or policy changes (new automation, CI updates, breaking interface changes), the assistant will propose edits and wait for your approval before applying them.
- Every change will include a short rationale and, when useful, an example showing the new/changed code locations (e.g., `screens/currently_playing_screen.py`).
- To pause automatic edits, reply with `pause instruction updates`; to switch to review-only mode, reply with `review-only`.

If you'd like this workflow adjusted (more or less automation, commit-message style, or acceptance criteria), tell me how you prefer it and I'll update this section.
