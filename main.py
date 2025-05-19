import os
import subprocess
import sys
import platform
import venv


def create_virtualenv(venv_dir: str) -> None:
    """Creates a virtual environment in the specified directory.

    :param venv_dir: virtual environment directory name
    """
    if not os.path.exists(venv_dir):
        print(f"Creating virtual environment in {venv_dir}...")
        venv.create(venv_dir, with_pip=True)
    else:
        print(f"Virtual environment already exists in {venv_dir}.")


def install_requirements(venv_dir: str, requirements_file: str) -> None:
    """Installs dependencies from a requirements.txt file.

    :param venv_dir: virtual environment directory name
    :param requirements_file: file name to install requirements from
    """
    if not os.path.exists(requirements_file):
        print("No requirements file found. Script cannot run.")
        sys.exit(1)

    print(f"Installing dependencies from {requirements_file}...")

    pip_executable = os.path.join(venv_dir, 'Scripts', 'pip.exe') \
        if platform.system() == 'Windows' else os.path.join(venv_dir, 'bin', 'pip')

    if not os.path.exists(pip_executable):
        print(f"Error: pip executable not found at {pip_executable}")
        sys.exit(1)

    subprocess.check_call([pip_executable, 'install', '-r', requirements_file])


def run_program_in_venv(venv_dir: str, program_script: str) -> None:
    """Runs a Python program inside the virtual environment.

    :param venv_dir: virtual environment directory name
    :param program_script: python module to execute in subprocess
    """
    python_executable = os.path.join(venv_dir, 'Scripts', 'python.exe') \
        if platform.system() == 'Windows' else os.path.join(venv_dir, 'bin', 'python')

    if not os.path.exists(python_executable):
        print(f"Error: Python executable not found at {python_executable}")
        sys.exit(1)

    # Run the program
    print(f"Running program {program_script} inside virtual environment...")
    subprocess.call([python_executable, "-m", program_script])


def set_screen() -> None:
    """Sets the screen for the program to run on."""
    if sys.prefix == sys.base_prefix:
        print("Please activate the virtual environment before running.")
        sys.exit(1)

    if platform.system() != 'Windows':
        if os.environ.get('DISPLAY', '') == '':
            print('No display found. Using :0.0')
            os.environ['DISPLAY'] = ':0.0'


def remove_ds_files() -> None:
    """Removes all .DS_Store files (only needed on macOS)."""
    if platform.system() == 'Darwin':
        print("Removing .DS_Store files...")
        # Walk through the directory and remove .DS_Store files
        for root, _, files in os.walk('.'):
            for file in files:
                if file == '.DS_Store':
                    path = os.path.join(root, file)
                    print(f"Removing: {path}")
                    os.remove(path)


def main():
    venv_dir = './venv'
    requirements_file = 'requirements.txt'
    program_script = 'screens.main_screen'

    create_virtualenv(venv_dir)
    install_requirements(venv_dir, requirements_file)
    remove_ds_files()
    run_program_in_venv(venv_dir, program_script)


if __name__ == "__main__":
    main()
