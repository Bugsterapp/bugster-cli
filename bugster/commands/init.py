"""Initialize command implementation."""

import contextlib
import time
from pathlib import Path

import typer
import yaml
from loguru import logger
from rich.console import Console
from rich.prompt import Confirm, Prompt

from bugster.analytics import track_command
from bugster.clients.http_client import BugsterHTTPClient
from bugster.commands.auth import auth_command
from bugster.constants import (
    CONFIG_PATH,
    TESTS_DIR,
)
from bugster.libs.utils.git import get_git_prefix_path
from bugster.utils.console_messages import InitMessages
from bugster.utils.user_config import get_api_key

console = Console()


def create_credential_entry(
    identifier="admin",
    username="admin",
    password="admin",
):
    """Create a credential entry with a slug identifier."""
    return {
        "id": identifier.lower().replace(" ", "-"),
        "username": username,
        "password": password,
    }


def find_existing_config():
    """Find existing configuration in current or parent directories."""
    current_dir = Path.cwd()
    while current_dir != current_dir.parent:  # Stop at root directory
        config_path = current_dir / ".bugster" / "config.yaml"
        if config_path.exists():
            return True, config_path
        current_dir = current_dir.parent
    return False, None


def update_gitignore():
    """Update .gitignore with Bugster entries."""
    gitignore_path = Path(".gitignore")
    bugster_entries = [
        "# Bugster",
        ".bugster/results/",
        ".bugster/screenshots/",
        ".bugster/videos/",
        ".bugster/logs/",
        ".bugster/reports/",
        "*.bugster.log",
    ]

    # Read existing entries
    existing_entries = []
    if gitignore_path.exists():
        with open(gitignore_path) as f:
            existing_entries = f.read().splitlines()

    # Add missing entries
    with open(gitignore_path, "a") as f:
        if existing_entries and existing_entries[-1] != "":
            f.write("\n")  # Add newline if file doesn't end with one

        for entry in bugster_entries:
            if entry not in existing_entries:
                f.write(f"{entry}\n")


def generate_project_id(project_name: str) -> str:
    """Generate a project ID from project name."""
    # Use timestamp to ensure uniqueness
    timestamp = int(time.time())
    # Convert project name to lowercase and replace spaces with dashes
    safe_name = project_name.lower().replace(" ", "-")
    return f"{safe_name}-{timestamp}"


@track_command("init")
def init_command():
    """Initialize Bugster CLI configuration."""
    InitMessages.welcome()

    # First check if user is authenticated
    api_key = get_api_key()

    if not api_key:
        logger.info("API key not found, running auth command...")
        InitMessages.auth_required()

        # Run auth command
        auth_command()

        # Check if auth was successful
        api_key = get_api_key()

        if not api_key:
            InitMessages.auth_failed()
            raise typer.Exit(1)

        InitMessages.auth_success()

    # Check for existing configuration
    config_exists, existing_config_path = find_existing_config()

    if config_exists:
        if existing_config_path == CONFIG_PATH:
            if not Confirm.ask(
                InitMessages.get_existing_project_warning(), default=False
            ):
                InitMessages.initialization_cancelled()
                raise typer.Exit(0)
        else:
            current_dir = Path.cwd()
            project_dir = existing_config_path.parent.parent
            InitMessages.nested_project_error(current_dir, project_dir)
            raise typer.Exit(1)

    # Project setup
    InitMessages.project_setup()
    project_name = Prompt.ask("🏷️  Project name", default=Path.cwd().name)
    project_path = ""
    with contextlib.suppress(Exception):
        project_path = get_git_prefix_path()

    # Create project via API
    try:
        with BugsterHTTPClient() as client:
            client.set_headers({"x-api-key": api_key})
            InitMessages.creating_project()

            project_data = client.post(
                "/api/v1/gui/project",
                json={"name": project_name, "path": project_path},
            )
            project_id = project_data.get("project_id") or project_data.get("id")

            if not project_id:
                raise Exception("Project ID not found in response")

            InitMessages.project_created()

    except Exception as e:
        InitMessages.project_creation_error(str(e))
        project_id = generate_project_id(project_name)

    InitMessages.show_project_id(project_id)
    base_url = Prompt.ask("\n🌐 Application URL", default="http://localhost:3000")

    # Credentials setup
    InitMessages.auth_setup()
    credentials = []

    if (
        Prompt.ask(
            "➕ Would you like to add custom login credentials? (y/n)", default="y"
        ).lower()
        == "y"
    ):
        identifier = Prompt.ask(
            "👤 Credential name",
            default="admin",
        )
        username = Prompt.ask("📧 Username/Email")
        password = Prompt.ask("🔒 Password", password=True)

        credentials.append(create_credential_entry(identifier, username, password))
        InitMessages.credential_added()
    else:
        credentials.append(create_credential_entry())
        InitMessages.using_default_credentials()

    # Create project structure
    InitMessages.project_structure_setup()

    # Create folders
    TESTS_DIR.mkdir(parents=True, exist_ok=True)

    # Update .gitignore
    update_gitignore()

    # Save config
    config = {
        "project_name": project_name,
        "project_id": project_id,
        "base_url": base_url,
        "credentials": credentials,
    }
    with open(CONFIG_PATH, "w") as f:
        yaml.dump(config, f, default_flow_style=False)

    # Show success message and summary
    InitMessages.initialization_success()

    # Show project summary
    summary_table = InitMessages.create_project_summary_table(
        project_name,
        project_id,
        base_url,
        CONFIG_PATH,
    )
    console.print()
    console.print(summary_table)

    # Show credentials if custom ones were added
    if len(credentials) > 1 or (
        len(credentials) == 1 and credentials[0]["id"] != "admin"
    ):
        creds_table = InitMessages.create_credentials_table(credentials)
        console.print()
        console.print(creds_table)

    # Show success panel
    success_panel = InitMessages.create_success_panel()
    console.print()
    console.print(success_panel)
    console.print()
