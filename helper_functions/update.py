"""Functions to connect to GitHub and update files."""
import os
import re
import shutil
from pathlib import Path
from shutil import ignore_patterns

import requests  # type: ignore[import]

from helper_functions.logger_config import logger

# Path to local version.txt
LOCAL_VERSION_FILE = "version.txt"

# GitHub base URL (raw)
GITHUB_BASE_URL = (
    "https://raw.githubusercontent.com/MFerretti27/Scoreboard/refs/heads/main/"
)

# Path to version file on GitHub
GITHUB_VERSION_URL = GITHUB_BASE_URL + "version.txt"


# Automatically populate the list of files to update
def get_files_to_update(directory: str, extensions: list[str] | None = None) -> list[str]:
    """Scan the directory and returns a list of files with the specified extensions.

    :param directory: Directory to scan
    :param extensions: List of file extensions to look for

    :return: List of files to update
    """
    if extensions is None:
        extensions = [".py"]

    files_to_update = []
    for root, _, files in os.walk(directory):
        path_parts = Path(root).parts
        if any(x in path_parts for x in ("venv", ".vscode", ".git", "backup_files", "__pycache__")):
            continue
        for file in files:
            if file == "settings.py":
                continue
            if any(file.endswith(ext) for ext in extensions):
                relative_path = str(Path(root).joinpath(file).relative_to(directory))
                files_to_update.append(relative_path)
    return files_to_update


FILES_TO_UPDATE = get_files_to_update(str(Path.cwd()), extensions=[".py", ".txt", ".json"])


def get_local_version() -> str | None:
    """Read the local version from version.txt.

    :return: Local version string or None if an error occurs
    """
    try:
        with Path(LOCAL_VERSION_FILE).open() as f:
            return f.read().strip()
    except FileNotFoundError:
        logger.exception("Error: %s not found!", LOCAL_VERSION_FILE, exc_info=True)
        return None
    except Exception:
        logger.exception("Error reading %s", LOCAL_VERSION_FILE, exc_info=True)
        return None


def get_remote_version() -> str | None:
    """Fetch the remote version from GitHub.

    :return: Remote version string or None if an error occurs
    """
    try:
        response = requests.get(GITHUB_VERSION_URL, timeout=5)
        response.raise_for_status()
        text = response.text.strip()

        if text.startswith("<!DOCTYPE html") or "<html" in text.lower():
            logger.info("Error: version.txt not found or invalid URL.")
            return None
    except Exception:
        logger.info("Error checking remote version", exc_info=True)
        return None
    return text


def is_newer(local: str, remote: str) -> bool:
    """Compare two version strings.

    :param local: Local version string
    :param remote: Remote version string

    :return: True if remote version is newer, False otherwise
    """
    def parse(v: str) -> list[int]:
        return [int(x) for x in v.split(".")]

    return parse(remote) > parse(local)


def backup_entire_repo(project_folder: str, version: str) -> None:
    """Backup the entire project folder to a new location.

    :param project_folder: Path to the project folder
    :param version: Version string to include in the backup folder name
    """
    project_path = Path(project_folder)
    parent_folder = project_path.parent
    backup_folder_name = f"{project_path.name}-v{version}-backup"
    backup_folder_path = parent_folder / backup_folder_name

    logger.info("Backing up project: %s", project_folder)
    logger.info("Backup will be saved at: %s", backup_folder_path)

    if backup_folder_path.resolve() == project_path.resolve():
        logger.info("Error: Backup path is the same as project path! Aborting.")
        return

    if backup_folder_path.exists():
        logger.info("Backup folder already exists. Deleting old backup: %s", backup_folder_path)
        shutil.rmtree(backup_folder_path)

    try:
        shutil.copytree(project_path, backup_folder_path, ignore=ignore_patterns("*.pyc", "venv", ".git",
                                                                                 ".vscode", "backup_files",
                                                                                 "__pycache__"))
        logger.info("Backup completed successfully at: %s", backup_folder_path)
    except Exception:
        logger.exception("Error during backup", exc_info=True)


def download_file(file_path: str) -> None:
    """Download a file from GitHub and save it locally.

    :param file_path: Relative path to the file on GitHub
    """
    try:
        url = GITHUB_BASE_URL + file_path
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        local_path = Path.cwd() / file_path
        local_path.parent.mkdir(parents=True, exist_ok=True)

        with local_path.open("w", encoding="utf-8") as f:
            f.write(response.text)

        logger.info("Updated: %s", file_path)

    except Exception:
        logger.exception("Failed to update %s",file_path, exc_info=True)


def update_all_files() -> None:
    """Update all files in the current directory and subdirectories."""
    backup_entire_repo(str(Path.cwd()), get_local_version() or "unknown")
    for file in FILES_TO_UPDATE:
        download_file(file)


def list_backups(max_backups: int = 5) -> list[str]:
    """List all available backups for the project.

    :param max_backups: Maximum number of backups to keep

    :return: A list of versions that are found.
    """
    parent_folder = Path.cwd().parent
    project_name = Path.cwd().name

    backup_pattern = re.compile(rf"^{re.escape(project_name)}-v(\d+\.\d+\.\d+)-backup$")

    available_backups = []
    for item in parent_folder.iterdir():
        match = backup_pattern.match(item.name)
        if match:
            version = match.group(1)
            available_backups.append(version)

    available_backups.sort(reverse=True)

    if len(available_backups) > max_backups:
        backups_to_remove = available_backups[max_backups:]
        for backup in backups_to_remove:
            backup_folder_path = parent_folder / f"{project_name}-v{backup}-backup"
            logger.info("Removing old backup: %s", backup_folder_path)
            shutil.rmtree(backup_folder_path)
        available_backups = available_backups[:max_backups]

    return available_backups


def restore_backup(version: str) -> tuple[str, bool]:
    """Restore the backup from a specific version.

    :param version: Version string to restore
    """
    project_folder = Path.cwd()
    parent_folder = project_folder.parent
    backup_folder_path = parent_folder / f"{project_folder.name}-v{version}-backup"

    logger.info("Attempting to restore from: %s", backup_folder_path)

    if not backup_folder_path.exists():
        return f"Backup folder for version {version} not found!", False

    try:
        logger.info("Removing current project files...")
        for item in project_folder.iterdir():
            if item.name in {"venv", ".git", ".vscode", "backup_files", "__pycache__"}:
                continue
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()

        logger.info("Restoring backup files...")
        for item in backup_folder_path.iterdir():
            dst = project_folder / item.name
            if item.is_dir():
                shutil.copytree(item, dst)
            else:
                shutil.copy2(item, dst)

    except Exception as e:
        return f"Error during restore: {e}", False

    return f"Successfully restored project to version {version}", True


def check_for_update() -> tuple[str, bool, bool]:
    """Check if an update is available.

    :return: tuple[str, bool, bool] indicating status message, success, and if up to date
    """
    remote_version = get_remote_version()
    local_version = get_local_version()
    if not remote_version or not local_version:
        return "Could not Get Update", False, False

    if is_newer(local_version, remote_version):
        return f"Update available: {remote_version} (current: {local_version})", True, False

    return "You are running the latest version", True, True


def update_program() -> tuple[str, bool]:
    """Update the program to the latest version."""
    try:
        update_all_files()
    except Exception as e:
        return f"Error during update: {e}", False
    return "Update complete. Restarting application....", True
