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


def download_and_extract(version):
    """Download and extract the appropriate asset for the current platform."""
    system = platform.system()
    temp_dir = tempfile.mkdtemp()

    print_step(f"Downloading Bugster CLI {version} for {system}...")

    # Determine the correct asset name for the current platform
    if system == "Windows":
        asset_name = "bugster-windows.zip"
    elif system == "Darwin":  # macOS
        # Detect macOS architecture
        machine = platform.machine().lower()
        if machine in ["x86_64", "amd64"]:
            asset_name = "bugster-macos-intel.zip"
        elif machine in ["arm64", "aarch64"]:
            asset_name = "bugster-macos-arm64.zip"
        else:
            print_warning(f"Unknown macOS architecture: {machine}, defaulting to Intel")
            asset_name = "bugster-macos-intel.zip"
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


def add_to_path_windows(install_dir):
    """Add directory to PATH on Windows."""
    try:
        import winreg

        # Open the user environment variables registry key
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_ALL_ACCESS
        )

        try:
            # Get current PATH value
            current_path, _ = winreg.QueryValueEx(key, "PATH")
        except FileNotFoundError:
            # PATH doesn't exist, create it
            current_path = ""

        # Check if the directory is already in PATH
        if install_dir in current_path.split(os.pathsep):
            print_success(f"✅ {install_dir} is already in PATH")
            winreg.CloseKey(key)
            return True

        # Add the directory to PATH
        if current_path:
            new_path = f"{current_path}{os.pathsep}{install_dir}"
        else:
            new_path = install_dir

        winreg.SetValueEx(key, "PATH", 0, winreg.REG_EXPAND_SZ, new_path)
        winreg.CloseKey(key)

        # Notify Windows of environment change
        run_command(
            "powershell -Command \"& {[Environment]::SetEnvironmentVariable('PATH', [Environment]::GetEnvironmentVariable('PATH', 'User'), 'User')}\""
        )

        print_success(f"✅ Added {install_dir} to PATH")
        return True

    except ImportError:
        print_error("winreg module not available")
        return False
    except Exception as e:
        print_error(f"Error adding to PATH on Windows: {e}")
        return False


def add_to_path_unix(install_dir):
    """Add directory to PATH on Unix-like systems."""
    shell = os.environ.get("SHELL", "/bin/bash")
    home_dir = os.path.expanduser("~")

    # Determine which shell config file to update
    if "zsh" in shell:
        config_files = [".zshrc", ".zprofile"]
    elif "bash" in shell:
        config_files = [".bashrc", ".bash_profile", ".profile"]
    elif "fish" in shell:
        config_files = [".config/fish/config.fish"]
    else:
        config_files = [".profile"]  # Fallback

    # Try to find an existing config file
    config_file = None
    for cf in config_files:
        full_path = os.path.join(home_dir, cf)
        if os.path.exists(full_path):
            config_file = full_path
            break

    # If no config file exists, create the first one in the list
    if config_file is None:
        config_file = os.path.join(home_dir, config_files[0])
        # Create directory if needed (for fish config)
        os.makedirs(os.path.dirname(config_file), exist_ok=True)

    try:
        # Check if PATH export already exists
        path_export = f'export PATH="$PATH:{install_dir}"'

        if os.path.exists(config_file):
            with open(config_file, "r") as f:
                content = f.read()
                if install_dir in content:
                    print_success(
                        f"✅ {install_dir} is already in PATH (found in {config_file})"
                    )
                    return True

        # Add PATH export to config file
        with open(config_file, "a") as f:
            f.write(f"\n# Added by Bugster CLI installer\n{path_export}\n")

        print_success(f"✅ Added {install_dir} to PATH in {config_file}")
        return True

    except Exception as e:
        print_error(f"Error adding to PATH: {e}")
        return False


def add_to_path(install_dir):
    """Add installation directory to PATH."""
    print_step("Adding installation directory to PATH...")

    system = platform.system()

    if system == "Windows":
        return add_to_path_windows(install_dir)
    else:
        return add_to_path_unix(install_dir)


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


