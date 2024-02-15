import ast
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
import os
import glob

def find_files(path, pattern, excluded_folders = None):
    """
    Find a matching file pattern in a specified folder looking in all subfolder.

    Args:
        path: path to look ex : './folder'
        pattern: pattern of the file to look '*.json'

    Returns: list of the different matching file

    """

    def exclude_partial_match(folder_list, partial_matches):
        """
        Exclude folders with names containing any of the partial matches from a list of folders.

        :param folder_list: List of folder paths
        :param partial_matches: List of partial match strings to exclude
        :return: Filtered list of folders
        """
        filtered_folders = [folder for folder in folder_list if
                            all(partial not in folder for partial in partial_matches)]
        return filtered_folders
    files = []

    if type(pattern) is list:
        for pattern_item in pattern:
            for root, dirs, filenames in os.walk(path):
                for filename in glob.fnmatch.filter(filenames, pattern_item):
                    files.append(os.path.join(root, filename))
    else:
        for root, dirs, filenames in os.walk(path):
            for filename in glob.fnmatch.filter(filenames, pattern):
                files.append(os.path.join(root, filename))

    if excluded_folders is not None:
       files = exclude_partial_match(files, excluded_folders)
    return files

def collect_imports(node):
    """
    Collects the names of modules and specific symbols imported by an AST node.

    This function checks if the provided AST node represents an import statement. If the node is an `ast.Import`, it returns a list of imported module names. If the node is an `ast.ImportFrom`, it returns a list of strings that combine the module name with the imported symbols' names, in the format "module.symbol".

    Args:
        node (ast.AST): The AST node to analyze for import statements.

    Returns:
        list of str: A list of strings representing the names of imported modules or symbols. If the node is not an import statement, the function returns an empty list.

    Example:
        Given an `ast.Import` node for `import os, sys`, this function will return `['os', 'sys']`.
        Given an `ast.ImportFrom` node for `from collections import defaultdict`, this function will return `['collections.defaultdict']`.
    """
    if isinstance(node, ast.Import):
        return [name.name for name in node.names]
    elif isinstance(node, ast.ImportFrom):
        return [f"{node.module}.{name.name}" for name in node.names]

def analyze_py_files(file_paths):
    """
    Analyzes Python files to extract imported modules and symbols.

    This function takes a list of file paths to Python files and analyzes each file to extract imported modules and symbols. For each file, it parses the file's Abstract Syntax Tree (AST) and collects import statements. The result is a dictionary where each key is the name of a Python file, and the corresponding value is a list of imported modules and symbols.

    Args:
        file_paths (List[str]): A list of file paths to Python (.py) files to analyze.

    Returns:
        Dict[str, List[str]]: A dictionary where keys are file names and values are lists of imported modules and symbols.

    Example:
        If `file_paths` contains ['example.py'], and 'example.py' contains the following code:
        ```python
        import os
        from collections import defaultdict
        from module import function
        ```
        The function will return:
        ```python
        {'example.py': ['os', 'collections.defaultdict', 'module.function']}
        ```

    Raises:
        FileNotFoundError: If a file specified in `file_paths` does not exist.
        PermissionError: If the function does not have permission to read a file specified in `file_paths`.
        SyntaxError: If a syntax error occurs while parsing a Python file.
        Other errors: Any other exceptions raised during file reading or parsing.
    """
    results = {}

    for file_path in file_paths:
        file_name = file_path.split('/')[-1]  # Extract the file name from the path
        imported_modules = []

        try:
            with open(file_path, 'r') as file:
                tree = ast.parse(file.read())

            for node in ast.walk(tree):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    imported_modules.extend(collect_imports(node))

            results[file_name] = imported_modules
        except Exception as e:
            results[file_name] = [f"Error analyzing file: {str(e)}"]

    return results

#%%
def get_unique_packages(imported_packages_dict):
    """
      Extracts unique root packages from a dictionary of imported packages.

      This function takes a dictionary where keys are file names and values are lists of imported packages. It extracts the unique root packages (the top-level package names) from all imported packages across all files.

      Args:
          imported_packages_dict (dict): A dictionary where keys are file names and values are lists of imported packages.

      Returns:
          list: A sorted list of unique root packages extracted from all imported packages.

      Example:
          If `imported_packages_dict` is {'file1.py': ['os', 'collections.defaultdict', 'module.function'], 'file2.py': ['numpy', 'os.path']}, the function will return ['collections', 'module', 'numpy', 'os'].

      Note:
          The function considers the root package as the first part of a package name before the first dot ('.') character.

      """
    def get_root_packages(imported_packages):
        root_packages = set()

        for package in imported_packages:
            root_package = package.split('.')[0]  # Extract the root package
            root_packages.add(root_package)

        return sorted(list(root_packages))  # Convert to list and sort

    all_imports = []

    # Merge all the imported packages into one list
    for imported_modules in imported_packages_dict.values():
        all_imports.extend(imported_modules)

    # Use set to remove duplicates and then convert back to a list
    unique_packages = list(set(all_imports))

    return get_root_packages(unique_packages)


