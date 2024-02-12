from pyprojectsetup.hlp_package import get_unique_packages_from_filepath, categorize_packages, update_requirements_txt
import os

if __name__ == '__main__':
    #%%----------------------------------------------------------------
    # Get all unique package from filepath
    filepath  = '../' # filepath to look
    flag_verbose = False # make it extra talkative about which file import which package
    excluded_folders = ['venv', 'build'] # folder that don't need to be looked for packages
    additional_exclude_packages = [] # additional packages that you dont want to add (native python one for exemple)
    packages = get_unique_packages_from_filepath(filepath=filepath, excluded_folders=excluded_folders, flag_verbose=flag_verbose, additional_exclude_packages=additional_exclude_packages)
    pypi_packages, localpy_packages, undetermined_packages = categorize_packages(packages)

    print("Looking into  :", os.path.abspath(filepath))
    print("Local Python Files used :", localpy_packages)
    print("Undetermined Packages (either native to python or homemade) :", undetermined_packages)
    print("PyPI Packages to put into requirements.txt : \n")
    for item in pypi_packages:
        print(item)


    print("Updating requirements.txt : \n")
    update_requirements_txt(pypi_packages, './requirements.txt')
