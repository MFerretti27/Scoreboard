"""Use ESPN API to Grab Major League Sports Teams logo and Resize to fit screen."""
from __future__ import annotations

import random
import shutil
from pathlib import Path

import FreeSimpleGUI as Sg  # type: ignore[import]
import requests  # type: ignore[import]
from PIL import Image  # type: ignore[import]

import settings
from constants.file_paths import (
    BASEBALL_BASE_IMAGES_DIR,
    CHAMPIONSHIP_IMAGES_DIR,
    CONFERENCE_CHAMPIONSHIP_IMAGES_DIR,
    NETWORKS_DIR,
    PLAYOFF_IMAGES_DIR,
    SPORT_LOGOS_DIR,
)
from get_data.get_team_league import MLB, NBA, NFL, NHL
from helper_functions.logging.logger_config import logger


def new_league_added() -> bool:
    """Check if new league has been added to teams array.

    :return: True if new league added, False otherwise
    """
    folder_names = ([str(name).split("/")[-1] for name in Path(Path.cwd() / "images" / "sport_logos").iterdir()
                     if Path.is_dir(Path.cwd() / "images" / "sport_logos" / name)])

    return any(league_name[1].upper() not in folder_names for league_name in settings.teams)


def resize_image(image_path: str | Path, directory: str | Path, file_name: str) -> None:
    """Resize image to fit better on Monitor.

    :param image_path: Path of where image was downloaded
    :param directory: Folder were new resized image should be put
    :param file_name: Name to use as file name
    """
    window_width = Sg.Window.get_screen_size()[0] * .9
    window_height = Sg.Window.get_screen_size()[1] * .9

    if "sport_logos" in str(image_path):  # If team logo it should fit into these specifications
        column_width = window_width / 3
        column_height = window_height * .66
        column_height = column_height * (4 / 5)
    else:  # If network logo of base images it should fit into these specifications
        column_width = window_width / 3
        column_height = window_height * .66
        column_height = column_height * (5 / 16)

    # Open an image file using Pillow
    img = Image.open(image_path)

    # Calculate new size based on screen size
    width, height = img.size
    new_width = width
    new_height = height

    iteration = 1.0
    if width > column_width or height > column_height:
        width_ratio = column_width / width
        height_ratio = column_height / height
        scale_factor = min(width_ratio, height_ratio)

        new_width = int(width * scale_factor)
        new_height = int(height * scale_factor)

    elif width < column_width or height < column_height:
        while new_width < column_width and new_height < column_height:
            new_width = int(width * iteration)
            new_height = int(height * iteration)
            iteration += .001
        new_width = int(width * (iteration + .005))
        new_height = int(height * (iteration + .005))

    # If images dont need resizing then dont resave images (images get distorted over time, copy of a copy)
    if abs(width - new_width) <= 3 and abs(height - new_height) <= 3 and "sport_logos" not in str(image_path):
        logger.info("%s Does not need resizing", file_name)
        return

    logger.info("Resizing %s logo to %dx%d from %dx%d.", file_name, new_width, new_height, width, height)

    if ".png" in file_name:  # Remove .png if in filename as it will be saved with .png below
        file_name = file_name.replace(".png", "")

    # Resize and save the new image
    img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    new_path_png = Path.cwd() / directory / f"{file_name}.png"
    img_resized.save(new_path_png)


def download_team_logos(window: Sg.Window, teams: list) -> None:
    """Use ESPN API to download team logos for all leagues that user selects for their teams.

    :param teams: Dictionary with teams to display
    :param teams: List of teams containing leagues to get logos for
    """
    count = 0
    # Loop through each league to get the teams
    for i in range(len(teams)):
        sport_league = teams[i][1].lower()
        sport_name = teams[i][2].lower()
        if not Path.exists(Path.cwd() / "images" / "sport_logos" / sport_league.upper()):

            # Create a directory for the current sport if it doesn't exist
            sport_dir = Path.cwd() / "images" / "sport_logos" / sport_league.upper()
            if not Path.exists(sport_dir):
                Path.mkdir(sport_dir)

            # Fetch the JSON data
            url = f"https://site.api.espn.com/apis/site/v2/sports/{sport_name}/{sport_league}/teams"
            response = requests.get(url, timeout=5)
            data = response.json()

            # Extract team data
            teams_data = data.get("sports", [{}])[0].get("leagues", [{}])[0].get("teams", [])

            # Download, process, resize, and save each logo
            for team in teams_data:
                team_name = team["team"]["displayName"]
                logo_url = team["team"]["logos"][0]["href"]
                team_name = team_name.upper()

                logger.info("Downloading logo for %s from %s...", team_name, teams[i][1])

                img_path_png = str(Path.cwd() / "images" / "sport_logos" / str(team_name)) + "_Original.png"
                response = requests.get(logo_url, stream=True, timeout=5)
                with Path(img_path_png).open("wb") as file:
                    file.writelines(response.iter_content(chunk_size=1024))

                # Open, resize, and save the image with PIL
                with Image.open(img_path_png):
                    resize_image(img_path_png, sport_dir, team_name)

                # Delete the original .png file
                Path.unlink(Path(img_path_png))
                count +=1
                window["PROGRESS_BAR"].update(current_count=count)
                window.refresh()  # Refresh to display text

    if Path.exists(Path.cwd() / "images" / "sport_logos"):
        logger.info("All logos have been downloaded!\n")


