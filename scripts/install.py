#!/usr/bin/env python3
"""
Cross-platform installer for Bugster CLI
Can be run directly:
    python install.py [--version VERSION]

Or via curl:
    curl -sSL https://raw.githubusercontent.com/Bugsterapp/bugster-cli/main/scripts/install.py | python3 - --version VERSION
"""
import argparse
import os
import platform
import subprocess
import sys
import tempfile
import zipfile
import shutil
import json
import ssl
import re
from urllib.request import Request, urlopen
from urllib.error import URLError

# Disable SSL certificate verification
ssl._create_default_https_context = ssl._create_unverified_context

# ANSI color codes
BLUE = "\033[94m"
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"

# Constants
GITHUB_REPO = "https://github.com/Bugsterapp/bugster-cli"
GITHUB_API = "https://api.github.com/repos/Bugsterapp/bugster-cli"
DEFAULT_VERSION = "v0.1.0"
REQUIRED_PYTHON_VERSION = (3, 12)
MINIMUM_PYTHON_VERSION = (3, 10)


def print_step(message):
    """Print a step message."""
    print(f"\n{BLUE}=> {message}{RESET}")


def print_error(message):
    """Print an error message."""
    print(f"{RED}{message}{RESET}")


def print_success(message):
    """Print a success message."""
    print(f"{GREEN}{message}{RESET}")


def print_warning(message):
    """Print a warning message."""
    print(f"{YELLOW}{message}{RESET}")


