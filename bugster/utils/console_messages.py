"""Console output messages for Bugster CLI."""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from bugster.utils.colors import BugsterColors

console = Console()

class InitMessages:
    """Messages for the init command."""
    
    @staticmethod
    def welcome():
        """Show welcome message."""
        console.print()
        console.print(f"🚀 [{BugsterColors.TEXT_PRIMARY}]Welcome to Bugster![/{BugsterColors.TEXT_PRIMARY}]")
        console.print(f"[{BugsterColors.TEXT_DIM}]Let's set up your project[/{BugsterColors.TEXT_DIM}]\n")

    @staticmethod
    def auth_required():
        """Show authentication required message."""
        console.print(f"⚠️  [{BugsterColors.WARNING}]Authentication Required[/{BugsterColors.WARNING}]")
        console.print(f"[{BugsterColors.TEXT_DIM}]First, let's set up your API key[/{BugsterColors.TEXT_DIM}]\n")

    @staticmethod
    def auth_success():
        """Show authentication success message."""
        console.print(f"[{BugsterColors.TEXT_DIM}]Now let's configure your project[/{BugsterColors.TEXT_DIM}]\n")

    @staticmethod
    def auth_failed():
        """Show authentication failed message."""
        console.print(f"\n❌ [{BugsterColors.ERROR}]Authentication failed. Please try again.[/{BugsterColors.ERROR}]")

    @staticmethod
    def get_existing_project_warning():
        """Get existing project warning message."""
        return "⚠️  Existing Bugster project detected. Would you like to reinitialize? This will overwrite current settings"

    @staticmethod
    def initialization_cancelled():
        """Show initialization cancelled message."""
        console.print(f"\n❌ [{BugsterColors.WARNING}]Initialization cancelled[/{BugsterColors.WARNING}]")

    @staticmethod
    def nested_project_error(current_dir, project_dir):
        """Show nested project error."""
        console.print(f"\n🚫 [{BugsterColors.ERROR}]Cannot initialize nested Bugster project[/{BugsterColors.ERROR}]")
        console.print(f"📁 [{BugsterColors.WARNING}]Current directory:[/{BugsterColors.WARNING}] {current_dir}")
        console.print(f"📁 [{BugsterColors.WARNING}]Parent project:[/{BugsterColors.WARNING}] {project_dir}")
        console.print(f"\n💡 [{BugsterColors.ERROR}]Please initialize the project outside of any existing Bugster project[/{BugsterColors.ERROR}]")

    @staticmethod
    def project_setup():
        """Show project setup header."""
        console.print(f"\n📝 [{BugsterColors.TEXT_PRIMARY}]Project Setup[/{BugsterColors.TEXT_PRIMARY}]")
        console.print(f"[{BugsterColors.TEXT_DIM}]Let's configure your project details[/{BugsterColors.TEXT_DIM}]\n")

    @staticmethod
    def creating_project():
        """Show creating project message."""
        console.print(f"\n[{BugsterColors.TEXT_DIM}]Creating project on Bugster...[/{BugsterColors.TEXT_DIM}]")

    @staticmethod
    def project_created():
        """Show project created message."""
        console.print(f"✨ [{BugsterColors.SUCCESS}]Project created successfully![/{BugsterColors.SUCCESS}]")

    @staticmethod
    def project_creation_error(error):
        """Show project creation error."""
        console.print(f"⚠️  [{BugsterColors.ERROR}]API connection error: {str(error)}[/{BugsterColors.ERROR}]")
        console.print(f"↪️  [{BugsterColors.WARNING}]Falling back to local project ID[/{BugsterColors.WARNING}]")

    @staticmethod
    def show_project_id(project_id):
        """Show project ID."""
        console.print(f"\n🆔 Project ID: [{BugsterColors.INFO}]{project_id}[/{BugsterColors.INFO}]")

    @staticmethod
    def auth_setup():
        """Show authentication setup header."""
        console.print(f"\n🔐 [{BugsterColors.TEXT_PRIMARY}]Authentication Setup[/{BugsterColors.TEXT_PRIMARY}]")
        console.print(f"[{BugsterColors.TEXT_DIM}]Configure login credentials for your application[/{BugsterColors.TEXT_DIM}]\n")

    @staticmethod
    def credential_added():
        """Show credential added message."""
        console.print(f"✓ [{BugsterColors.SUCCESS}]Credential added successfully[/{BugsterColors.SUCCESS}]\n")

    @staticmethod
    def using_default_credentials():
        """Show using default credentials message."""
        console.print(f"ℹ️  [{BugsterColors.TEXT_DIM}]Using default credentials (admin/admin)[/{BugsterColors.TEXT_DIM}]\n")

    @staticmethod
    def project_structure_setup():
        """Show project structure setup header."""
        console.print(f"🏗️  [{BugsterColors.TEXT_PRIMARY}]Setting Up Project Structure[/{BugsterColors.TEXT_PRIMARY}]")
        console.print(f"[{BugsterColors.TEXT_DIM}]Creating necessary files and directories[/{BugsterColors.TEXT_DIM}]\n")

    @staticmethod
    def initialization_success():
        """Show initialization success message."""
        console.print(f"\n🎉 [{BugsterColors.SUCCESS}]Project Initialized Successfully![/{BugsterColors.SUCCESS}]")

    @staticmethod
    def create_project_summary_table(project_name, project_id, base_url, config_path, creds_count):
        """Create and return project summary table."""
        table = Table(
            title="📋 Project Summary",
            show_header=True,
            header_style=BugsterColors.INFO
        )
        table.add_column("Setting", style=BugsterColors.INFO)
        table.add_column("Value", style=BugsterColors.SUCCESS)
        
        table.add_row("Project Name", project_name)
        table.add_row("Project ID", project_id)
        table.add_row("Base URL", base_url)
        table.add_row("Config Location", str(config_path))
        table.add_row("Credentials", f"{creds_count} configured")
        
        return table

    @staticmethod
    def create_credentials_table(credentials):
        """Create and return credentials table."""
        table = Table(title="🔐 Configured Credentials")
        table.add_column("ID", style=BugsterColors.INFO)
        table.add_column("Username", style=BugsterColors.SUCCESS)
        table.add_column("Password", style=BugsterColors.WARNING)
        
        for cred in credentials:
            password_masked = "•" * len(cred["password"])
            table.add_row(cred["id"], cred["username"], password_masked)
            
        return table

    @staticmethod
    def create_success_panel():
        """Create and return success panel."""
        return Panel(
            f"[bold][{BugsterColors.SUCCESS}]🎉 You're all set![/{BugsterColors.SUCCESS}][/bold]\n\n"
            f"[bold][{BugsterColors.TEXT_PRIMARY}]Next steps:[/{BugsterColors.TEXT_PRIMARY}][/bold]\n"
            f"1. [{BugsterColors.COMMAND}]bugster generate[/{BugsterColors.COMMAND}] - Generate test specs\n"
            f"2. [{BugsterColors.COMMAND}]bugster run[/{BugsterColors.COMMAND}] - Run your specs\n"
            f"3. [{BugsterColors.TEXT_DIM}]Integrate Bugster with GitHub [{BugsterColors.LINK}]https://gui.bugster.dev/dashboard[/{BugsterColors.LINK}][/{BugsterColors.TEXT_DIM}]\n\n"
            f"[{BugsterColors.TEXT_DIM}]Need help? Visit [{BugsterColors.LINK}]https://docs.bugster.dev[/{BugsterColors.LINK}][/{BugsterColors.TEXT_DIM}]",
            title="🚀 Ready to Go",
            border_style=BugsterColors.SUCCESS
        )