def get_team_logos(window: Sg.Window, teams: list) -> str:
    """Determine if logos need to be downloaded.

    :param teams: Dictionary with teams to display
    :param TEAM_LOGO_SIZE: Size of team logos to display

    :return: message to display if things logos where downloaded and resized successful or failed
    """
    already_downloaded = True
    try:
        if not Path.exists(Path.cwd() / "images" / "sport_logos"):
            Path.mkdir((Path.cwd() / "images" / "sport_logos"), exist_ok=True)
            msg = "First time running, Downloading and Re-sizing logos"
            window["download_message"].update(value=msg)
            download_team_logos(window, teams)
            # Resize local images to fit on screen
            resize_images_from_folder([
                NETWORKS_DIR,
                BASEBALL_BASE_IMAGES_DIR,
                CONFERENCE_CHAMPIONSHIP_IMAGES_DIR,
                PLAYOFF_IMAGES_DIR,
                CHAMPIONSHIP_IMAGES_DIR,
            ])
            already_downloaded = False  # If hit this is the first time getting images and resizing
            return check_downloaded_correctly()

        # If user selects new team in a league they haven't selected before download all logos in that league
        if new_league_added():
            msg = "New league added, Downloading and Re-sizing logos for new league"
            window["download_message"].update(value=msg)
            download_team_logos(window, teams)  # Will only get new league team logos
            return check_downloaded_correctly()

        if settings.always_get_logos and already_downloaded:
            msg = "Always get logos in settings selected, Downloading and Re-sizing logos"
            window["download_message"].update(value=msg)
            # Dont want to continually resize images multiple times, so remove
            shutil.rmtree(Path.cwd() / SPORT_LOGOS_DIR)
            Path.mkdir((Path.cwd() / SPORT_LOGOS_DIR), exist_ok=True)
            download_team_logos(window, teams)
            resize_images_from_folder([
                NETWORKS_DIR,
                BASEBALL_BASE_IMAGES_DIR,
                CONFERENCE_CHAMPIONSHIP_IMAGES_DIR,
                PLAYOFF_IMAGES_DIR,
                CHAMPIONSHIP_IMAGES_DIR,
            ])
            return check_downloaded_correctly()

    except Exception as e:
        logger.exception("Failed to download team logos")
        return "Failed to download team logos, please try again. Error: " + str(e)

    return "Starting..."

def get_random_logo() -> dict:
    """Get 2 random teams from teams array, if only one team then it will return the only team there.

    :return logos: Dictionary with league name and team name for file location
    """
    logos = {}
    if len(settings.teams) >= 2:
        random_indexes = random.sample(range(len(settings.teams)), 2)

        logos[0] = [settings.teams[random_indexes[0]][1].upper(), settings.teams[random_indexes[0]][0].upper()]
        logos[1] = [settings.teams[random_indexes[1]][1].upper(), settings.teams[random_indexes[1]][0].upper()]
    # If only one team in teams array then only return the one file location for logo
    else:
        logos[0] = [settings.teams[[0][0]][1].upper(), settings.teams[[0][0]][0].upper()]
        logos[1] = [settings.teams[[0][0]][1].upper(), settings.teams[[0][0]][0].upper()]

    return logos


def resize_images_from_folder(image_folder_path: list[Path]) -> None:
    """Resize all images in the folder.

    :param image_folder_path: folder to look through to find png images
    """
    for folder in image_folder_path:
            folder_path = Path.cwd() / folder
            files = [
                f for f in folder_path.iterdir()
                if f.is_file() and f.suffix.lower() == ".png"
            ]
            for file in files:
                resize_image(file, file.parent, file.name)


def check_downloaded_correctly() -> str:
    """Check to see that all logos for every team was downloaded.

    return: Empty string if all logos downloaded correctly, otherwise error message
    """
    folder_path = Path.cwd() / "images" / "sport_logos"

    sports_logo_folders = list(folder_path.iterdir())

    MLB.append("MLB")
    NFL.append("NFL")
    NBA.append("NBA")
    NHL.append("NHL")

    for folder in sports_logo_folders:

        if folder.name in MLB:
            looking_at_sport = "MLB"
        elif folder.name in NFL:
            looking_at_sport = "NFL"
        elif folder.name in NBA:
            looking_at_sport = "NBA"
        elif folder.name in NHL:
            looking_at_sport = "NHL"
        else:
            return "Failed to get Logos, Please Retry By Pressing Start Again."

        if looking_at_sport == "MLB" and len(list(folder.iterdir())) != len(MLB) - 1:
            number_of_files = len(list(folder.iterdir()))
            shutil.rmtree(folder_path)
            MLB.remove("MLB")
            return ("Failed to get MLB Logos, Please Retry By Pressing Start Again."
                    f" Got {number_of_files} logos but MLB has {len(MLB)} teams.")
        if looking_at_sport == "NFL" and len(list(folder.iterdir())) != len(NFL) - 1:
            number_of_files = len(list(folder.iterdir()))
            shutil.rmtree(folder_path)
            NFL.remove("NFL")
            return ("Failed to get NFL Logos, Please Retry By Pressing Start Again."
                    f" Got {number_of_files} logos but NFL has {len(NFL)} teams.")
        if looking_at_sport == "NBA" and len(list(folder.iterdir())) != len(NBA) - 1:
            number_of_files = len(list(folder.iterdir()))
            shutil.rmtree(folder_path)
            NBA.remove("NBA")
            return ("Failed to get NBA Logos, Please Retry By Pressing Start Again."
                    f" Got {number_of_files} logos but NBA has {len(NBA)} teams.")
        if looking_at_sport == "NHL" and len(list(folder.iterdir())) != len(NHL) - 1:
            number_of_files = len(list(folder.iterdir()))
            shutil.rmtree(folder_path)
            NHL.remove("NHL")
            return ("Failed to get NHL Logos, Please Retry By Pressing Start Again."
                    f" Got {number_of_files} logos but NHL has {len(NHL)} teams.")

    MLB.remove("MLB")
    NFL.remove("NFL")
    NBA.remove("NBA")
    NHL.remove("NHL")
    return ""