def run_command(command, check=True, shell=True):
    """Run a shell command and print its output."""
    try:
        result = subprocess.run(
            command,
            shell=shell,
            check=check,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return result
    except subprocess.CalledProcessError as e:
        print_error(f"Error executing command: {command}")
        print_error(f"Error output: {e.stderr}")
        return None


def is_development_version(version):
    """Check if the version is a development version (beta, rc, alpha)."""
    return bool(re.search(r"-beta|-rc|-alpha", version))


def get_api_endpoint(version):
    """Get the API endpoint based on version."""
    if is_development_version(version):
        return "dev.bugster.api"
    return "api.bugster.app"


def validate_version(version):
    """Validate version format."""
    if version == "latest":
        return True
    if not re.match(r"^v\d+\.\d+\.\d+(-beta\.\d+|-rc\.\d+|-alpha\.\d+)?$", version):
        print_error("Invalid version format. Examples of valid versions:")
        print("  - v0.2.8")
        print("  - v0.2.8-beta.1")
        print("  - v0.2.8-rc.1")
        print("  - v0.2.8-alpha.1")
        print("  - latest")
        return False
    return True


def get_latest_version():
    """Get the latest version from GitHub."""
    print_step("Checking for latest version...")

    try:
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        request = Request(f"{GITHUB_API}/releases/latest", headers=headers)

        with urlopen(request) as response:
            release = json.loads(response.read())

        if release:
            tag = release["tag_name"]
            print_success(f"Latest version is {tag}")
            return tag
    except URLError as e:
        print_error(f"Error fetching latest version: {e}")
        print_warning(
            "Network connection error. Please check your internet connection."
        )
    except Exception as e:
        print_error(f"Error fetching latest version: {e}")

    print_warning(f"Using default version: {DEFAULT_VERSION}")
    return DEFAULT_VERSION


def check_version_exists(version):
    """Check if the specified version exists in GitHub releases."""
    try:
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        request = Request(f"{GITHUB_API}/releases/tags/{version}", headers=headers)

        with urlopen(request) as response:
            return response.getcode() == 200
    except URLError:
        return False


def download_with_progress(url, destination):
    """Download a file with progress indicator."""
    try:
        with urlopen(url) as response:
            total_size = int(response.headers.get("content-length", 0))
            block_size = 8192
            current_size = 0

            with open(destination, "wb") as f:
                while True:
                    block = response.read(block_size)
                    if not block:
                        break
                    current_size += len(block)
                    f.write(block)

                    if total_size > 0:
                        progress = current_size / total_size * 100
                        print(f"\rDownloading... {progress:.1f}%", end="", flush=True)

            print("\rDownload complete!      ")
            return True
    except Exception as e:
        print_error(f"\nError during download: {e}")
        return False


def find_python_executable():
    """Find the best available Python executable."""
    system = platform.system()
    paths = []

    if system == "Windows":
        # Windows-specific paths
        local_app_data = os.environ.get("LOCALAPPDATA", "")
        program_files = os.environ.get("PROGRAMFILES", "")
        program_files_x86 = os.environ.get("PROGRAMFILES(x86)", "")
        paths.extend(
            [
                os.path.join(
                    local_app_data, "Programs", "Python", "Python312", "python.exe"
                ),
                os.path.join(program_files, "Python312", "python.exe"),
                os.path.join(program_files_x86, "Python312", "python.exe"),
                os.path.join(
                    local_app_data, "Microsoft", "WindowsApps", "python3.12.exe"
                ),
            ]
        )
    else:
        # Unix-like systems (macOS/Linux)
        paths.extend(
            [
                "/usr/local/bin/python3.12",
                "/usr/bin/python3.12",
                "/opt/homebrew/bin/python3.12",
            ]
        )

    # Add common paths
    paths.extend(
        [
            "python3.12",
            "python3.11",
            "python3.10",
            "python3",
            "python",
        ]
    )

    for path in paths:
        try:
            if system == "Windows" and os.path.exists(path):
                result = run_command(f'"{path}" --version', check=False)
            else:
                result = run_command(
                    f"command -v {path} && {path} --version", check=False
                )

            if result and result.returncode == 0:
                version_str = result.stdout.strip()
                if "Python" in version_str:
                    version = tuple(map(int, version_str.split()[1].split(".")))
                    if version >= MINIMUM_PYTHON_VERSION:
                        return path, version
        except Exception:
            continue

    return None, None


def download_and_extract(version):
    """Download and extract the appropriate asset for the current platform."""
    system = platform.system()
    temp_dir = tempfile.mkdtemp()

    print_step(f"Downloading Bugster CLI {version} for {system}...")

    # Determine the correct asset name for the current platform
    if system == "Windows":
        asset_name = "bugster-windows.zip"
    elif system == "Darwin":  # macOS
        asset_name = "bugster-macos.zip"
    elif system == "Linux":
        asset_name = "bugster-linux.zip"
    else:
        print_error(f"Unsupported platform: {system}")
        sys.exit(1)

    # Download the asset
    zip_path = os.path.join(temp_dir, "bugster.zip")
    download_url = f"{GITHUB_REPO}/releases/download/{version}/{asset_name}"

    try:
        print(f"Downloading from {download_url}...")
        if not download_with_progress(download_url, zip_path):
            raise Exception("Download failed")
    except Exception as e:
        print_error(f"Error downloading release: {e}")
        print_error(f"Check if {asset_name} exists for version {version}")
        sys.exit(1)

    # Extract the zip file
    try:
        print_step("Extracting files...")
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(temp_dir)
    except Exception as e:
        print_error(f"Error extracting zip file: {e}")
        sys.exit(1)

    # Find the executable
    if system == "Windows":
        exe_path = os.path.join(temp_dir, "bugster.exe")
    else:
        exe_path = os.path.join(temp_dir, "bugster")

    # Make sure the file exists and is executable
    if not os.path.exists(exe_path):
        print_error("Could not find executable in zip file")
        print_error(f"Expected path: {exe_path}")
        sys.exit(1)

    if system != "Windows":
        os.chmod(exe_path, 0o755)  # Make executable on Unix systems

    return exe_path, temp_dir


def install_executable(executable_path):
    """Install the Bugster CLI executable."""
    system = platform.system()

    # Determine installation directory
    if system == "Windows":
        install_dir = os.path.join(
            os.environ.get("LOCALAPPDATA", ""), "Programs", "bugster"
        )
    else:
        install_dir = os.path.expanduser("~/.local/bin")

    # Create installation directory if it doesn't exist
    os.makedirs(install_dir, exist_ok=True)

    # Determine target path
    if system == "Windows":
        target_path = os.path.join(install_dir, "bugster.exe")
    else:
        target_path = os.path.join(install_dir, "bugster")

    # Copy executable to installation directory
    try:
        shutil.copy2(executable_path, target_path)
        if system != "Windows":
            os.chmod(target_path, 0o755)
        print_success(f"✅ Installed Bugster CLI to {target_path}")
        return target_path
    except Exception as e:
        print_error(f"Error installing executable: {e}")
        return None


def test_installation(executable_path, version):
    """Test the Bugster CLI installation."""
    print_step("Testing installation...")

    try:
        result = run_command(f'"{executable_path}" --version')
        if result and result.returncode == 0:
            installed_version = result.stdout.strip()
            print_success(f"✅ Bugster CLI {installed_version} installed successfully!")
            return True
    except Exception as e:
        print_error(f"Error testing installation: {e}")

    return False


def cleanup(temp_dir):
    """Clean up temporary files."""
    try:
        shutil.rmtree(temp_dir)
    except Exception:
        pass


def ensure_python312():
    """Ensure Python 3.12 is available and set as default."""
    current_version = sys.version_info[:2]
    if current_version >= REQUIRED_PYTHON_VERSION:
        return True, sys.executable

    # Find best available Python
    python_path, python_version = find_python_executable()

    if python_path and python_version >= REQUIRED_PYTHON_VERSION:
        return True, python_path
    elif python_version and python_version >= MINIMUM_PYTHON_VERSION:
        print_warning(
            f"Using Python {'.'.join(map(str, python_version))} (Python {'.'.join(map(str, REQUIRED_PYTHON_VERSION))} recommended)"
        )
        return True, python_path

    print_error(
        f"Python {'.'.join(map(str, MINIMUM_PYTHON_VERSION))} or higher is required"
    )
    print_error(
        "Please install Python using your system's package manager or download from python.org"
    )
    return False, None


def main():
    """Main installation function."""
    parser = argparse.ArgumentParser(description="Bugster CLI installer")
    parser.add_argument(
        "-v", "--version", default="latest", help="Version to install (e.g., v0.2.8)"
    )
    args = parser.parse_args()

    # Validate version format
    if not validate_version(args.version):
        sys.exit(1)

    # Ensure we have Python 3.12 (or at least 3.10)
    python_ok, python_path = ensure_python312()
    if not python_ok:
        sys.exit(1)

    # Get version to install
    version = args.version
    if version == "latest":
        version = get_latest_version()

    # Check if version exists
    if not check_version_exists(version):
        print_error(f"Version {version} not found")
        sys.exit(1)

    # Download and extract
    executable_path, temp_dir = download_and_extract(version)

    try:
        # Install executable
        installed_path = install_executable(executable_path)
        if not installed_path:
            sys.exit(1)

        # Test installation
        if not test_installation(installed_path, version):
            sys.exit(1)

        # Print installation success message
        print_success("\nBugster CLI has been installed successfully!")
        print_warning("\nMake sure the installation directory is in your PATH:")
        if platform.system() == "Windows":
            print(f"  {os.path.dirname(installed_path)}")
        else:
            print("  ~/.local/bin")

        print("\nTo start using Bugster CLI, run:")
        print("  bugster --help")

    finally:
        # Clean up
        cleanup(temp_dir)


if __name__ == "__main__":
    main()
