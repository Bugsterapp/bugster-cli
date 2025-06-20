import subprocess
import sys

import requests
import typer
from packaging.version import parse as parse_version
from rich.console import Console

from bugster import __version__

console = Console()

GITHUB_REPO = "Bugsterapp/bugster-cli"
LATEST_RELEASE_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
INSTALL_SCRIPT_URL = (
    f"https://github.com/{GITHUB_REPO}/releases/latest/download/install.sh"
)


def _get_latest_version():
    """Fetches the latest version from GitHub releases."""
    try:
        response = requests.get(LATEST_RELEASE_URL, timeout=10)
        response.raise_for_status()
        # The tag name can be like 'v0.3.4'
        return response.json()["tag_name"].lstrip("v")
    except requests.RequestException as e:
        console.print(f"Error fetching latest version: {e}", style="bold red")
        raise typer.Exit(1)
    except (KeyError, IndexError):
        console.print("Could not find version in GitHub release.", style="bold red")
        raise typer.Exit(1)


def upgrade_command(yes: bool = False):
    """Updates Bugster CLI to the latest version."""
    console.print("Checking for updates...", style="yellow")

    current_version_str = __version__
    latest_version_str = _get_latest_version()

    if not latest_version_str:
        return

    current_version = parse_version(current_version_str)
    latest_version = parse_version(latest_version_str)

    if current_version < latest_version:
        console.print(
            f"A new version of Bugster CLI is available: [bold green]v{latest_version}[/bold green] (you have v{current_version})."
        )
        if yes or typer.confirm("Do you want to upgrade?", default=True):
            console.print("Upgrading Bugster CLI...", style="yellow")
            try:
                install_command = f"curl -sSL {INSTALL_SCRIPT_URL} | bash -s -- -y"
                # We use -y to auto-confirm any prompts from the install script
                process = subprocess.run(
                    install_command,
                    shell=True,
                    check=True,
                    capture_output=True,
                    text=True,
                )
                if process.returncode == 0:
                    console.print(process.stdout)
                    console.print(
                        "Bugster CLI has been updated successfully!", style="bold green"
                    )
                    console.print(
                        "Please restart your terminal for the changes to take effect."
                    )
                else:
                    console.print("Upgrade failed:", style="bold red")
                    console.print(process.stderr)
            except subprocess.CalledProcessError as e:
                console.print("Upgrade failed:", style="bold red")
                console.print(e.stderr)
                raise typer.Exit(1)
    else:
        console.print(
            f"You are already using the latest version of Bugster CLI (v{current_version}).",
            style="bold green",
        ) 