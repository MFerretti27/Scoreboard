"""Functions to check and manage GitHub releases for the packaged app."""
from __future__ import annotations

import platform
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

import requests  # type: ignore[import]

import settings
from helper_functions.logging.logger_config import logger

if TYPE_CHECKING:
    import FreeSimpleGUI as Sg

# GitHub repo info
GITHUB_REPO = "MFerretti27/Scoreboard"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"

# Local version file
LOCAL_VERSION_FILE = "version.txt"


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


def get_all_releases() -> list[dict[str, Any]] | None:
    """Fetch all releases from GitHub API.

    :return: List of release dicts or None if error
    """
    try:
        url = f"https://api.github.com/repos/{GITHUB_REPO}/releases"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception:
        logger.info("Error fetching all releases from GitHub", exc_info=True)
        return None


def get_release_by_version(version: str) -> dict[str, Any] | None:
    """Fetch a specific release by version tag.

    :param version: Version tag (e.g., "0.0.3" or "V0.0.3")
    :return: Release dict or None if not found
    """
    try:
        url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/tags/V{version.lstrip('vV')}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception:
        logger.info("Error fetching release for version %s", version, exc_info=True)
        return None


def get_latest_release() -> dict[str, Any] | None:
    """Fetch the latest release info from GitHub API.

    :return: Release dict with 'tag_name' and 'assets', or None if error
    """
    try:
        response = requests.get(GITHUB_API_URL, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception:
        logger.info("Error checking GitHub for latest release", exc_info=True)
        return None


def get_platform_asset(release: dict[str, Any]) -> str | None:
    """Get the download URL for the current platform's release asset.

    :param release: Release dict from GitHub API
    :return: Download URL or None if asset not found
    """
    system = platform.system()

    # Map system to expected asset name patterns
    if system == "Windows":
        asset_pattern = ".exe"
    elif system == "Darwin":  # macOS
        asset_pattern = ".dmg"
    else:
        logger.info("Unsupported platform: %s", system)
        return None

    for asset in release.get("assets", []):
        if asset_pattern in asset["name"].lower():
            return asset["browser_download_url"]

    logger.info("No %s asset found in release", asset_pattern)
    return None


def is_newer(local: str, remote: str) -> bool:
    """Compare two version strings (semver).

    :param local: Local version string (e.g., "1.2.3" or "v1.2.3")
    :param remote: Remote version string (e.g., "1.2.4" or "v1.2.4")
    :return: True if remote version is newer
    """
    def parse(v: str) -> tuple[int, int, int]:
        # Remove 'v' or 'V' prefix if present
        v_clean = v.lstrip("vV") if v and v[0].lower() == "v" else v
        parts = v_clean.split(".")
        return (int(parts[0]), int(parts[1] if len(parts) > 1 else 0), int(parts[2] if len(parts) > 2 else 0))

    try:
        return parse(remote) > parse(local)
    except (ValueError, IndexError):
        logger.warning("Could not parse versions: %s vs %s", local, remote)
        return False


def download_release_asset(url: str, output_path: Path) -> bool:
    """Download a release asset from GitHub.

    :param url: Download URL
    :param output_path: Where to save the file
    :return: True if successful
    """
    try:
        logger.info("Downloading release asset from: %s", url)
        response = requests.get(url, timeout=30, stream=True)
        response.raise_for_status()

        total_size = int(response.headers.get("content-length", 0))
        downloaded = 0

        with output_path.open("wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                downloaded += len(chunk)
                if total_size:
                    percent = (downloaded / total_size) * 100
                    logger.debug("Download progress: %.1f%%", percent)

        logger.info("Downloaded successfully to: %s", output_path)
    except Exception:
        logger.exception("Failed to download release asset", exc_info=True)
        return False
    else:
        return True


def backup_current_app(app_path: Path) -> Path | None:
    """Backup the current app before updating.

    :param app_path: Path to the current app executable
    :return: Path to backup or None if failed
    """
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = app_path.parent / f"{app_path.stem}_backup_{timestamp}{app_path.suffix}"

        logger.info("Backing up current app to: %s", backup_path)
        shutil.copy2(app_path, backup_path)
    except Exception:
        logger.exception("Failed to backup current app", exc_info=True)
        return None
    else:
        return backup_path


def launch_update_installer(new_app_path: Path, current_app_path: Path) -> bool:
    """Launch a subprocess to handle the app replacement and restart.

    This runs independently so the main app can exit cleanly.

    :param new_app_path: Path to the newly downloaded app
    :param current_app_path: Path to the current running app
    :return: True if subprocess launched successfully, False otherwise
    """
    # Create updater script
    updater_script = f"""
import shutil
import time
import subprocess
import sys
from pathlib import Path

new_app = Path(r"{new_app_path}")
current_app = Path(r"{current_app_path}")

# Wait for main app to exit
time.sleep(2)

try:
    # Back up current app
    import datetime
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = current_app.parent / f"{{current_app.stem}}_backup_{{timestamp}}{{current_app.suffix}}"
    shutil.copy2(current_app, backup)
    print(f"Backed up to: {{backup}}")

    # Replace with new app
    shutil.move(str(new_app), str(current_app))
    print(f"Replaced app at: {{current_app}}")

    # Restart the app
    subprocess.Popen([str(current_app)])
    print("App restarted successfully")
except Exception as e:
    print(f"Update failed: {{e}}")
    sys.exit(1)
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(updater_script)
        updater_path = f.name

    try:
        logger.info("Launching update installer from: %s", updater_path)
        subprocess.Popen([sys.executable, updater_path], start_new_session=True)
    except Exception:
        logger.exception("Failed to launch updater subprocess", exc_info=True)
        return False
    else:
        return True


def check_for_update() -> tuple[str, bool, bool]:
    """Check if an update is available.

    :return: tuple[message, success, is_up_to_date]
    """
    local_version = get_local_version()
    if not local_version:
        return "Could not read local version", False, False

    release = get_latest_release()
    if not release:
        return "Could not check for updates (GitHub offline?)", False, False

    remote_version = release.get("tag_name")
    if not remote_version:
        return "Invalid release data from GitHub", False, False

    if is_newer(local_version, remote_version):
        return f"Update available: {remote_version} (current: {local_version})", True, False

    return f"Running latest version ({local_version})", True, True


def download_specific_version(version: str) -> tuple[str, bool]:
    """Download and apply a specific version.

    :param version: Version string (e.g., "0.0.2")
    :return: tuple[message, success]
    """
    release = get_release_by_version(version)
    if not release:
        return f"Could not find release for version {version}", False

    asset_url = get_platform_asset(release)
    if not asset_url:
        return "No compatible asset found for your platform", False

    # Download to updates folder
    updates_dir = Path("updates")
    updates_dir.mkdir(exist_ok=True)
    downloaded_file = updates_dir / f"Scoreboard_v{version}{Path(asset_url).suffix}"

    if not download_release_asset(asset_url, downloaded_file):
        return "Failed to download release", False

    # Determine current app path
    if getattr(sys, "frozen", False):
        current_app = Path(sys.executable)
    else:
        return "Running from source code, cannot update", False

    # Launch updater
    if not launch_update_installer(downloaded_file, current_app):
        return "Failed to launch updater", False

    return f"Updating to version {version}. The app will restart...", True


def download_and_prepare_update() -> tuple[str, Path | None]:
    """Download the latest release and prepare for update.

    :return: tuple[message, path_to_new_app] or tuple[error_message, None]
    """
    release = get_latest_release()
    if not release:
        return "Could not fetch release information", None

    download_url = get_platform_asset(release)
    if not download_url:
        return f"No release available for {platform.system()}", None

    # Download to temp location
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        app_filename = download_url.split("/")[-1]
        new_app_path = temp_path / app_filename

        if not download_release_asset(download_url, new_app_path):
            return "Failed to download update", None

        # Copy to persistent location for updater subprocess
        updates_dir = Path.cwd() / "updates"
        updates_dir.mkdir(exist_ok=True)
        persistent_path = updates_dir / app_filename

        try:
            shutil.copy2(new_app_path, persistent_path)
            logger.info("Update prepared at: %s", persistent_path)
            return f"Update ready: {release.get('tag_name')}", persistent_path
        except Exception:
            logger.exception("Failed to prepare update", exc_info=True)
            return "Failed to prepare update", None


def apply_update(current_app_path: Path | None = None) -> tuple[str, bool]:
    """Apply the update by launching the installer subprocess.

    :param current_app_path: Path to the current running app (auto-detected if None)
    :return: tuple[message, success]
    """
    if current_app_path is None:
        # Auto-detect current app path
        if getattr(sys, "frozen", False):
            current_app_path = Path(sys.executable)
        else:
            return "Could not determine current app path", False

    message, new_app_path = download_and_prepare_update()
    if not new_app_path:
        return message, False

    logger.info("Launching update process...")
    if not launch_update_installer(new_app_path, current_app_path):
        return "Failed to launch update installer", False

    return "Update in progress. App will restart shortly.", True


def auto_update(window: Sg.Window) -> None:
    """Automatically check for updates at a scheduled time.

    If an update is available, download it and schedule app restart.

    :param window: The main GUI window
    """
    if not settings.auto_update:
        return

    # Check at 4:30 AM
    if datetime.now().hour == 4 and datetime.now().minute == 30:
        logger.info("Checking for update at scheduled time (4:30 AM)")

        message, success, latest = check_for_update()
        logger.info(message)

        if success and not latest:
            logger.info("Update available, preparing to download and apply...")
            msg, successful = apply_update()
            logger.info(msg)

            if successful:
                # Give user a moment to see message, then exit
                window.read(timeout=2000)
                logger.info("Exiting app for update installation...")
                sys.exit(0)
