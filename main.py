"""Main file to run."""
import os
import platform
import subprocess
import sys
import venv
from pathlib import Path

from helper_functions.logger_config import logger


def create_virtualenv(venv_dir: str) -> None:
    """Create a virtual environment in the specified directory.

    :param venv_dir: virtual environment directory name
    """
    if not Path(venv_dir).exists():
        logger.info(f"Creating virtual environment in {venv_dir}...")
        venv.create(venv_dir, with_pip=True)
    else:
        logger.info(f"Virtual environment already exists in {venv_dir}.")


def install_requirements(venv_dir: str, requirements_file: str) -> None:
    """Installs dependencies from a requirements.txt file.

    :param venv_dir: virtual environment directory name
    :param requirements_file: file name to install requirements from
    """
    if not Path(requirements_file).exists():
        logger.info("No requirements file found. Script cannot run.")
        sys.exit(1)

    logger.info(f"Installing dependencies from {requirements_file}...")

    pip_executable = (Path(venv_dir) / "Scripts" / "pip.exe") \
        if platform.system() == "Windows" else (Path(venv_dir) / "bin" / "pip")

    if not Path(pip_executable).exists():
        logger.info(f"Error: pip executable not found at {pip_executable}")
        sys.exit(1)

    subprocess.check_call([pip_executable, "install", "-r", requirements_file])


def run_program_in_venv(venv_dir: str, program_script: str) -> None:
    """Run a Python program inside the virtual environment.

    :param venv_dir: virtual environment directory name
    :param program_script: python module to execute in subprocess
    """
    python_executable = (Path(venv_dir) / "Scripts" / "python.exe") \
        if platform.system() == "Windows" else (Path(venv_dir) / "bin" / "python")

    if not Path(python_executable).exists():
        logger.info(f"Error: Python executable not found at {python_executable}")
        sys.exit(1)

    # Run the program
    logger.info(f"Running program {program_script} inside virtual environment...")
    subprocess.call([python_executable, "-m", program_script])


def set_screen() -> None:
    """Set the screen for the program to run on."""
    if sys.prefix == sys.base_prefix:
        logger.info("Please activate the virtual environment before running.")
        sys.exit(1)

    if platform.system() != "Windows" and os.environ.get("DISPLAY", "") == "":
        logger.info("No display found. Using :0.0")
        os.environ["DISPLAY"] = ":0.0"


def remove_ds_files() -> None:
    """Remove all .DS_Store files (only needed on macOS)."""
    if platform.system() == "Darwin":
        logger.info("Removing .DS_Store files...")
        # Walk through the directory and remove .DS_Store files
        for root, _, files in os.walk("."):
            for file in files:
                if file == ".DS_Store":
                    path = Path(root) / file
                    logger.info(f"Removing: {path}")
                    path.unlink()


def main() -> None:
    """Create virtual environment, download dependencies, and run script."""
    venv_dir = "./venv"
    requirements_file = "requirements.txt"
    program_script = "screens.main_screen"

    create_virtualenv(venv_dir)
    install_requirements(venv_dir, requirements_file)
    remove_ds_files()
    run_program_in_venv(venv_dir, program_script)


if __name__ == "__main__":
    main()
