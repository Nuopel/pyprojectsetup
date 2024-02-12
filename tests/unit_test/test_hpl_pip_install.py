import unittest
from unittest.mock import patch, MagicMock,mock_open, call
from unittest import TestCase
from pathlib import Path
import subprocess

import sys
import os
from pyprojectsetup.hpl_pip_install import exec_command, install_requirements, pip_install, clone_and_install_package, install_requirements_onepackage_at_a_time


class TestExec(unittest.TestCase):
    @patch('subprocess.run')
    def test_exec_command_success(self, mock_run):
        # Simulate a successful command execution
        mock_run.return_value = MagicMock(check_returncode=lambda: None)

        command = "git clone https://example.com/repo.git"
        with self.assertLogs(level='INFO') as captured:  # Ensure the correct log level
            exec_command(command)
            self.assertTrue(any("successful" in message for message in captured.output))
            mock_run.assert_called_with(command, check=True)

    @patch('subprocess.run')
    def test_exec_command_failure(self, mock_run):
        # Simulate a command execution failure
        mock_run.side_effect = subprocess.CalledProcessError(1, cmd="git clone https://example.com/repo.git")

        command = "git clone https://example.com/repo.git"
        with self.assertLogs() as captured:
            exec_command(command)
            self.assertIn("Error with:", captured.records[0].getMessage())
            mock_run.assert_called_with(command, check=True)


class TestInstallRequirements(unittest.TestCase):
    @patch('subprocess.check_call')
    def test_install_requirements_success(self, mock_check_call):
        # Simulate successful installation
        requirements_path = "requirements.txt"
        install_requirements(requirements_path)
        requirements_path = os.path.abspath(requirements_path)
        mock_check_call.assert_called_once_with([sys.executable, '-m', 'pip', 'install', '-r', requirements_path])

    @patch('subprocess.check_call')
    def test_install_requirements_called_process_error(self, mock_check_call):
        # Simulate a subprocess.CalledProcessError
        mock_check_call.side_effect = subprocess.CalledProcessError(1, 'cmd')

        with self.assertLogs() as captured:
            install_requirements("requirements.txt")
            self.assertIn("An error occurred during package installation", captured.records[0].getMessage())

    @patch('subprocess.check_call')
    def test_install_requirements_file_not_found_error(self, mock_check_call):
        # Simulate a FileNotFoundError
        mock_check_call.side_effect = FileNotFoundError
        requirements_path = "nonexistent_requirements.txt"
        requirements_path = os.path.abspath(requirements_path)
        with self.assertLogs() as captured:
            install_requirements(requirements_path)
            self.assertIn(f"The file {requirements_path} was not found.",
                          captured.records[0].getMessage())


class TestPipInstall(unittest.TestCase):
    @patch('subprocess.run')
    def test_pip_install_success(self, mock_run):
        # Simulate a successful pip command execution
        mock_run.return_value = MagicMock(returncode=0)

        result = pip_install("example-package")
        self.assertTrue(result)
        mock_run.assert_called_once_with([sys.executable, '-m', 'pip', 'install', 'example-package'], capture_output=True, text=True)

    @patch('subprocess.run')
    def test_pip_install_failure(self, mock_run):
        # Simulate a failed pip command execution
        mock_run.return_value = MagicMock(returncode=1, stderr="Error message")

        result = pip_install("example-package")
        self.assertFalse(result)
        mock_run.assert_called_once_with([sys.executable, '-m', 'pip', 'install', 'example-package'], capture_output=True, text=True)

    @patch('subprocess.run')
    def test_pip_install_editable_mode_in_args(self, mock_run):
        # Simulate a successful pip command execution in editable mode via arguments
        mock_run.return_value = MagicMock(returncode=0)

        result = pip_install("example-package", "-e")
        self.assertTrue(result)
        mock_run.assert_called_once_with([sys.executable, '-m', 'pip', 'install', '-e', 'example-package'], capture_output=True, text=True)

    @patch('subprocess.run')
    def test_pip_install_editable_mode_in_package(self, mock_run):
        # Simulate a successful pip command execution with editable mode in package string
        mock_run.return_value = MagicMock(returncode=0)

        result = pip_install("-e example-package")
        self.assertTrue(result)
        mock_run.assert_called_once_with([sys.executable, '-m', 'pip', 'install', '-e', 'example-package'], capture_output=True, text=True)

    @patch('subprocess.run')
    def test_pip_install_with_additional_args(self, mock_run):
        # Simulate a successful pip command execution with additional pip arguments
        mock_run.return_value = MagicMock(returncode=0)

        result = pip_install("example-package", "--upgrade")
        self.assertTrue(result)
        mock_run.assert_called_once_with([sys.executable, '-m', 'pip', 'install', 'example-package', '--upgrade'], capture_output=True, text=True)


