import os
import subprocess
import sys
import platform
import venv


def create_virtualenv(venv_dir: str) -> None:
    """Creates a virtual environment in the specified directory

    :param venv_dir: Path to the virtual environment directory
    """

    if not os.path.exists(venv_dir):
        print(f"Creating virtual environment in {venv_dir}...")
        venv.create(venv_dir, with_pip=True)
    else:
        print(f"Virtual environment already exists in {venv_dir}.")


def install_requirements(venv_dir: str, requirements_file: str) -> None:
    """Installs dependencies from a requirements.txt file

    :param venv_dir: Path to the virtual environment directory
    :param requirements_file: requirements file name
    """

    if os.path.exists(requirements_file):
        print(f"Installing dependencies from {requirements_file}...")

        # Based on OS determine the path to the to activate the virtual environment
        pip_executable = os.path.join(venv_dir, 'Scripts', 'pip') \
            if platform.system() == 'Windows' else os.path.join(venv_dir, 'bin', 'pip')

        # Install dependencies
        subprocess.call([pip_executable, 'install', '-r', requirements_file])
    else:
        print("No requirements file found script cannot run")
        exit()


def run_program_in_venv(venv_dir: str, program_script: str) -> None:
    """Runs a Python program inside the virtual environment

    :param venv_dir: Path to the virtual environment directory
    :param program_script: Name of the Python program to run
    """

    # Based on OS determine the path to the to activate the virtual environment
    python_executable = os.path.join(venv_dir, 'Scripts', 'python') \
        if platform.system() == 'Windows' else os.path.join(venv_dir, 'bin', 'python')

    if not os.path.exists(python_executable):
        print(f"Error: Python executable not found at {python_executable}")
        sys.exit(1)

    # Run the program
    print(f"Running program {program_script} inside virtual environment...")
    subprocess.call([python_executable, program_script])


def main():
    venv_dir = './venv'  # Virtual environment directory
    requirements_file = 'requirements.txt'  # Path to requirements file
    program_script = 'main_screen.py'  # Name of main file to run

    create_virtualenv(venv_dir)
    install_requirements(venv_dir, requirements_file)
    run_program_in_venv(venv_dir, program_script)


if __name__ == "__main__":
    main()
