"""File path constants for images and resources."""

from pathlib import Path

# Base directories
IMAGES_DIR = Path("images")
SPORT_LOGOS_DIR = IMAGES_DIR / "sport_logos"
BASEBALL_BASE_IMAGES_DIR = IMAGES_DIR / "baseball_base_images"
CHAMPIONSHIP_IMAGES_DIR = IMAGES_DIR / "championship_images"
CONFERENCE_CHAMPIONSHIP_IMAGES_DIR = IMAGES_DIR / "conference_championship_images"
PLAYOFF_IMAGES_DIR = IMAGES_DIR / "playoff_images"
NETWORKS_DIR = IMAGES_DIR / "Networks"

# Logs directory
LOGS_DIR = Path("logs")

# File extensions
PNG_EXT = ".png"


def get_sport_logo_path(league: str, team: str) -> str:
    """Get path to sport team logo.

    :param league: League abbreviation (e.g., 'MLB', 'NBA', 'NFL', 'NHL')
    :param team: Team abbreviation
    :return: Path string to the logo file
    """
    return str(SPORT_LOGOS_DIR / league / f"{team}{PNG_EXT}")


def get_baseball_base_image_path(filename: str) -> str:
    """Get path to baseball base image.

    :param filename: Base image filename
    :return: Path string to the base image file
    """
    return str(BASEBALL_BASE_IMAGES_DIR / filename)
