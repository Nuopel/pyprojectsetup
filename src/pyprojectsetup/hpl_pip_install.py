import subprocess
import sys
import shutil
from pathlib import Path
import os
import logging
import subprocess
import importlib

# Ensure the logging is configured; this might be better placed in your main script or a setup function
logging.basicConfig(level=logging.INFO)

def exec_command(command):
    try:
        subprocess.run(command, check=True)
        logging.info(f"{command} : successful")
    except subprocess.CalledProcessError as e:
        logging.error(f"Error with: {command} {e}")



def install_requirements_onepackage_at_a_time(requirements_path):
    """
    Install packages from a requirements.txt file one package at a time.

    :param requirements_path: Path to the requirements.txt file
    """
    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

    try:
        # Validate requirements file path
        if not os.path.isfile(requirements_path):
            raise FileNotFoundError(f"Requirements file not found at {requirements_path}")

        # Open and read the requirements.txt file
        with open(requirements_path, 'r') as file:
            packages = [package.strip() for package in file.readlines() if package.strip()]

        # Lists to store successful and unsuccessful installations
        successful_installs = []
        unsuccessful_installs = []

        # Install each package using pip
        for package in packages:
            try:
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
                successful_installs.append(package)
                logger.info(f"Successfully installed package: {package}")
            except subprocess.CalledProcessError:
                unsuccessful_installs.append(package)
                logger.error(f"Failed to install package: {package}")

        # Print summary
        logger.info("Installation summary:")
        logger.info(f"Total packages installed: {len(successful_installs)}")
        if successful_installs:
            logger.info("Successfully installed packages:")
            for package in successful_installs:
                logger.info(package)
        if unsuccessful_installs:
            logger.error("Failed to install the following packages:")
            for package in unsuccessful_installs:
                # Attempt to import the package
                try:
                    package_name = package.split('==')[0]  # Extract package name, ignore version
                    importlib.import_module(package_name)
                    logger.info(f"{package} but it is already present in the Python environment.")
                except ImportError:
                    # If import fails, then the package is genuinely missing
                    logger.error(package)

    except FileNotFoundError as e:
        logger.error(e)
    except Exception as e:
        logger.error(f"An error occurred: {e}")



def install_requirements(requirements_path):
    """
    Install packages from a requirements.txt file using `pip install -r`.

    :param requirements_path: Path to the requirements.txt file
    """
    try:
        # Execute pip install command
        requirements_path = os.path.abspath(requirements_path)  # Get the absolute path
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', requirements_path])
        logging.info(f"Packages from {requirements_path} installed successfully.")
    except subprocess.CalledProcessError as e:
        logging.error(f"An error occurred during package installation: {e}")
    except FileNotFoundError:
        logging.error(f"The file {requirements_path} was not found.")




def pip_install(package, *pip_args, flag_verbose=False):
    """
    Install a Python package using pip with optional arguments. Improved handling for '-e' (editable mode).

    Args:
        package (str): The name of the package to install. Can include '-e' for editable installations.
        *pip_args (str): Optional arguments to pass to the 'pip install' command.

    Returns:
        bool: True if installation was successful, False otherwise.
    """
    try:
        pip_command = [sys.executable, "-m", "pip", "install"]

        # Check if '-e' is in pip_args instead of the package string
        if '-e' in pip_args:
            # Remove '-e' from pip_args and ensure it's added to pip_command
            pip_args = list(pip_args)
            pip_args.remove('-e')
            pip_command.append('-e')

        # If '-e' is part of the package string
        elif ' -e ' in package or package.startswith('-e '):
            # Split the package string and extract '-e' and the package path
            parts = package.split()
            pip_command.append(parts[0])  # '-e'
            package = ' '.join(parts[1:])  # Remaining part is the package

        # Add the package name and any additional pip arguments
        pip_command.append(package)
        pip_command.extend(pip_args)

        # Execute the pip command
        result = subprocess.run(pip_command, capture_output=True, text=True)

        if result.returncode == 0:
            if flag_verbose:
                print(f"Installed package: {package}")
                if ' -e ' in pip_command:
                    print(f"Developper mode")

            return True
        else:
            # Optionally, log or handle errors using result.stderr
            print(f'Installation failed: {result.stderr}')
            return False
    except Exception as e:
        print(f'Error during installation: {e}')
        return False



