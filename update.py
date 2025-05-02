import requests  # type: ignore
import os
import shutil
import re

# Path to local version.txt
LOCAL_VERSION_FILE = "version.txt"

# GitHub base URL (raw)
GITHUB_BASE_URL = "https://raw.githubusercontent.com/MFerretti27/Scoreboard/refs/heads/Complete-Overhaul/"

# Path to version file on GitHub
GITHUB_VERSION_URL = GITHUB_BASE_URL + "version.txt"


# Automatically populate the list of files to update
def get_files_to_update(directory, extensions=[".py"]) -> list:
    """Scans the directory and returns a list of files with the specified extensions.

    :param directory: Directory to scan
    :param extensions: List of file extensions to look for

    :return: List of files to update
    """
    files_to_update = []
    for root, _, files in os.walk(directory):
        if "venv" in root.split(os.sep) or ".vscode" in root.split(os.sep) or ".git" in root.split(os.sep) or\
                "backup_files" in root.split(os.sep) or "__pycache__" in root.split(os.sep):
            continue
        for file in files:
            if file == "settings.py":
                continue
            # Check if the file has one of the extensions in the list
            if any(file.endswith(ext) for ext in extensions):
                # Get the relative path to the file
                relative_path = os.path.relpath(os.path.join(root, file), directory)
                files_to_update.append(relative_path)
    return files_to_update


# Get all Python files in the current directory and subdirectories
FILES_TO_UPDATE = get_files_to_update(os.getcwd(), extensions=[".py", ".txt", ".json"])


