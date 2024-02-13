import subprocess
import sys
import os
import logging

# Setup basic logging
logging.basicConfig(filename='python_venv_setup.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def list_pythons():
    """List available Python installations with improved exception handling and security considerations."""
    try:
        command = ["where", "python"] if sys.platform.startswith('win') else ["which", "-a", "python", "python3"]
        logging.info(f"Executing command: {' '.join(command)}")
        paths = subprocess.check_output(command, text=True, shell=False).splitlines()  # shell=False for better security
        return paths
    except subprocess.CalledProcessError as e:
        logging.error(f"Error executing command: {e}")
        return []
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return []

def prompt_installation(pythons):
    """Prompt user for installation or selection with user feedback and logging."""
    if pythons:
        print("Found Python installations:")
        for idx, path in enumerate(pythons, start=1):
            print(f"{idx}. {path}")

        while True:
            answer = input('Choose which one you want to use by entering the number, or enter "n" for no installation: ').strip()
            if answer.lower() == 'n':
                print("No installation selected.")
                logging.info("User selected no installation.")
                return None
            elif answer.isdigit() and 1 <= int(answer) <= len(pythons):
                selected_path = pythons[int(answer) - 1]
                logging.info(f"User selected Python installation: {selected_path}")
                return selected_path
            else:
                print("Invalid selection. Please enter a valid number or 'n' to cancel.")
    else:
        print("No Python installations found.")
        logging.warning("No Python installations found.")
        choice = input("Would you like to install Python now? (yes/no): ")
        if choice.lower() in ['yes', 'y']:
            print("Please visit 'https://www.python.org/downloads/' to download and install Python.")
            logging.info("Directed user to download Python.")
        else:
            print("Python installation is required to proceed.")
            logging.info("User opted not to install Python.")
        return None

def check_virtual_env(venv_path):
    """Check if a virtual environment exists at the given path."""
    exists = os.path.exists(venv_path)
    logging.info(f"Checking if virtual environment exists at {venv_path}: {'Found' if exists else 'Not found'}")
    return exists

def create_virtual_env(python_executable, venv_path="venv"):
    """Create a virtual environment with progress indication, exception handling, and logging."""
    try:
        if not os.path.exists(venv_path):
            os.makedirs(venv_path)
            logging.info(f"Created directory for virtual environment: {venv_path}")
        print("Creating virtual environment. This may take a few moments...")
        result = subprocess.run([python_executable, "-m", "venv", venv_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode == 0:
            print(f"Virtual environment created successfully in {venv_path}")
            logging.info(f"Virtual environment created successfully in {venv_path}")
            return True
        else:
            print(f"Failed to create virtual environment: {result.stderr}")
            logging.error(f"Failed to create virtual environment: {result.stderr}")
            return False
    except Exception as e:
        print(f"An error occurred: {e}")
        logging.error(f"An error occurred while creating virtual environment: {e}")
        return False

def print_activation_instructions(venv_path):
    """Print instructions for activating the virtual environment."""
    if sys.platform == "win32":
        activation_command = f"{venv_path}\\Scripts\\activate.bat"
    else:
        activation_command = f"source {venv_path}/bin/activate"
    print(f"To activate the virtual environment, run: {activation_command}")
    logging.info(f"Provided activation instructions for virtual environment: {activation_command}")

def setup_python_virtual_env(venv_path="venv"):
    """Setup Python virtual environment with enhanced logging and user feedback."""
    logging.info("Starting setup of Python virtual environment.")
    if check_virtual_env(venv_path):
        print(f"Virtual environment already exists at '{venv_path}'.")
    else:
        pythons = list_pythons()
        selected_python = prompt_installation(pythons)
        if selected_python:
            print(f"Creating virtual environment using {selected_python} at '{venv_path}'...")
            if create_virtual_env(selected_python, venv_path):
                print("Virtual environment created successfully.")
                print_activation_instructions(venv_path)
                logging.info(f"Virtual environment setup completed successfully using {selected_python}.")
                print('\n You might want to select venv as your virtual environment in pycharm in interpreter settings for your current python project ')

if __name__ == "__main__":
    setup_python_virtual_env()
