'''Use ESPN API to Grab Major League Sports Teams logo and Resize based in Constant'''

import os
from PIL import Image  # pip install pillow
import requests  # pip install requests
import random
from constants import *


def resize_image(image_path: str, sport_dir: str, team_name: str, scale_factor: int) -> None:
    '''Resize image to fit better on Monitor

    :param image_path: Path of where image was downloaded
    :param sport_dir: Folder were new resized image should be put
    :param team_name: Team name to use as file name
    :param scale_factor: What scale to resize the image to
    '''
    # Open an image file using Pillow
    img = Image.open(image_path)

    # Calculate new size based on scale factor
    width, height = img.size
    new_width = int(width * scale_factor)
    new_height = int(height * scale_factor)

    # Resize the image
    img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    new_path_png = os.path.join(sport_dir, f"{team_name}.png")
    img_resized.save(new_path_png)


def get_team_logos(teams: list, TEAM_LOGO_SIZE: int) -> None:
    ''' Create a base directory to store the logos if it doesn't exist

    :param teams: Dictionary with teams to display
    :param TEAM_LOGO_SIZE: Size of team logos to display
    '''
    if not os.path.exists('sport_logos'):
        os.makedirs('sport_logos')
        logo_directories = []

        # Loop through each league to get the teams
        for i in range(len(teams)):
            sport_league = teams[i][1].lower()
            sport_name = teams[i][2].lower()
            if not os.path.exists(f"{sport_league.upper()}"):
                logo_directories.append(f"{sport_league.upper()}")

                # Create a directory for the current sport if it doesn't exist
                sport_dir = os.path.join('sport_logos', logo_directories[i])
                if not os.path.exists(sport_dir):
                    os.makedirs(sport_dir)

                # Fetch the JSON data
                url = f"https://site.api.espn.com/apis/site/v2/sports/{sport_name}/{sport_league}/teams"
                response = requests.get(url)
                data = response.json()

                # Extract team data
                teams_data = data.get('sports', [{}])[0].get('leagues', [{}])[0].get('teams', [])

                # Download, process, resize, and save each logo
                for team in teams_data:
                    team_name = team['team']["displayName"]
                    logo_url = team['team']['logos'][0]['href']
                    team_name = team_name.upper()

                    print(f"Downloading logo for {team_name} from {teams[i][1]}...")

                    img_path_png = os.path.join(sport_dir, f"{team_name}_Original.png")
                    response = requests.get(logo_url, stream=True)
                    with open(img_path_png, 'wb') as file:
                        for chunk in response.iter_content(chunk_size=1024):
                            file.write(chunk)

                    # Open, resize, and save the image with PIL
                    with Image.open(img_path_png):
                        resize_image(img_path_png, sport_dir, team_name, TEAM_LOGO_SIZE)

                    # Delete the original .png file
                    os.remove(img_path_png)

        if os.path.exists('sport_logos'):
            print("All logos have been downloaded!")


def get_random_logo() -> dict:
    '''Get 2 random teams from teams array, if only one team then it will return the only team there

    :return logos: Dictionary with team logos
    '''
    logos = {}
    if len(teams) >= 2:
        random_indexes = random.sample(range(len(teams)), 2)

        logos[0] = [teams[random_indexes[0]][1].upper(), teams[random_indexes[0]][0].upper()]
        logos[1] = [teams[random_indexes[1]][1].upper(), teams[random_indexes[1]][0].upper()]
    # If only one team in teams array then only return the one file location for logo
    else:
        random_indexes = 0
        logos[0] = [teams[random_indexes[0]][1].upper(), teams[random_indexes[0]][0].upper()]
        logos[1] = [teams[random_indexes[0]][1].upper(), teams[random_indexes[0]][0].upper()]

    return logos
