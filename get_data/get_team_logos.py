"""Use ESPN API to Grab Major League Sports Teams logo and Resize to fit screen."""

import random
import shutil
from pathlib import Path

import FreeSimpleGUI as Sg  # type: ignore
import requests  # type: ignore
from PIL import Image  # type: ignore

import settings
from get_data.get_team_league import MLB, NBA, NFL, NHL


def new_league_added() -> bool:
    """Check if new league has been added to teams array.

    :return: True if new league added, False otherwise
    """
    folder_names = ([name for name in Path(Path.cwd() / "images" / "sport_logos").iterdir()
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

    print(f"Resizing {file_name} logo to {new_width}x{new_height} from {width}x{height}.")

    if ".png" in file_name:  # Remove .png if in filename as it will be saved with .png below
        file_name = file_name.replace(".png", "")

    # Resize and save the new image
    img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    new_path_png = (Path.cwd() / directory / file_name).with_suffix(".png")
    img_resized.save(new_path_png)


def download_team_logos(window: Sg.Window, teams: list) -> None:
    """Use ESPN API to download team logos for all leagues that user selects for their teams.

    :param teams: Dictionary with teams to display
    :param TEAM_LOGO_SIZE: Size of team logos to display
    """
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

                print(f"Downloading logo for {team_name} from {teams[i][1]}...")
                print()

                img_path_png = str(Path.cwd() / "images" / "sport_logos" / str(team_name)) + "_Original.png"
                response = requests.get(logo_url, stream=True, timeout=5)
                with Path(img_path_png).open("wb") as file:
                    for chunk in response.iter_content(chunk_size=1024):
                        file.write(chunk)

                # Open, resize, and save the image with PIL
                with Image.open(img_path_png):
                    resize_image(img_path_png, sport_dir, team_name)

                # Delete the original .png file
                Path.unlink(Path(img_path_png))
                window.refresh()  # Refresh to display text

    if Path.exists(Path.cwd() / "images" / "sport_logos"):
        print("All logos have been downloaded!")


def get_team_logos(window: Sg.Window, teams: list) -> str:
    """Determine if logos need to be downloaded.

    :param teams: Dictionary with teams to display
    :param TEAM_LOGO_SIZE: Size of team logos to display
    """
    already_downloaded = True
    if not Path.exists(Path.cwd() / "images" / "sport_logos"):
        Path.mkdir((Path.cwd() / "images" / "sport_logos"), exist_ok=True)
        download_team_logos(window, teams)
        # Resize local images to fit on screen
        resize_images_from_folder([
            Path("images/Networks"),
            Path("images/baseball_base_images"),
            Path("images/conference_championship_images"),
            Path("images/playoff_images"),
            Path("images/championship_images"),
        ])
        already_downloaded = False  # If hit this is the first time getting images and resizing
        return check_downloaded_correctly()

    # If user selects new team in a league they haven't selected before download all logos in that league
    elif new_league_added():
        download_team_logos(window, teams)  # Will only get new league team logos
        return check_downloaded_correctly()

    if settings.always_get_logos and already_downloaded:
        # Dont want to continually resize images multiple times, so remove
        shutil.rmtree(Path.cwd() / "images" / "sport_logos")
        Path.mkdir((Path.cwd() / "images" / "sport_logos"), exist_ok=True)
        download_team_logos(window, teams)
        return check_downloaded_correctly()

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
    """Check to see that all logos for every team was downloaded."""

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

        if looking_at_sport == "MLB":
            if len(list(folder.iterdir())) != len(MLB) - 1:
                number_of_files = len(list(folder.iterdir()))
                shutil.rmtree(folder_path)
                MLB.remove("MLB")
                return ("Failed to get MLB Logos, Please Retry By Pressing Start Again."
                        f" Got {number_of_files} logos but MLB has {len(MLB)} teams.")
        if looking_at_sport == "NFL":
            if len(list(folder.iterdir())) != len(NFL) - 1:
                number_of_files = len(list(folder.iterdir()))
                shutil.rmtree(folder_path)
                NFL.remove("NFL")
                return ("Failed to get NFL Logos, Please Retry By Pressing Start Again."
                        f" Got {number_of_files} logos but NFL has {len(NFL)} teams.")
        if looking_at_sport == "NBA":
            if len(list(folder.iterdir())) != len(NBA) - 1:
                number_of_files = len(list(folder.iterdir()))
                shutil.rmtree(folder_path)
                NBA.remove("NBA")
                return ("Failed to get NBA Logos, Please Retry By Pressing Start Again."
                        f" Got {number_of_files} logos but NBA has {len(NBA)} teams.")
        if looking_at_sport == "NHL":
            if len(list(folder.iterdir())) != len(NHL) - 1:
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
