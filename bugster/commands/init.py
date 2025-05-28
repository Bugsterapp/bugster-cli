"""
Initialize command implementation.
"""

import yaml
import time
import os
from rich.prompt import Prompt
from rich.console import Console
from rich.table import Table

from bugster.constants import (
    BUGSTER_DIR,
    CONFIG_PATH,
    EXAMPLE_DIR,
    EXAMPLE_TEST_FILE,
    EXAMPLE_TEST,
)

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


def generate_project_id(name):
    """Generate a unique project ID from the project name.

    Combines the slugified project name with a timestamp to ensure uniqueness.
    """
    slug = name.lower().replace(" ", "-")
    timestamp = str(int(time.time()))
    return f"{slug}-{timestamp}"


def update_gitignore():
    """Create or update .gitignore to ignore videos, next, and example directories."""
    gitignore_path = BUGSTER_DIR / ".gitignore"
    ignore_patterns = [
        "videos/",
        "next/",
        "project.json",
    ]

    # Check if .gitignore exists
    if os.path.exists(gitignore_path):
        # Read existing content
        with open(gitignore_path, "r") as f:
            content = f.read()

        # Check which patterns need to be added
        patterns_to_add = []
        for pattern in ignore_patterns:
            if pattern not in content:
                patterns_to_add.append(pattern)

        # Add missing patterns
        if patterns_to_add:
            with open(gitignore_path, "a") as f:
                if not content.endswith("\n"):
                    f.write("\n")
                for pattern in patterns_to_add:
                    f.write(f"{pattern}\n")
    else:
        # Create new .gitignore with all patterns
        with open(gitignore_path, "w") as f:
            for pattern in ignore_patterns:
                f.write(f"{pattern}\n")


def init_command():
    """Initialize Bugster CLI configuration."""
    # Ask for project name and generate ID
    project_name = Prompt.ask("Project name", default="My Project")
    project_id = generate_project_id(project_name)

    base_url = Prompt.ask("Base URL", default="http://localhost:3000")

    # Initialize empty credentials array
    credentials = []

    if Prompt.ask("Do you want to add credentials? (y/n)", default="n").lower() == "y":
        while True:
            identifier = Prompt.ask(
                "Credential identifier (e.g. admin-user, test-manager)",
                default="custom-user",
            )
            username = Prompt.ask("Username")
            password = Prompt.ask("Password", password=True)

            credentials.append(
                create_credential_entry(
                    identifier=identifier,
                    username=username,
                    password=password,
                )
            )
            break

    else:
        # If no custom credentials, use default admin
        credentials.append(create_credential_entry())

    # Create folders
    EXAMPLE_DIR.mkdir(parents=True, exist_ok=True)

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

    # Save example test
    with open(EXAMPLE_TEST_FILE, "w") as f:
        f.write(EXAMPLE_TEST)

    # Show results
    console.print(f"[green]Configuration created at {CONFIG_PATH}")
    console.print(f"[green]Example test created at {EXAMPLE_TEST_FILE}")

    # Show credentials table
    table = Table(title="Configured Credentials")
    table.add_column("ID", style="cyan")
    table.add_column("Username", style="green")
    table.add_column("Password", style="yellow")

    for cred in credentials:
        table.add_row(cred["id"], cred["username"], cred["password"])

    console.print(table)
