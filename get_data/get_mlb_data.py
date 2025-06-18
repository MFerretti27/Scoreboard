"""Get MLB from MLB specific API."""
from datetime import UTC, datetime, timedelta
from pathlib import Path

import requests
import statsapi  # type: ignore

import settings
from helper_functions.data_helpers import check_playing_each_other

from .get_game_type import get_game_type
from .get_series_data import get_current_series_mlb
from .get_team_id import get_mlb_team_id

# What things to get from MLBStats API
API_FIELDS = (
    "gameData,game,datetime,dateTime,officialDate,status,detailedState,abstractGameState,teams,home,away,"
    "teamName,record,wins,losses,fullName,liveData,plays,currentPlay,result,playEvents,isPitch,runs,"
    "details,type,code,description,linescore,outs,balls,strikes,inningState,currentInningOrdinal,defense,"
    "offense,batter,inHole,onDeck,first,second,third,pitcher,wins,hits,errors,pitching,currentInning"
)


def get_all_mlb_data(team_name: str, double_header: int = 0) -> tuple[dict[str, str], bool, bool]:
    """Get all information for MLB team.

    Call this if ESPN fails to get MLB data as backup.

    :param team_name: The team name to get information for
    :param double_header: If team has double header, defaults to 0 (no)

    :return team_info: dictionary containing team information to display
    """
    team_info: dict[str, str] = {}
    has_data = False
    currently_playing = False

    # Try to get first game from now for the next 3 days
    today = datetime.now(UTC).strftime("%Y-%m-%d")
    three_days_later = (datetime.now(UTC) + timedelta(days=3)).strftime("%Y-%m-%d")
    try:
        data = statsapi.schedule(
            team=get_mlb_team_id(team_name), include_series_status=True, start_date=today, end_date=three_days_later,
        )
        live = statsapi.get("game", {"gamePk": data[double_header]["game_id"], "fields": API_FIELDS})

        live_feed = requests.get(f"https://statsapi.mlb.com/api/v1.1/game/{data[0]["game_id"]}/feed/live",
                                 timeout=5).json()

    except Exception:
        double_header = 0
        return team_info, has_data, currently_playing  # Could not find game

    has_data = True
    # Cannot Get network so dont display anything, and if game is currently playing it will updated with base images
    team_info["under_score_image"] = ""

    # Get Score
    team_info["home_score"] = live["liveData"]["linescore"]["teams"]["home"].get("runs", 0)
    team_info["away_score"] = live["liveData"]["linescore"]["teams"]["away"].get("runs", 0)

    # Get date and put in local time
    utc_time = datetime.strptime(live["gameData"]["datetime"]["dateTime"], "%Y-%m-%dT%H:%M:%S%z")
    game_time = utc_time.replace(tzinfo=UTC).astimezone().strftime("%-m/%-d - %-I:%M %p")

    # Get venue and set bottom info to display game time and venue
    team_info["bottom_info"] = game_time
    if settings.display_venue:
        venue = live_feed["gameData"]["venue"]["name"]
        team_info["bottom_info"] = f"{game_time} @ {venue}"

    # Get Home and Away team logos/names
    home_team_name = live["gameData"]["teams"]["home"]["teamName"]
    away_team_name = live["gameData"]["teams"]["away"]["teamName"]
    team_info["above_score_txt"] = f"{away_team_name} @ {home_team_name}"

    # Check if two of your teams are playing each other to not display same data twice
    full_home_team_name = live_feed["gameData"]["teams"]["home"]["franchiseName"] + " " + home_team_name
    full_away_team_name = live_feed["gameData"]["teams"]["away"]["franchiseName"] + " " + away_team_name
    if check_playing_each_other(full_home_team_name, full_away_team_name):
        team_has_data = False
        return team_info, team_has_data, currently_playing

    # If team is D-backs change to "ARIZONA DIAMONDBACKS", there is no logo file called D-backs
    home_team_name.replace("D-backs", "ARIZONA DIAMONDBACKS")
    away_team_name.replace("D-backs", "ARIZONA DIAMONDBACKS")

    folder_path = Path.cwd() / "images" / "sport_logos" / "MLB"
    file_names = [f for f in Path(folder_path).iterdir() if Path.is_file(Path.cwd() / folder_path / f)]
    for file in file_names:
        filename = file.name.upper()
        if home_team_name.upper() in filename:
            home_team = filename
        if away_team_name.upper() in filename:
            away_team = filename

    team_info["away_logo"] = Path.cwd() / "images" / "sport_logos" / "MLB" / away_team
    team_info["home_logo"] = Path.cwd() / "images" / "sport_logos" / "MLB" / home_team

    # Get Home and Away team records
    if settings.display_records:
        home_wins = live["gameData"]["teams"]["home"]["record"]["wins"]
        home_losses = live["gameData"]["teams"]["home"]["record"]["losses"]
        team_info["home_record"] = f"{home_wins!s}-{home_losses!s}"

        away_wins = live["gameData"]["teams"]["away"]["record"]["wins"]
        away_losses = live["gameData"]["teams"]["away"]["record"]["losses"]
        team_info["away_record"] = f"{away_wins!s}-{away_losses!s}"

    # Check if game is currently playing
    if "Progress" in live["gameData"]["status"]["detailedState"]:
        currently_playing = True
        team_info = append_mlb_data(team_info, team_name)

    # Check if game is over
    elif "Final" in live["gameData"]["status"]["detailedState"]:
        team_info["top_info"] = get_current_series_mlb(team_name)
        team_info["bottom_info"] = live["gameData"]["status"]["detailedState"].upper()

        # Once game is over check if its a double header but ensure second game does't call this
        if live["gameData"]["game"]["doubleHeader"] not in ["N", "S"]and double_header !=1:
            team_info = get_all_mlb_data(team_name, double_header=1)

    # Game has not been played yet but scheduled
    else:

        # Check if postponed or delayed
        scheduled = statsapi.get(
            "schedule", {"gamePk": data[0]["game_id"],
                         "sportId": 1,
                         "fields": "dates,date,games,status,detailedState,abstractGameState,reason"},
            )
        if scheduled["dates"][0]["games"][0]["status"]["detailedState"] in ["Postponed", "Delayed", "Canceled"]:
            sate_of_game = scheduled["dates"][0]["games"][0]["status"]["detailedState"]
            reason_for_state = scheduled["dates"][0]["games"][0]["status"]["reason"]
            team_info["bottom_info"] = sate_of_game + " due to " + reason_for_state

    # Check if game is a championship game, if so display its championship game
    if get_game_type("MLB", team_name) != "":
        # If str returned is not empty, then its world series/conference championship, so display championship png
        team_info["under_score_image"] = get_game_type("MLB", team_name)

    return team_info, has_data, currently_playing