def get_unique_packages_from_filepath(filepath, flag_exclude=True, additional_exclude_packages=None, excluded_folders = ['venv'], flag_verbose = False):
    """
    Extracts and returns a list of unique packages used in Python files within the specified directory.

    Args:
    - filepath (str): The file path where Python files are located.
    - flag_exclude (bool, optional): A flag to determine if default packages should be excluded. Defaults to True.
    - additional_exclude_packages (list of str, optional): Additional packages to exclude. Defaults to None.

    Returns:
    - list: A list of unique packages used in the Python files, excluding specified packages if flag_exclude is True.
    """

    file_paths = find_files(filepath, '*.py', excluded_folders=excluded_folders)
    results = analyze_py_files(file_paths)

    if flag_verbose:# Print the results
        for file_name, imported_modules in results.items():
            print(f"File: {file_name}")
            for module in imported_modules:
                print(f"  Import: {module}")

    unique_packages = get_unique_packages(results)

    exclude_packages = ['unittest','ast','os', 'math', 'cmath', 'glob', 'concurrent', 're', 'shutil', 'subprocess',
                        'sys'] # list of known packages from native python that should be excluded
    if additional_exclude_packages:
        exclude_packages.extend(additional_exclude_packages)

    if flag_exclude:
        excluded_packages = [pkg for pkg in exclude_packages if pkg in unique_packages]
        print(f"Excluded packages: {excluded_packages}")
        unique_packages = [pkg for pkg in unique_packages if pkg not in exclude_packages]

    return unique_packages

# check if package are homemade or existing
def check_pypi(package_name):
    """Check if a package is available on PyPI."""
    try:
        response = requests.get(f"https://pypi.org/pypi/{package_name}/json", timeout=5)
        return package_name, response.status_code == 200
    except requests.RequestException:
        return package_name, False

def categorize_packages(package_names, filepath = '.'):
    """Categorize packages into PyPI, local Python files, or undetermined."""
    pypi_packages = []
    undetermined_packages = []

    # Check for local Python files first to reduce unnecessary PyPI checks
    all_files = {f[:-3] for f in os.listdir(filepath) if os.path.isfile(filepath+f) and f.endswith('.py')}
    localpy_packages = [name for name in package_names if name in all_files]

    # Prepare a list for PyPI checks excluding those already found locally
    remaining_checks = [name for name in package_names if name not in all_files]

    # Concurrently check remaining packages on PyPI
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_package = {executor.submit(check_pypi, pkg): pkg for pkg in remaining_checks}
        for future in as_completed(future_to_package):
            package_name, is_pypi = future.result()
            if is_pypi:
                pypi_packages.append(package_name)
            else:
                undetermined_packages.append(package_name)

    return pypi_packages, localpy_packages, undetermined_packages

def update_requirements_txt(dependencies, requirements_path):
    """
    Updates a requirements.txt file with new dependencies.

    This function takes a list of dependencies extracted from project files and compares them to the packages listed
    in a requirements.txt file. If any new packages are found in the dependencies that are not already listed in the
    requirements.txt file, the user is prompted to add them to the file.

    Args:
        dependencies (list): A list of imported packages extracted from project files.
        requirements_path (str): The file path to the requirements.txt file to update.

    Returns:
        None

    Example:
        Given `dependencies` as ['os', 'numpy', 'requests'], and the contents of
        requirements.txt as:
        ```
        numpy==1.21.0
        requests==2.26.0
        ```
        The function will prompt the user to add 'os' to requirements.txt, resulting in:
        ```
        numpy==1.21.0
        requests==2.26.0
        os
        ```

    """
    try:
        with open(requirements_path, 'r') as file:
            existing_packages = {line.strip() for line in file}

        new_packages = set(dependencies) - existing_packages

        if new_packages:
            print("The following packages are not listed in requirements.txt:")
            for package in new_packages:
                print(package)

            choice = input("Do you want to add them to requirements.txt? (y/n): ")
            if choice.lower() == 'y':
                with open(requirements_path, 'a') as file:
                    for package in new_packages:
                        file.write(f"{package}\n")
        else:
            print("No packages listed are missing in requirements.txt ")

    except FileNotFoundError:
        print(f"Error: requirements.txt file not found at {requirements_path}.")
    except Exception as e:
        print(f"An error occurred while updating requirements.txt: {e}")



if __name__ == '__main__':

    #%%----------------------------------------------------------------
    # Get unique package from src
    packages = get_unique_packages_from_filepath('../../',excluded_folders=['venv','build'])
    pypi_packages, localpy_packages, undetermined_packages = categorize_packages(packages)
    
    print("Local Python Files used :", localpy_packages)
    print("Undetermined Packages (either native to python or homemade) :", undetermined_packages)
    print("PyPI Packages to put into requirements.txt : \n")
    for item in pypi_packages:
        print(item)

    print("Updating requirements.txt : \n")
    update_requirements_txt(pypi_packages, './requirements.txt')
