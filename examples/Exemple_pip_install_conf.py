from pyprojectsetup.hpl_pip_install import install_requirements, clone_and_install_package, pip_install,install_requirements_onepackage_at_a_time

if __name__ == '__main__':
    #%% install requirements.txt
    # Example usage
    requirements_path = './requirements.txt'  # Update this path
    install_requirements_onepackage_at_a_time(requirements_path)

    # #%% install homemade packages from git networks
    # repo_branch_pairs = r'\\172.29.192.2\git\ToolboxSD\toolkitsd'
    # clone_and_install_package(repo_branch_pairs)
    #
    # # %% install homemade packages from local folder
    # print('\n Trying local install')
    # local_package = r'..\..\..\pyprojectsetup'
    # pip_install(local_package, flag_verbose=True)
    #
    # print('\n Trying local install developper mode')
    # pip_install(local_package, '-e', flag_verbose=True)