def get_local_version() -> str:
    """Read the local version from version.txt.

    :return: Local version string or None if an error occurs
    """
    try:
        with open(LOCAL_VERSION_FILE, 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        print(f"Error: {LOCAL_VERSION_FILE} not found!")
        return None
    except Exception as e:
        print(f"Error reading {LOCAL_VERSION_FILE}: {e}")
        return None


def get_remote_version() -> str:
    """Fetch the remote version from GitHub.

    :return: Remote version string or None if an error occurs
    """
    try:
        response = requests.get(GITHUB_VERSION_URL, timeout=5)
        response.raise_for_status()
        text = response.text.strip()

        # Detect if we accidentally got HTML instead of plain version
        if text.startswith("<!DOCTYPE html") or "<html" in text.lower():
            print("Error: version.txt not found or invalid URL.")
            return None

        return text
    except Exception as e:
        print(f"Error checking remote version: {e}")
        return None


def is_newer(local, remote) -> bool:
    """Compare two version strings.

    :param local: Local version string
    :param remote: Remote version string

    :return: True if remote version is newer, False otherwise
    """
    def parse(v):
        return [int(x) for x in v.split('.')]
    return parse(remote) > parse(local)


def backup_entire_repo(project_folder, version) -> None:
    """Backup the entire project folder to a new location.

    :param project_folder: Path to the project folder
    :param version: Version string to include in the backup folder name
    """
    # Backup folder will be created next to your project folder
    parent_folder = os.path.dirname(project_folder)

    backup_folder_name = f"{os.path.basename(project_folder)}-v{version}-backup"
    backup_folder_path = os.path.join(parent_folder, backup_folder_name)

    print(f"Backing up project: {project_folder}")
    print(f"Backup will be saved at: {backup_folder_path}")

    # Safety check
    if os.path.abspath(backup_folder_path) == os.path.abspath(project_folder):
        print("Error: Backup path is the same as project path! Aborting.")
        return

    # If backup folder already exists, remove it
    if os.path.exists(backup_folder_path):
        print(f"Backup folder already exists. Deleting old backup: {backup_folder_path}")
        shutil.rmtree(backup_folder_path)

    def ignore_patterns(directory, files):
        ignore_list = []
        for f in files:
            full_path = os.path.join(directory, f)
            # Ignore virtual environments, git, vscode settings, pycache, backup folders
            if f == 'venv' or f == '.git' or f == '.vscode' or f == 'backup_files' or f == '__pycache__':
                print(f"Ignoring folder: {full_path}")
                ignore_list.append(f)
            if f.endswith('.pyc'):
                ignore_list.append(f)
        return ignore_list

    try:
        shutil.copytree(project_folder, backup_folder_path, ignore=ignore_patterns)
        print(f"Backup completed successfully at: {backup_folder_path}")
    except Exception as e:
        print(f"Error during backup: {e}")


def download_file(file_path) -> None:
    """Download a file from GitHub and save it locally.

    :param file_path: Relative path to the file on GitHub
    """
    try:
        url = GITHUB_BASE_URL + file_path
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        # Ensure directory exists
        local_path = os.path.join(os.getcwd(), file_path)
        os.makedirs(os.path.dirname(local_path), exist_ok=True)

        # Write new file
        with open(local_path, "w", encoding="utf-8") as f:
            f.write(response.text)

        print(f"Updated: {file_path}")

    except Exception as e:
        print(f"Failed to update {file_path}: {e}")


def update_all_files() -> None:
    """Update all files in the current directory and subdirectories."""
    # Backup old file
    backup_entire_repo(os.getcwd(), get_local_version())
    for file in FILES_TO_UPDATE:
        download_file(file)


def list_backups(max_backups=5) -> list:
    """List all available backups for the project.

    :param max_backups: Maximum number of backups to keep

    Returns a list of version strings.
    """
    parent_folder = os.path.dirname(os.getcwd())
    project_name = os.path.basename(os.getcwd())

    # Regex pattern to match folders like "ProjectName-v1.2.3-backup"
    backup_pattern = re.compile(rf"^{re.escape(project_name)}-v(\d+\.\d+\.\d+)-backup$")

    available_backups = []

    for item in os.listdir(parent_folder):
        match = backup_pattern.match(item)
        if match:
            version = match.group(1)
            available_backups.append(version)

    # Sort backups in reverse order (newest first)
    available_backups.sort(reverse=True)

    # Check if there are more than the maximum allowed backups
    if len(available_backups) > max_backups:
        # Remove oldest backups if there are too many
        backups_to_remove = available_backups[max_backups:]
        for backup in backups_to_remove:
            backup_folder_path = os.path.join(parent_folder, f"{project_name}-v{backup}-backup")
            print(f"Removing old backup: {backup_folder_path}")
            shutil.rmtree(backup_folder_path)
        available_backups = available_backups[:max_backups]  # Keep only the latest backups

    return available_backups


def restore_backup(version) -> tuple:
    """Restore the backup made for a specific version.

    :param project_folder: Path to the project folder
    :param version: Version string to restore (e.g., "1.2.3")
    """
    project_folder = os.getcwd()
    parent_folder = os.path.dirname(project_folder)
    backup_folder_name = f"{os.path.basename(project_folder)}-v{version}-backup"
    backup_folder_path = os.path.join(parent_folder, backup_folder_name)

    print(f"Attempting to restore from: {backup_folder_path}")

    if not os.path.exists(backup_folder_path):
        print(f"Backup folder for version {version} not found!")
        return

    try:
        # --- REMOVE current files (but skip venv, .git, etc) ---
        print("Removing current project files...")
        for item in os.listdir(project_folder):
            if item in ['venv', '.git', '.vscode', 'backup_files', '__pycache__']:
                continue
            item_path = os.path.join(project_folder, item)
            if os.path.isdir(item_path):
                shutil.rmtree(item_path)
            else:
                os.remove(item_path)

        # --- COPY files from backup ---
        print("Restoring backup files...")
        for item in os.listdir(backup_folder_path):
            src = os.path.join(backup_folder_path, item)
            dst = os.path.join(project_folder, item)
            if os.path.isdir(src):
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)

        return f"Successfully restored project to version {version}", True

    except Exception as e:
        return f"Error during restore: {e}", False


def check_for_update() -> tuple:
    """Check if an update is available.

    Returns a message indicating whether an update is available.
    """
    remote_version = get_remote_version()
    if not remote_version:
        return "Could not Get Update", False, False

    if is_newer(get_local_version(), get_remote_version()):
        return (f"Update available: {remote_version} (current: {get_local_version()})"), True, False
    else:
        return "You are running the latest version", True, True


def update_program() -> tuple:
    """Update the program to the latest version."""
    try:
        update_all_files()
        return "Update complete. Restarting application....", True
    except Exception as e:
        return f"Error during update: {e}", False
