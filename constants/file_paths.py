"""File path constants for images and resources."""

from pathlib import Path

# Base directories
# Used internally to compose other path constants
IMAGES_DIR = Path("images")

# Used in: get_data/get_team_logos.py
SPORT_LOGOS_DIR = IMAGES_DIR / "sport_logos"

# Used in: get_data/get_team_logos.py
BASEBALL_BASE_IMAGES_DIR = IMAGES_DIR / "baseball_base_images"

# Used in: get_data/get_team_logos.py
CHAMPIONSHIP_IMAGES_DIR = IMAGES_DIR / "championship_images"

# Used in: get_data/get_team_logos.py
CONFERENCE_CHAMPIONSHIP_IMAGES_DIR = IMAGES_DIR / "conference_championship_images"

# Used in: get_data/get_team_logos.py
PLAYOFF_IMAGES_DIR = IMAGES_DIR / "playoff_images"

# Used in: get_data/get_team_logos.py, helper_functions/data/data_helpers.py
NETWORKS_DIR = IMAGES_DIR / "Networks"

# Used in: helper_functions/system/email.py
LOGS_DIR = Path("logs")

# Used internally in helper functions
PNG_EXT = ".png"


# Used in: get_data/get_espn_data.py, screens/clock_screen.py, gui_layouts/scoreboard_layout.py
def get_sport_logo_path(league: str, team: str) -> str:
    """Get path to sport team logo.

    :param league: League abbreviation (e.g., 'MLB', 'NBA', 'NFL', 'NHL')
    :param team: Team abbreviation
    :return: Path string to the logo file
    """
    return str(Path.cwd() / SPORT_LOGOS_DIR / league / f"{team}{PNG_EXT}")


# Used in: get_data/get_espn_data.py, get_data/get_mlb_data.py
def get_baseball_base_image_path(filename: str) -> str:
    """Get path to baseball base image.

    :param filename: Base image filename
    :return: Path string to the base image file
    """
    return str(Path.cwd() / BASEBALL_BASE_IMAGES_DIR / filename)


# Used in: get_data/get_game_type.py
def get_championship_image_path(filename: str) -> str:
    """Get path to championship image.

    :param filename: Championship image filename (e.g., 'world_series.png')
    :return: Path string to the championship image file
    """
    return str(Path.cwd() / CHAMPIONSHIP_IMAGES_DIR / filename)


# Used in: get_data/get_game_type.py
def get_conference_championship_image_path(filename: str) -> str:
    """Get path to conference championship image.

    :param filename: Conference championship image filename (e.g., 'alcs.png')
    :return: Path string to the conference championship image file
    """
    return str(Path.cwd() / CONFERENCE_CHAMPIONSHIP_IMAGES_DIR / filename)


# Used in: get_data/get_game_type.py
def get_playoff_image_path(filename: str) -> str:
    """Get path to playoff image.

    :param filename: Playoff image filename (e.g., 'nfl_playoffs.png')
    :return: Path string to the playoff image file
    """
    return str(Path.cwd() / PLAYOFF_IMAGES_DIR / filename)


# Used in: helper_functions/data/data_helpers.py
def get_network_image_path(filename: str) -> str:
    """Get path to network broadcast image.

    :param filename: Network image filename
    :return: Path string to the network image file
    """
    return str(Path.cwd() / NETWORKS_DIR / filename)