def append_mlb_data(team_info: dict, team_name: str) -> dict:
    """Get information for MLB team if playing.

    :param team_info: Dictionary where data is stored to display
    :param team_name: The team name to get information for

    :return team_info: dictionary containing team information to display
    """
    data = statsapi.schedule(team=get_mlb_team_id(team=team_name), include_series_status=True)
    live = statsapi.get("game", {"gamePk": data[0]["game_id"], "fields": API_FIELDS})

    # Get Scores
    team_info["home_score"] = str(live["liveData"]["linescore"]["teams"]["home"]["runs"])
    team_info["away_score"] = str(live["liveData"]["linescore"]["teams"]["away"]["runs"])

    # Get hits and error to display under score
    if settings.display_hits_errors:
        home_hits = live["liveData"]["linescore"]["teams"]["home"].get("hits", 0)
        away_hits = live["liveData"]["linescore"]["teams"]["away"].get("hits", 0)
        home_errors = live["liveData"]["linescore"]["teams"]["home"].get("errors", 0)
        away_errors = live["liveData"]["linescore"]["teams"]["away"].get("errors", 0)
        team_info["away_timeouts"] = (f"Hits: {away_hits} Errors: {away_errors}")
        team_info["home_timeouts"] = (f"Hits: {home_hits} Errors: {home_errors}")

    # Get inning
    if settings.display_inning:
        inning_state = live["liveData"]["linescore"].get("inningState", "Top")
        inning_number = live["liveData"]["linescore"].get("currentInningOrdinal", 0)
        team_info["above_score_txt"] = inning_state + " " + str(inning_number)

    # Get pitcher and batter for bottom info
    if settings.display_pitcher_batter:
        batter_full_name = live["liveData"]["linescore"]["offense"]["batter"]["fullName"]
        batter_last_name = " ".join(batter_full_name.split()[1:])  # Remove First Name
        pitcher_full_name = live["liveData"]["linescore"]["defense"]["pitcher"]["fullName"]
        pitcher_last_name = " ".join(pitcher_full_name.split()[1:])  # Remove First Name

        team_info["bottom_info"] = ""
        if pitcher_last_name != "":
            team_info["bottom_info"] += (f"P: {pitcher_last_name}   ")
        if batter_last_name != "":
            team_info["bottom_info"] += (f"AB: {batter_last_name}")

    team_info["top_info"] = ""
    # If inning is changing do not display count and move inning to display below score
    if "Mid" not in team_info["above_score_txt"] and "End" not in team_info["above_score_txt"]:
        try:
            pitch = live["liveData"]["plays"].get("currentPlay", {}).get("playEvents", [{}])[-1]
            if pitch.get("isPitch", True) and settings.display_last_pitch:
                team_info["top_info"] += pitch["details"]["type"]["description"].replace("Four-Seam", "") + "  "

            play = live["liveData"]["plays"].get("currentPlay", {}).get("result", {}).get("description", "")
            if play and settings.display_play_description:
                team_info["bottom_info"] = play
        except Exception:
            print("couldn't get Pitch or play")

        if settings.display_balls_strikes:
            balls = live["liveData"]["linescore"].get("balls", 0)
            strikes = live["liveData"]["linescore"].get("strikes", 0)
            outs = live["liveData"]["linescore"].get("outs", 0)
            team_info["top_info"] += (f"{balls}-{strikes}, {outs} Outs")
    else:
        # If it is the Middle or End of inning show who is leading off batting
        if settings.display_pitcher_batter:
            team_info["bottom_info"] = (f"DueUp: {batter_full_name}")
        team_info["top_info"] = ""

    if settings.display_bases:
        bases = {"first": False, "second": False, "third": False}  # Dictionary to store info of occupied bases

        for key in bases:
            try:
                # Dont need to store name of whose on just has to ensure call is successful
                _ = live["liveData"]["linescore"]["offense"][key]["fullName"]
                bases[key] = True  # If call is successful someone is on that base
            except KeyError:
                bases[key] = False  # If call fails no one is on that base

        # Get which image to display based on what base is occupied
        base_conditions = {
            (True, False, False): "on_first.png",
            (False, True, False): "on_second.png",
            (False, False, True): "on_third.png",
            (True, False, True): "on_first_third.png",
            (True, True, False): "on_first_second.png",
            (False, True, True): "on_second_third.png",
            (True, True, True): "on_first_second_third.png",
            (False, False, False): "empty_bases.png",
        }

        # Get image location for representing runners on base
        base_image = base_conditions[(bases["first"], bases["second"], bases["third"])]
        team_info["under_score_image"] = f"images/baseball_base_images/{base_image}"

        if "Status Change" in team_info["bottom_info"]:
            team_info["bottom_info"] = "Game Starting"

    return team_info