class AuthMessages:
    """Messages for the auth command."""
    
    @staticmethod
    def create_auth_panel():
        """Create and return the authentication panel."""
        return Panel(
            f"[bold]To use Bugster CLI, you need an API key from your Bugster dashboard.[/bold]\n\n"
            f"1. Visit [{BugsterColors.LINK}]https://gui.bugster.dev[/{BugsterColors.LINK}]\n"
            "2. Sign up or log in to your account\n"
            "3. Copy your API key from the dashboard\n"
            "4. Paste it below to authenticate this CLI",
            title="🚀 Getting Started",
            border_style=BugsterColors.PRIMARY,
            padding=(1, 2)
        )

    @staticmethod
    def ask_open_dashboard():
        """Get the open dashboard prompt message."""
        return f"🌐 [{BugsterColors.TEXT_PRIMARY}]Open Bugster dashboard in your browser?[/{BugsterColors.TEXT_PRIMARY}]"

    @staticmethod
    def opening_dashboard():
        """Show opening dashboard message."""
        console.print(f"🔍 [{BugsterColors.TEXT_DIM}]Opening https://gui.bugster.dev in your browser...[/{BugsterColors.TEXT_DIM}]")

    @staticmethod
    def api_key_prompt():
        """Show API key prompt messages."""
        console.print(f"📋 [bold][{BugsterColors.TEXT_PRIMARY}]Please copy your API key from the dashboard[/{BugsterColors.TEXT_PRIMARY}][/bold]")
        console.print(f"[{BugsterColors.TEXT_DIM}]Your API key should start with 'bugster_'[/{BugsterColors.TEXT_DIM}]")

    @staticmethod
    def get_api_key_prompt():
        """Get the API key input prompt."""
        return f"🔑 [{BugsterColors.TEXT_PRIMARY}]Paste your API key here[/{BugsterColors.TEXT_PRIMARY}]"

    @staticmethod
    def empty_api_key_error():
        """Show empty API key error message."""
        console.print(f"❌ [{BugsterColors.ERROR}]API key cannot be empty. Please try again.[/{BugsterColors.ERROR}]")

    @staticmethod
    def invalid_prefix_warning():
        """Show invalid prefix warning message."""
        console.print(f"⚠️  [{BugsterColors.WARNING}]Warning: API keys typically start with 'bugster_'[/{BugsterColors.WARNING}]")

    @staticmethod
    def get_continue_anyway_prompt():
        """Get the continue anyway prompt message."""
        return f"[{BugsterColors.TEXT_PRIMARY}]Continue anyway?[/{BugsterColors.TEXT_PRIMARY}]"

    @staticmethod
    def validating_api_key():
        """Show validating API key message."""
        console.print(f"🔄 [{BugsterColors.WARNING}]Validating API key...[/{BugsterColors.WARNING}]")

    @staticmethod
    def invalid_api_key_error():
        """Show invalid API key error message."""
        console.print(f"❌ [{BugsterColors.ERROR}]Invalid API key. Please check and try again.[/{BugsterColors.ERROR}]")

    @staticmethod
    def auth_success():
        """Show authentication success message."""
        console.print()
        console.print(f"✅ [bold][{BugsterColors.SUCCESS}]Authentication successful![/{BugsterColors.SUCCESS}][/bold]")
        console.print()

    @staticmethod
    def auth_error(error):
        """Show authentication error message."""
        console.print(f"❌ [{BugsterColors.ERROR}]Error saving API key: {str(error)}[/{BugsterColors.ERROR}]")