def clone_and_install_package(pair, dev_mode=False, destination_folder=False):
    # Determine if pair is a tuple of (repository_url, branch_name) or just repository_url
    if isinstance(pair, tuple) and len(pair) == 2:
        repository_url, branch_name = pair
    else:
        repository_url = pair  # This handles when pair is just the URL
        branch_name = None  # This indicates no branch was explicitly provided

    print(f"Attempt to clone package: {repository_url}")
    # Use pathlib to handle the path extraction for package name
    package_name = Path(repository_url.split('/')[-1]).stem
    try:
        # Clone the repository with or without branch name and into the specified destination folder
        if branch_name:
            if destination_folder:
                exec_command(f"git clone {repository_url} --branch {branch_name} {destination_folder}/{package_name}")
            else:
                exec_command(f"git clone {repository_url} --branch {branch_name}")

        else:
            if destination_folder:
                exec_command(f"git clone {repository_url} {destination_folder}/{package_name}")
            else:
                exec_command(f"git clone {repository_url}")

    except Exception as e:
        print(f"Failed to clone package: {repository_url}, Error: {e}")
        return False



    # Install the package
    if dev_mode :
        if destination_folder:
            if pip_install(f"{destination_folder}/{package_name}", '-e'):
                print(f"Installed package: {package_name}, dev mode")
        else:
            if pip_install(f"./{package_name}", '-e'):
                print(f"Installed package: {package_name}, dev mode")

    else:
        if destination_folder:
            if pip_install(f"{destination_folder}/{package_name}"):
                print(f"Installed package: {package_name}")
        else:
            if pip_install(f"./{package_name}"):
                print(f"Installed package: {package_name}")

        # Remove the cloned directory using pathlib for cross-platform compatibility
        if destination_folder:
            shutil.rmtree(Path(f"{destination_folder}/{package_name}"))
        else:
            shutil.rmtree(Path(f"./{package_name}"))

        print(f"Removed folder: {package_name}")
    return True


def install_requirements_network_onepackage_at_a_time(requirements_path, dev_mode=False, destination_folder=False):
    """
    Install packages from a requirements.txt file one package at a time.

    :param requirements_path: Path to the requirements.txt file
    """
    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

    try:
        # Validate requirements file path
        if not os.path.isfile(requirements_path):
            raise FileNotFoundError(f"Requirements file not found at {requirements_path}")

        # Open and read the requirements.txt file
        with open(requirements_path, 'r') as file:
            packages = [package.strip() for package in file.readlines() if package.strip()]

        # Lists to store successful and unsuccessful installations
        successful_installs = []
        unsuccessful_installs = []

        # Install each package using pip
        for package in packages:
            try:
                clone_and_install_package(package, dev_mode=dev_mode, destination_folder=destination_folder)
                successful_installs.append(package)
                logger.info(f"Successfully installed package: {package}")
            except subprocess.CalledProcessError:
                unsuccessful_installs.append(package)
                logger.error(f"Failed to install package: {package}")

        # Print summary
        logger.info("Installation summary:")
        logger.info(f"Total packages installed: {len(successful_installs)}")
        if successful_installs:
            logger.info("Successfully installed packages:")
            for package in successful_installs:
                logger.info(package)
        if unsuccessful_installs:
            logger.error("Failed to install the following packages:")
            for package in unsuccessful_installs:
                # Attempt to import the package
                try:
                    package_name = package.split('==')[0]  # Extract package name, ignore version
                    importlib.import_module(package_name)
                    logger.info(f"{package} but it is already present in the Python environment.")
                except ImportError:
                    # If import fails, then the package is genuinely missing
                    logger.error(package)

    except FileNotFoundError as e:
        logger.error(e)
    except Exception as e:
        logger.error(f"An error occurred: {e}")

if __name__ == '__main__':
    #%% install requirements.txt
    # Example usage
    requirements_path = './requirements.txt'  # Update this path
    install_requirements(requirements_path)

    #%% install homemade packages in git network
    print('\n Trying git network install')
    repo_branch_pairs = r'\\172.29.192.2\git\ToolboxSD\toolkitsd'
    clone_and_install_package(repo_branch_pairs)

    #%% install homemade packages from local folder
    print('\n Trying local install')
    local_package = r'..\..\..\pyprojectsetup'
    pip_install(local_package, flag_verbose=True)

    print('\n Trying local install developper mode')
    pip_install(local_package, '-e' , flag_verbose=True)