import os
import subprocess
import sys
import platform
import venv

def create_virtualenv(venv_dir):
    """Creates a virtual environment in the specified directory."""
    if not os.path.exists(venv_dir):
        print(f"Creating virtual environment in {venv_dir}...")
        venv.create(venv_dir, with_pip=True)
    else:
        print(f"Virtual environment already exists in {venv_dir}.")
        
def activate_venv(venv_dir):
    """Activates the virtual environment and runs the given program."""
    if platform.system() == 'Windows':
        activate_script = os.path.join(venv_dir, 'Scripts', 'activate.bat')
    else:
        activate_script = os.path.join(venv_dir, 'bin', 'activate')

    if not os.path.exists(activate_script):
        print(f"Error: Virtual environment activation script not found at {activate_script}")
        sys.exit(1)
    
    # Activate the virtual environment and run a program
    if platform.system() == 'Windows':
        subprocess.call([activate_script], shell=True)
    else:
        # For Linux/MacOS, 'source' needs to be used in the shell context
        subprocess.call(f"source {activate_script} && python my_program.py", shell=True)

def install_requirements(venv_dir, requirements_file):
    """Installs dependencies from a requirements.txt file."""
    if os.path.exists(requirements_file):
        print(f"Installing dependencies from {requirements_file}...")
        pip_executable = os.path.join(venv_dir, 'Scripts', 'pip') if platform.system() == 'Windows' else os.path.join(venv_dir, 'bin', 'pip')
        subprocess.call([pip_executable, 'install', '-r', requirements_file])
    else:
        print(f"No requirements file found at {requirements_file}.")

def run_program_in_venv(venv_dir, program_script):
    """Runs a Python program inside the virtual environment."""
    python_executable = os.path.join(venv_dir, 'Scripts', 'python') if platform.system() == 'Windows' else os.path.join(venv_dir, 'bin', 'python')
    
    if not os.path.exists(python_executable):
        print(f"Error: Python executable not found at {python_executable}")
        sys.exit(1)

    # Run the program
    print(f"Running program {program_script} inside virtual environment...")
    subprocess.call([python_executable, program_script])

def main():
    venv_dir = './venv'  # Virtual environment directory
    requirements_file = 'requirements.txt'  # Optional: Path to your requirements.txt
    program_script = 'scoreboard.py'  # Replace with the name of your program

    create_virtualenv(venv_dir)
    install_requirements(venv_dir, requirements_file)
    run_program_in_venv(venv_dir, program_script)

if __name__ == "__main__":
    main()