def ensure_python310():
    """Ensure Python 3.10 is available and set as default."""
    current_version = sys.version_info[:2]
    if current_version >= MINIMUM_PYTHON_VERSION:
        return True, sys.executable

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

    # Ensure we have Python 3.10
    python_ok, python_path = ensure_python310()
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

        # Add to PATH (unless --no-path is specified)
        install_dir = os.path.dirname(installed_path)
        path_added = False
        path_added = add_to_path(install_dir)

        # Test installation, but skip if we're in an upgrade
        if os.environ.get("BUGSTER_UPGRADE_IN_PROGRESS"):
            print_step("Skipping installation test during upgrade process.")
        elif not test_installation(installed_path, version):
            sys.exit(1)

        # Print installation success message
        print_success("\n🎉 Bugster CLI has been installed successfully!")
        
        # Check if we're in an interactive environment
        import sys
        is_interactive = sys.stdin.isatty()
        
        if is_interactive:
            # Only ask for terminal reset if we're in an interactive environment
            print_warning("\nWould you like to reset your terminal? (y/n)")
            try:
                choice = input().strip().lower()
                
                if choice in ["y", "yes"]:
                    print_step("Resetting terminal...")
                    print("\nTo start using Bugster CLI, run:")
                    print("  bugster --help")
                    import signal
                    system = platform.system()
                    if system == "Windows":
                        # On Windows, just exit gracefully
                        print_warning("Please restart your command prompt manually.")
                        sys.exit(0)
                    else:
                        # On Unix systems, kill the parent process
                        os.kill(os.getppid(), signal.SIGKILL)
                else:
                    # Show restart instructions only if user chose not to reset
                    print("\nTo start using Bugster CLI, restart terminal and run:")
                    print("  bugster --help")
                    system = platform.system()
                    if system == "Windows":
                        print_warning("\nPlease restart your terminal to use Bugster CLI.")
                    else:
                        # Determine config file for Unix systems
                        shell = os.environ.get("SHELL", "/bin/bash")
                        home_dir = os.path.expanduser("~")
                        if "zsh" in shell:
                            config_files = [".zshrc", ".zprofile"]
                        elif "bash" in shell:
                            config_files = [".bashrc", ".bash_profile", ".profile"]
                        elif "fish" in shell:
                            config_files = [".config/fish/config.fish"]
                        else:
                            config_files = [".profile"]

                        config_file = None
                        for cf in config_files:
                            full_path = os.path.join(home_dir, cf)
                            if os.path.exists(full_path):
                                config_file = full_path
                                break

                        if config_file:
                            print_warning(f"\nPlease restart your terminal to use Bugster CLI or run:")
                            print(f"    source {config_file}")
                        else:
                            print_warning("\nPlease restart your terminal to use Bugster CLI.")
            except (EOFError, KeyboardInterrupt):
                # Handle non-interactive environments gracefully
                print("\nTo start using Bugster CLI, restart terminal and run:")
                print("  bugster --help")
        else:
            # Non-interactive environment (like curl), just show instructions
            print("\nTo start using Bugster CLI, restart terminal and run:")
            print("  bugster --help")
            system = platform.system()
            if system == "Windows":
                print_warning("\nPlease restart your terminal to use Bugster CLI.")
            else:
                # Determine config file for Unix systems
                shell = os.environ.get("SHELL", "/bin/bash")
                home_dir = os.path.expanduser("~")
                if "zsh" in shell:
                    config_files = [".zshrc", ".zprofile"]
                elif "bash" in shell:
                    config_files = [".bashrc", ".bash_profile", ".profile"]
                elif "fish" in shell:
                    config_files = [".config/fish/config.fish"]
                else:
                    config_files = [".profile"]

                config_file = None
                for cf in config_files:
                    full_path = os.path.join(home_dir, cf)
                    if os.path.exists(full_path):
                        config_file = full_path
                        break

                if config_file:
                    print_warning(f"\nPlease restart your terminal to use Bugster CLI or run:")
                    print(f"    source {config_file}")
                else:
                    print_warning("\nPlease restart your terminal to use Bugster CLI.")

    finally:
        # Clean up
        cleanup(temp_dir)


if __name__ == "__main__":
    main()