class TestCloneAndInstallPackage(TestCase):
    @patch('pyprojectsetup.hpl_pip_install.exec_command')
    @patch('pyprojectsetup.hpl_pip_install.pip_install')
    def test_clone_and_install_without_branch(self, mock_pip_install, mock_exec):
        repository_url = "https://github.com/example/repo.git"
        mock_pip_install.return_value = True

        self.assertTrue(clone_and_install_package(repository_url))

        mock_exec.assert_called_once_with(f"git clone {repository_url}")
        mock_pip_install.assert_called_once_with(f"./repo")

    @patch('pyprojectsetup.hpl_pip_install.exec_command')
    @patch('pyprojectsetup.hpl_pip_install.pip_install')
    def test_clone_and_install_with_branch(self,  mock_pip_install, mock_exec):
        pair = ("https://github.com/example/repo.git", "develop")
        mock_pip_install.return_value = True

        self.assertTrue(clone_and_install_package(pair))

        mock_exec.assert_called_once_with("git clone https://github.com/example/repo.git --branch develop")
        mock_pip_install.assert_called_once_with(f"./repo")

    @patch('pyprojectsetup.hpl_pip_install.exec_command')  # Adjust the import path as necessary
    @patch('pyprojectsetup.hpl_pip_install.pip_install')
    @patch('shutil.rmtree')
    def test_clone_and_install_dev_mode(self, mock_rmtree, mock_pip_install, mock_exec):
        repository_url = "https://github.com/example/repo.git"
        mock_pip_install.return_value = True

        clone_and_install_package(repository_url, dev_mode=True)

        mock_exec.assert_called_once_with(f"git clone {repository_url}")
        mock_pip_install.assert_called_once_with("./repo", '-e')
        mock_rmtree.assert_called_once_with(Path("repo"))

class TestInstallRequirementsOneAtTime(unittest.TestCase):


    @patch('subprocess.check_call')
    @patch('os.path.isfile', return_value=True)
    @patch('builtins.open', new_callable=mock_open, read_data="package1\npackage2==0.1")
    def test_valid_requirements(self, mock_open, mock_isfile, mock_subprocess):
        install_requirements_onepackage_at_a_time('requirements.txt')
        # Check subprocess was called correctly for each package
        calls = [
            call([sys.executable, '-m', 'pip', 'install', 'package1']),
            call([sys.executable, '-m', 'pip', 'install', 'package2==0.1'])
        ]
        mock_subprocess.assert_has_calls(calls, any_order=True)


    @patch('subprocess.check_call', side_effect=[None, subprocess.CalledProcessError(1, 'cmd')])
    @patch('os.path.isfile', return_value=True)
    @patch('builtins.open', new_callable=mock_open, read_data="package1\npackage2")
    def test_installation_failure(self, mock_open, mock_isfile, mock_subprocess):
        install_requirements_onepackage_at_a_time('requirements.txt')
        # Here you could check if the logger was called with expected error messages
        # This would involve mocking the logger used in your function and verifying it was called correctly

# Add more tests here as needed

if __name__ == '__main__':
    unittest.main()