class CLIMessages:
    """Messages for the CLI commands."""
    
    @staticmethod
    def get_version_header(version: str):
        """Get version header message."""
        messages = [
            (f"🐛 [bold {BugsterColors.PRIMARY}]Bugster CLI[/bold {BugsterColors.PRIMARY}]", "center"),
            (f"[{BugsterColors.TEXT_DIM}]Version[/{BugsterColors.TEXT_DIM}] [bold {BugsterColors.SUCCESS}]{version}[/bold {BugsterColors.SUCCESS}]", "center"),
            ("", None),
            (f"[{BugsterColors.TEXT_DIM}]AI-powered end-to-end testing for web applications[/{BugsterColors.TEXT_DIM}]", "center"),
            ("", None),
            (f"[{BugsterColors.TEXT_DIM}]Links:[/{BugsterColors.TEXT_DIM}]", "left"),
            (f"  🌐 Dashboard: [{BugsterColors.LINK}]https://gui.bugster.dev[/{BugsterColors.LINK}]", "left"),
            (f"  📚 Docs: [{BugsterColors.LINK}]https://docs.bugster.dev[/{BugsterColors.LINK}]", "left"),
            (f"  🐙 GitHub: [{BugsterColors.LINK}]https://github.com/Bugsterapp/bugster-cli[/{BugsterColors.LINK}]", "left"),
            ("", None)
        ]
        return messages

    @staticmethod
    def get_main_help():
        """Get main help message."""
        return f"""🐛 [bold {BugsterColors.PRIMARY}]Bugster CLI[/bold {BugsterColors.PRIMARY}] - AI-powered end-to-end testing for web applications
    
    [{BugsterColors.TEXT_DIM}]Transform your manual testing into automated test cases with intelligent code analysis.[/{BugsterColors.TEXT_DIM}]
    
    [{BugsterColors.TEXT_PRIMARY}]Quick Start:[/{BugsterColors.TEXT_PRIMARY}]
    1. [bold {BugsterColors.COMMAND}]bugster init[/bold {BugsterColors.COMMAND}]        - Initialize your project  
    2. [bold {BugsterColors.COMMAND}]bugster generate[/bold {BugsterColors.COMMAND}]    - Generate test cases
    3. [bold {BugsterColors.COMMAND}]bugster run[/bold {BugsterColors.COMMAND}]         - Run your tests
    4. [bold {BugsterColors.COMMAND}]bugster update[/bold {BugsterColors.COMMAND}]      - Update your test cases
    5. [bold {BugsterColors.COMMAND}]bugster sync[/bold {BugsterColors.COMMAND}]        - Sync your test cases with the remote repository
    
    [{BugsterColors.TEXT_DIM}]Visit [{BugsterColors.LINK}]https://gui.bugster.dev[/{BugsterColors.LINK}] to get started![/{BugsterColors.TEXT_DIM}]"""

    @staticmethod
    def get_init_help():
        """Get init command help message."""
        return f"""[bold {BugsterColors.COMMAND}]Initialize[/bold {BugsterColors.COMMAND}] Bugster CLI configuration in your project.

    Set up Bugster configuration in your repository.
    Creates .bugster/ directory with project settings."""

    @staticmethod
    def get_run_help():
        """Get run command help message."""
        return f"""🧪 [bold {BugsterColors.COMMAND}]Run[/bold {BugsterColors.COMMAND}] your Bugster tests
    
    Execute AI-generated test cases against your application.
    
    [{BugsterColors.TEXT_DIM}]Examples:[/{BugsterColors.TEXT_DIM}]
      [{BugsterColors.PRIMARY}]bugster run[/{BugsterColors.PRIMARY}]                    - Run all tests
      [{BugsterColors.PRIMARY}]bugster run auth/[/{BugsterColors.PRIMARY}]              - Run tests in auth/ directory  
      [{BugsterColors.PRIMARY}]bugster run --headless[/{BugsterColors.PRIMARY}]         - Run without browser UI
      [{BugsterColors.PRIMARY}]bugster run --stream-results[/{BugsterColors.PRIMARY}]   - Stream to dashboard"""

    @staticmethod
    def get_analyze_help():
        """Get analyze command help message."""
        return f"""🔍 [bold {BugsterColors.COMMAND}]Analyze[/bold {BugsterColors.COMMAND}] your codebase
    
    Scan your application code and generate test specs.
    Uses AI to understand your app structure and create comprehensive tests.
    
    [{BugsterColors.TEXT_DIM}]This may take a few minutes for large codebases.[/{BugsterColors.TEXT_DIM}]"""

    @staticmethod
    def get_update_help():
        """Get update command help message."""
        return f"""🔄 [bold {BugsterColors.COMMAND}]Update[/bold {BugsterColors.COMMAND}] your test specs with the latest changes."""

    @staticmethod
    def get_sync_help():
        """Get sync command help message."""
        return f"""🔄 [bold {BugsterColors.COMMAND}]Sync[/bold {BugsterColors.COMMAND}] test cases with team
    
    Keep your test cases in sync across team members and environments.
    Handles conflicts intelligently based on modification timestamps.""" 