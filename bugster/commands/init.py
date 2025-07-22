"""Initialize command implementation."""

import contextlib
import time
from pathlib import Path

import typer
from loguru import logger
from rich.console import Console
from rich.prompt import Confirm, Prompt

from bugster.analytics import track_command
from bugster.clients.http_client import BugsterHTTPClient
from bugster.commands.auth import auth_command, validate_api_key
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
        with open(gitignore_path, encoding="utf-8") as f:
            existing_entries = f.read().splitlines()

    # Add missing entries
    with open(gitignore_path, "a", encoding="utf-8") as f:
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


def generate_config_yaml_with_template(
    project_name: str,
    project_id: str,
    base_url: str,
    credentials: list,
    bypass_protection: str = "",
    platform: str = "vercel",
) -> str:
    """Generate config.yaml content with commented template options."""

    # Helper function to format YAML string values
    def format_yaml_string(value: str) -> str:
        """Format a string value for YAML, adding quotes if needed."""
        if " " in value or ":" in value or value.startswith("#"):
            return f'"{value}"'
        return value

    # Generate the main config with active values
    config_lines = [
        "# Bugster Configuration File",
        "# This file contains your project configuration and test execution preferences.",
        "",
        "# Project Information",
        f"project_name: {format_yaml_string(project_name)}",
        f"project_id: {format_yaml_string(project_id)}",
        f"base_url: {format_yaml_string(base_url)}",
        "",
        "# Project Authentication",
        "credentials:",
    ]

    # Add credentials
    for cred in credentials:
        config_lines.extend(
            [
                f"  - id: {format_yaml_string(cred['id'])}",
                f"    username: {format_yaml_string(cred['username'])}",
                f"    password: {format_yaml_string(cred['password'])}",
            ]
        )

    config_lines.append("")

    # Add platform-specific protection bypass section
    if platform == "vercel":
        config_lines.extend(
            [
                "# Vercel Configuration",
                "# You can create the Vercel Protection Bypass Secret for Automation in this link:",
                "# https://vercel.com/d?to=/[team]/[project]/settings/deployment-protection&title=Deployment+Protection+settings",
            ]
        )
        if bypass_protection:
            config_lines.append(
                f"x-vercel-protection-bypass: {format_yaml_string(bypass_protection)}"
            )
        else:
            config_lines.append("# x-vercel-protection-bypass: your-bypass-secret")
    elif platform == "railway":
        config_lines.extend(
            [
                "# Railway Configuration",
                "# Add your Railway protection bypass secret below:",
            ]
        )
        if bypass_protection:
            config_lines.append(
                f"x-railway-protection-bypass: {format_yaml_string(bypass_protection)}"
            )
        else:
            config_lines.append("# x-railway-protection-bypass: your-bypass-secret")

    config_lines.extend(
        [
            "",
            "",
            "# Test Execution Preferences",
            "# Uncomment and modify the options below to customize test execution behavior.",
            "# CLI options will override these settings when specified.",
            "# preferences:",
            "#   tests:",
            "#     always_run:",
            "#       - .bugster/tests/test1.yaml",
            "#       - .bugster/tests/test2.yaml",
            "#     limit: 5                    # Maximum number of tests to run",
            "#     headless: false             # Run tests in headless mode",
            "#     silent: false               # Run tests in silent mode",
            "#     verbose: false              # Enable verbose output",
            "#     only_affected: false        # Only run tests for affected files",
            "#     parallel: 5                 # Maximum number of concurrent tests",
            "#     output: bugster_output.json # Save test results to JSON file",
            "",
        ]
    )

    return "\n".join(config_lines)


@track_command("init")
def init_command(
    api_key: str = None,
    project_name: str = None,
    url: str = None,
    user: str = None,
    password: str = None,
    credential_name: str = None,
    no_auth: bool = False,
    no_credentials: bool = False,
    bypass_protection: str = None,
    platform: str = "vercel",
):
    """Initialize Bugster CLI configuration."""
    InitMessages.welcome()

    # Validate platform flag
    if platform not in ["vercel", "railway"]:
        console.print(
            "[red]Error: --platform must be either 'vercel' or 'railway'.[/red]"
        )
        raise typer.Exit(1)

    # Handle API key authentication
    current_api_key = get_api_key()

    # Use provided API key or get from storage
    if api_key:
        # Validate provided API key
        if not validate_api_key(api_key):
            console.print(
                "[red]Invalid API key. Please check the format and try again.[/red]"
            )
            raise typer.Exit(1)

        # Save the provided API key
        from bugster.utils.user_config import save_api_key

        save_api_key(api_key)
        current_api_key = api_key
        console.print("[green]✓ API key saved successfully[/green]")
    elif not current_api_key and not no_auth:
        logger.info("API key not found, running auth command...")
        InitMessages.auth_required()

        # Run auth command
        auth_command()

        # Check if auth was successful
        current_api_key = get_api_key()

        if not current_api_key:
            InitMessages.auth_failed()
            raise typer.Exit(1)

        InitMessages.auth_success()
    elif not current_api_key and no_auth:
        console.print(
            "[red]No API key configured and --no-auth flag provided. Please provide --api-key or run without --no-auth.[/red]"
        )
        raise typer.Exit(1)

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

    # Use provided project name or prompt for it
    if project_name is None:
        project_name = Prompt.ask("🏷️  Project name", default=Path.cwd().name)
    else:
        console.print(f"🏷️  Project name: {project_name}")

    project_path = ""
    with contextlib.suppress(Exception):
        project_path = get_git_prefix_path()

    # Create project via API
    try:
        with BugsterHTTPClient() as client:
            client.set_headers({"x-api-key": current_api_key})
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

    # Use provided URL or prompt for it
    if url is None:
        base_url = Prompt.ask("\n🌐 Application URL", default="http://localhost:3000")
    else:
        base_url = url
        console.print(f"🌐 Application URL: {base_url}")

    # Credentials setup
    credentials = []

    if no_credentials:
        # Skip credentials setup entirely
        if user is not None or password is not None or credential_name is not None:
            console.print(
                "[red]Error: Cannot use --user, --password, or --credential-name with --no-credentials.[/red]"
            )
            raise typer.Exit(1)
        else:
            console.print(
                "🚫 Skipping credential setup (--no-credentials flag provided)"
            )
    else:
        InitMessages.auth_setup()

        # Determine if we should use custom credentials
        use_custom_credentials = False

        if user is not None and password is not None:
            # Both user and password provided via flags
            use_custom_credentials = True
            console.print("✓ Using provided login credentials")
        elif user is not None or password is not None:
            # Only one of user/password provided - this is an error
            console.print(
                "[red]Error: Both --user and --password must be provided together.[/red]"
            )
            raise typer.Exit(1)
        else:
            # No credentials provided via flags, prompt interactively
            if (
                Prompt.ask(
                    "➕ Would you like to add custom login credentials? (y/n)",
                    default="y",
                ).lower()
                == "y"
            ):
                use_custom_credentials = True

        if use_custom_credentials:
            # Use provided values or prompt for them
            if user is not None and password is not None:
                # Values provided via flags
                identifier = credential_name or "admin"
                username = user
                password_value = password
                console.print(f"👤 Credential name: {identifier}")
                console.print(f"📧 Username/Email: {username}")
                console.print("🔒 Password: [hidden]")
            else:
                # Interactive mode
                identifier = Prompt.ask(
                    "👤 Credential name",
                    default="admin",
                )
                username = Prompt.ask("📧 Username/Email")
                password_value = Prompt.ask("🔒 Password", password=True)

            credentials.append(
                create_credential_entry(identifier, username, password_value)
            )
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
    config_content = generate_config_yaml_with_template(
        project_name=project_name,
        project_id=project_id,
        base_url=base_url,
        credentials=credentials,
        bypass_protection=bypass_protection or "",
        platform=platform,
    )

    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        f.write(config_content)

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
