"""Console output messages for Bugster CLI."""

from rich.console import Console
from rich.panel import Panel
from rich.style import Style
from rich.table import Table

from bugster.utils.colors import BugsterColors

console = Console()


class InitMessages:
    """Messages for the init command."""

    @staticmethod
    def welcome():
        """Show welcome message."""
        console.print()
        console.print(
            f"🚀 [{BugsterColors.TEXT_PRIMARY}]Welcome to Bugster![/{BugsterColors.TEXT_PRIMARY}]"
        )
        console.print(
            f"[{BugsterColors.TEXT_DIM}]Let's set up your project[/{BugsterColors.TEXT_DIM}]\n"
        )

    @staticmethod
    def auth_required():
        """Show authentication required message."""
        console.print(
            f"⚠️  [{BugsterColors.WARNING}]Authentication Required[/{BugsterColors.WARNING}]"
        )
        console.print(
            f"[{BugsterColors.TEXT_DIM}]First, let's set up your API key[/{BugsterColors.TEXT_DIM}]\n"
        )

    @staticmethod
    def auth_success():
        """Show authentication success message."""
        console.print(
            f"[{BugsterColors.TEXT_DIM}]Now let's configure your project[/{BugsterColors.TEXT_DIM}]\n"
        )

    @staticmethod
    def auth_failed():
        """Show authentication failed message."""
        console.print(
            f"\n❌ [{BugsterColors.ERROR}]Authentication failed. Please try again.[/{BugsterColors.ERROR}]"
        )

    @staticmethod
    def get_existing_project_warning():
        """Get existing project warning message."""
        return "⚠️  Existing Bugster project detected. Would you like to reinitialize? This will overwrite current settings"

    @staticmethod
    def initialization_cancelled():
        """Show initialization cancelled message."""
        console.print(
            f"\n❌ [{BugsterColors.WARNING}]Initialization cancelled[/{BugsterColors.WARNING}]"
        )

    @staticmethod
    def nested_project_error(current_dir, project_dir):
        """Show nested project error."""
        console.print(
            f"\n🚫 [{BugsterColors.ERROR}]Cannot initialize nested Bugster project[/{BugsterColors.ERROR}]"
        )
        console.print(
            f"📁 [{BugsterColors.WARNING}]Current directory:[/{BugsterColors.WARNING}] {current_dir}"
        )
        console.print(
            f"📁 [{BugsterColors.WARNING}]Parent project:[/{BugsterColors.WARNING}] {project_dir}"
        )
        console.print(
            f"\n💡 [{BugsterColors.ERROR}]Please initialize the project outside of any existing Bugster project[/{BugsterColors.ERROR}]"
        )

    @staticmethod
    def project_setup():
        """Show project setup header."""
        console.print(
            f"\n📝 [{BugsterColors.TEXT_PRIMARY}]Project Setup[/{BugsterColors.TEXT_PRIMARY}]"
        )
        console.print(
            f"[{BugsterColors.TEXT_DIM}]Let's configure your project details[/{BugsterColors.TEXT_DIM}]\n"
        )

    @staticmethod
    def creating_project():
        """Show creating project message."""
        console.print(
            f"\n[{BugsterColors.TEXT_DIM}]Creating project on Bugster...[/{BugsterColors.TEXT_DIM}]"
        )

    @staticmethod
    def project_created():
        """Show project created message."""
        console.print(
            f"✨ [{BugsterColors.SUCCESS}]Project created successfully![/{BugsterColors.SUCCESS}]"
        )

    @staticmethod
    def project_creation_error(error):
        """Show project creation error."""
        console.print(
            f"⚠️  [{BugsterColors.ERROR}]API connection error: {str(error)}[/{BugsterColors.ERROR}]"
        )
        console.print(
            f"↪️  [{BugsterColors.WARNING}]Falling back to local project ID[/{BugsterColors.WARNING}]"
        )

    @staticmethod
    def show_project_id(project_id):
        """Show project ID."""
        console.print(
            f"\n🆔 Project ID: [{BugsterColors.INFO}]{project_id}[/{BugsterColors.INFO}]"
        )

    @staticmethod
    def auth_setup():
        """Show authentication setup header."""
        console.print(
            f"\n🔐 [{BugsterColors.TEXT_PRIMARY}]Authentication Setup[/{BugsterColors.TEXT_PRIMARY}]"
        )
        console.print(
            f"[{BugsterColors.TEXT_DIM}]Configure login credentials for your application[/{BugsterColors.TEXT_DIM}]\n"
        )

    @staticmethod
    def credential_added():
        """Show credential added message."""
        console.print(
            f"✓ [{BugsterColors.SUCCESS}]Credential added successfully[/{BugsterColors.SUCCESS}]\n"
        )

    @staticmethod
    def using_default_credentials():
        """Show using default credentials message."""
        console.print(
            f"ℹ️  [{BugsterColors.TEXT_DIM}]Using default credentials (admin/admin)[/{BugsterColors.TEXT_DIM}]\n"
        )

    @staticmethod
    def project_structure_setup():
        """Show project structure setup header."""
        console.print(
            f"🏗️  [{BugsterColors.TEXT_PRIMARY}]Setting Up Project Structure[/{BugsterColors.TEXT_PRIMARY}]"
        )
        console.print(
            f"[{BugsterColors.TEXT_DIM}]Creating necessary files and directories[/{BugsterColors.TEXT_DIM}]\n"
        )

    @staticmethod
    def initialization_success():
        """Show initialization success message."""
        console.print(
            f"\n🎉 [{BugsterColors.SUCCESS}]Project Initialized Successfully![/{BugsterColors.SUCCESS}]"
        )

    @staticmethod
    def create_project_summary_table(project_name, project_id, base_url, config_path):
        """Create and return project summary table."""
        table = Table(
            title="📋 Project Summary",
            show_header=True,
            header_style=BugsterColors.INFO,
        )
        table.add_column("Setting", style=BugsterColors.INFO)
        table.add_column("Value", style=BugsterColors.SUCCESS)

        table.add_row("Project Name", project_name)
        table.add_row("Project ID", project_id)
        table.add_row("Base URL", base_url)
        table.add_row("Config Location", str(config_path))

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
            border_style=BugsterColors.SUCCESS,
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
            padding=(1, 2),
        )

    @staticmethod
    def ask_open_dashboard():
        """Get the open dashboard prompt message."""
        return f"🌐 [{BugsterColors.TEXT_PRIMARY}]Open Bugster dashboard in your browser?[/{BugsterColors.TEXT_PRIMARY}]"

    @staticmethod
    def opening_dashboard():
        """Show opening dashboard message."""
        console.print(
            f"🔍 [{BugsterColors.TEXT_DIM}]Opening https://gui.bugster.dev in your browser...[/{BugsterColors.TEXT_DIM}]"
        )

    @staticmethod
    def api_key_prompt():
        """Show API key prompt messages."""
        console.print(
            f"📋 [bold][{BugsterColors.TEXT_PRIMARY}]Please copy your API key from the dashboard[/{BugsterColors.TEXT_PRIMARY}][/bold]"
        )
        console.print(
            f"[{BugsterColors.TEXT_DIM}]Your API key should start with 'bugster_'[/{BugsterColors.TEXT_DIM}]"
        )

    @staticmethod
    def get_api_key_prompt():
        """Get the API key input prompt."""
        return f"🔑 [{BugsterColors.TEXT_PRIMARY}]Paste your API key here[/{BugsterColors.TEXT_PRIMARY}]"

    @staticmethod
    def empty_api_key_error():
        """Show empty API key error message."""
        console.print(
            f"❌ [{BugsterColors.ERROR}]API key cannot be empty. Please try again.[/{BugsterColors.ERROR}]"
        )

    @staticmethod
    def invalid_prefix_warning():
        """Show invalid prefix warning message."""
        console.print(
            f"⚠️  [{BugsterColors.WARNING}]Warning: API keys typically start with 'bugster_'[/{BugsterColors.WARNING}]"
        )

    @staticmethod
    def get_continue_anyway_prompt():
        """Get the continue anyway prompt message."""
        return f"[{BugsterColors.TEXT_PRIMARY}]Continue anyway?[/{BugsterColors.TEXT_PRIMARY}]"

    @staticmethod
    def validating_api_key():
        """Show validating API key message."""
        console.print(
            f"🔄 [{BugsterColors.WARNING}]Validating API key...[/{BugsterColors.WARNING}]"
        )

    @staticmethod
    def invalid_api_key_error():
        """Show invalid API key error message."""
        console.print(
            f"❌ [{BugsterColors.ERROR}]Invalid API key. Please check and try again.[/{BugsterColors.ERROR}]"
        )

    @staticmethod
    def auth_success():
        """Show authentication success message."""
        console.print()
        console.print(
            f"✅ [bold][{BugsterColors.SUCCESS}]Authentication successful![/{BugsterColors.SUCCESS}][/bold]"
        )
        console.print()

    @staticmethod
    def auth_error(error):
        """Show authentication error message."""
        console.print(
            f"❌ [{BugsterColors.ERROR}]Error saving API key: {str(error)}[/{BugsterColors.ERROR}]"
        )

    @staticmethod
    def create_analytics_panel():
        """Create and return the analytics opt-in panel."""
        return Panel(
            f"[bold][{BugsterColors.TEXT_PRIMARY}]📊 Help Improve Bugster[/{BugsterColors.TEXT_PRIMARY}][/bold]\n\n"
            f"Bugster collects anonymous usage analytics to help improve the CLI.\n\n"
            f"[bold][{BugsterColors.SUCCESS}]✅ What we collect:[/{BugsterColors.SUCCESS}][/bold]\n"
            f"• Command usage patterns\n"
            f"• Error types and frequencies\n"
            f"• Performance metrics\n"
            f"• Platform and environment info\n\n"
            f"[bold][{BugsterColors.ERROR}]❌ What we DON'T collect:[/{BugsterColors.ERROR}][/bold]\n"
            f"• Your code or file contents\n"
            f"• Personal information\n"
            f"• API keys or secrets\n"
            f"• File paths or names\n\n"
            f"[{BugsterColors.TEXT_DIM}]You can opt-out anytime by setting BUGSTER_ANALYTICS_DISABLED=true[/{BugsterColors.TEXT_DIM}]",
            title="🛡️ Privacy & Analytics",
            border_style=BugsterColors.INFO,
            padding=(1, 2),
        )

    @staticmethod
    def analytics_enabled():
        """Show analytics enabled message."""
        console.print(
            f"✅ [{BugsterColors.SUCCESS}]Thank you! Analytics enabled to help improve Bugster.[/{BugsterColors.SUCCESS}]"
        )

    @staticmethod
    def analytics_disabled():
        """Show analytics disabled message."""
        console.print(
            f"✅ [{BugsterColors.INFO}]Analytics disabled. You can change this anytime.[/{BugsterColors.INFO}]"
        )


class CLIMessages:
    """Messages for the CLI commands."""

    @staticmethod
    def get_version_header(version: str):
        """Get version header message."""
        messages = [
            (
                f"🐛 [bold {BugsterColors.PRIMARY}]Bugster CLI[/bold {BugsterColors.PRIMARY}]",
                "center",
            ),
            (
                f"[{BugsterColors.TEXT_DIM}]Version[/{BugsterColors.TEXT_DIM}] [bold {BugsterColors.SUCCESS}]{version}[/bold {BugsterColors.SUCCESS}]",
                "center",
            ),
            ("", None),
            (
                f"[{BugsterColors.TEXT_DIM}]AI-powered end-to-end testing for web applications[/{BugsterColors.TEXT_DIM}]",
                "center",
            ),
            ("", None),
            (f"[{BugsterColors.TEXT_DIM}]Links:[/{BugsterColors.TEXT_DIM}]", "left"),
            (
                f"  🌐 Dashboard: [{BugsterColors.LINK}]https://gui.bugster.dev[/{BugsterColors.LINK}]",
                "left",
            ),
            (
                f"  📚 Docs: [{BugsterColors.LINK}]https://docs.bugster.dev[/{BugsterColors.LINK}]",
                "left",
            ),
            (
                f"  🐙 GitHub: [{BugsterColors.LINK}]https://github.com/Bugsterapp/bugster-cli[/{BugsterColors.LINK}]",
                "left",
            ),
            ("", None),
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
    Handles conflicts intelligently based on modification timestamps.ps."""

    @staticmethod
    def get_destructive_help():
        """Get destructive command help message."""
        return f"""🔥 [bold {BugsterColors.COMMAND}]Destructive[/bold {BugsterColors.COMMAND}] testing for changed pages

    Run AI-powered destructive agents to find potential bugs in your recent code changes.
    Agents like 'form_destroyer' and 'ui_crasher' will attempt to break your application.

    [{BugsterColors.TEXT_DIM}]Examples:[/{BugsterColors.TEXT_DIM}]
      [{BugsterColors.PRIMARY}]bugster destructive[/{BugsterColors.PRIMARY}]                    - Run on all changed pages
      [{BugsterColors.PRIMARY}]bugster destructive --headless[/{BugsterColors.PRIMARY}]         - Run without browser UI
      [{BugsterColors.PRIMARY}]bugster destructive --max-concurrent 5[/{BugsterColors.PRIMARY}] - Run up to 5 agents in parallel"""

    @staticmethod
    def get_upgrade_help():
        """Get the help message for the upgrade command."""
        return "Upgrade Bugster CLI to the latest version."


class RunMessages:
    """Messages for the test command."""

    @staticmethod
    def no_tests_found():
        """Show no tests found message."""
        console.print(
            f"[{BugsterColors.WARNING}]No test files found[/{BugsterColors.WARNING}]"
        )

    @staticmethod
    def running_test_file(file_path):
        """Show running test file message."""
        console.print(
            f"\n[{BugsterColors.INFO}]Running tests from {file_path}[/{BugsterColors.INFO}]"
        )

    @staticmethod
    def invalid_test_file_format(file_path):
        """Show invalid test file format message."""
        console.print(
            f"[{BugsterColors.ERROR}]Error: Invalid test file format in {file_path}[/{BugsterColors.ERROR}]"
        )

    @staticmethod
    def test_start(test_name):
        """Show test start message."""
        console.print(
            f"\n[{BugsterColors.PRIMARY}]Test: {test_name}[/{BugsterColors.PRIMARY}]"
        )

    @staticmethod
    def test_result(test_name, result, elapsed_time):
        """Show test result message."""
        status_color = (
            BugsterColors.SUCCESS if result == "pass" else BugsterColors.ERROR
        )
        console.print(
            f"[{status_color}]Test: {test_name} -> {result} (Time: {elapsed_time:.2f}s)[/{status_color}]"
        )

    @staticmethod
    def connecting_to_agent():
        """Show connecting to agent message."""
        return f"[{BugsterColors.TEXT_PRIMARY}]Connecting to Bugster Agent. Sometimes this may take a few seconds...[/{BugsterColors.TEXT_PRIMARY}]"

    @staticmethod
    def connected_successfully():
        """Show connected successfully message."""
        return f"[{BugsterColors.SUCCESS}]Connected successfully!"

    @staticmethod
    def running_test_status(test_name, message=""):
        """Show running test status message."""
        return f"[{BugsterColors.PRIMARY}]Running test: {test_name}[/{BugsterColors.PRIMARY}]{f'[{BugsterColors.TEXT_PRIMARY}] - {message}[/{BugsterColors.TEXT_PRIMARY}]' if message else ''}"

    @staticmethod
    def retrying_step(test_name, retry_count, max_retries, message, is_timeout=True):
        """Show retrying step message."""
        retry_type = "Retrying" if is_timeout else "Waiting 30s, then retrying"
        return f"[{BugsterColors.WARNING}]Running test: {test_name} - {retry_type} ({retry_count}/{max_retries}): {message}[/{BugsterColors.WARNING}]"

    @staticmethod
    def max_retries_exceeded():
        """Show max retries exceeded message."""
        console.print(
            f"[{BugsterColors.ERROR}]Max retries exceeded. Please try again later[/{BugsterColors.ERROR}]"
        )

    @staticmethod
    def internal_error():
        """Show internal error message."""
        console.print(
            f"[{BugsterColors.ERROR}]Internal error. Please try again later[/{BugsterColors.ERROR}]"
        )

    @staticmethod
    def streaming_results_to_run(run_id):
        """Show streaming results message."""
        console.print(
            f"[{BugsterColors.INFO}]Streaming results to run: {run_id}[/{BugsterColors.INFO}]"
        )

    @staticmethod
    def streaming_warning(test_name, error):
        """Show streaming warning message."""
        console.print(
            f"[{BugsterColors.WARNING}]Warning: Failed to stream result for {test_name}: {str(error)}[/{BugsterColors.WARNING}]"
        )

    @staticmethod
    def streaming_init_warning(error):
        """Show streaming initialization warning message."""
        console.print(
            f"[{BugsterColors.WARNING}]Warning: Failed to initialize streaming service: {str(error)}[/{BugsterColors.WARNING}]"
        )

    @staticmethod
    def updating_final_status():
        """Show updating final status message."""
        console.print(
            f"[{BugsterColors.TEXT_DIM}]Updating final run status[/{BugsterColors.TEXT_DIM}]"
        )

    @staticmethod
    def results_saved(output_path):
        """Show results saved message."""
        console.print(
            f"\n[{BugsterColors.SUCCESS}]Results saved to: {output_path}[/{BugsterColors.SUCCESS}]"
        )

    @staticmethod
    def save_results_error(output_path, error):
        """Show save results error message."""
        console.print(
            f"[{BugsterColors.ERROR}]Error saving results to {output_path}: {str(error)}[/{BugsterColors.ERROR}]"
        )

    @staticmethod
    def total_execution_time(total_time):
        """Show total execution time."""
        console.print(
            f"\n[{BugsterColors.TEXT_DIM}]Total execution time: {total_time:.2f} seconds[/{BugsterColors.TEXT_DIM}]"
        )

    @staticmethod
    def create_results_table(results):
        """Create and show results table."""
        table = Table(title="Test Results")
        table.add_column("Name", justify="left")
        table.add_column("Result", justify="left")
        table.add_column("Reason", justify="left")
        table.add_column("Time (s)", justify="right")

        for result in results:
            table.add_row(
                result.name,
                result.result,
                result.reason,
                f"{result.time:.2f}" if hasattr(result, "time") else "N/A",
                style=Style(color="green" if result.result == "pass" else "red"),
            )

        console.print(table)

    @staticmethod
    def create_results_panel(results):
        """Create and show results panel."""
        passed = sum(1 for r in results if r.result == "pass")
        failed = len(results) - passed
        success_rate = (passed / len(results)) * 100 if results else 0

        panel_content = f"""
[bold]Test Summary[/bold]

✅ Passed: {passed}
❌ Failed: {failed}
📊 Success Rate: {success_rate:.1f}%
           """

        style = BugsterColors.SUCCESS if failed == 0 else BugsterColors.ERROR
        console.print(Panel(panel_content.strip(), border_style=style))

    @staticmethod
    def error(message):
        """Show error message."""
        console.print(
            f"[{BugsterColors.ERROR}]Error: {message}[/{BugsterColors.ERROR}]"
        )

    @staticmethod
    def create_test_limit_panel(
        original_count: int,
        selected_count: int,
        max_tests: int,
        folder_distribution: dict,
        always_run_count: int = 0,
        always_run_distribution: dict = None,
    ):
        """Create a panel showing test limit information."""
        content = []

        if selected_count < original_count:
            # Update title to show always-run breakdown
            if always_run_count > 0:
                total_running = selected_count + always_run_count
                total_limit = max_tests + always_run_count
                content.append(
                    f"[bold]Test limit applied:[/bold] Running {selected_count} + {always_run_count} (Always-run) out of {original_count} tests (limit: {max_tests} + {always_run_count})"
                )
            else:
                content.append(
                    f"[bold]Test limit applied:[/bold] Running {selected_count} out of {original_count} tests (limit: {max_tests})"
                )

            content.append("")  # Empty line for spacing
            content.append("[bold]Distribution by folder:[/bold]")

            # Add folder distribution
            for folder, count in sorted(folder_distribution.items()):
                content.append(
                    f"📁 [{BugsterColors.TEXT_DIM}]{folder}[/{BugsterColors.TEXT_DIM}]"
                )
                content.append(
                    f"   ▸ [{BugsterColors.TEXT_PRIMARY}]{count} tests[/{BugsterColors.TEXT_PRIMARY}]"
                )

            # Add always-run tests if any
            if always_run_count > 0:
                content.append("")  # Empty line for spacing
                content.append(
                    f"🎯 [{BugsterColors.TEXT_DIM}]Always-run tests[/{BugsterColors.TEXT_DIM}]"
                )
                if always_run_distribution:
                    for folder, count in sorted(always_run_distribution.items()):
                        content.append(
                            f"   📁 [{BugsterColors.TEXT_DIM}]{folder}[/{BugsterColors.TEXT_DIM}]"
                        )
                        content.append(
                            f"      ▸ [{BugsterColors.TEXT_PRIMARY}]{count} tests[/{BugsterColors.TEXT_PRIMARY}]"
                        )
                else:
                    content.append(
                        f"   ▸ [{BugsterColors.TEXT_PRIMARY}]{always_run_count} tests[/{BugsterColors.TEXT_PRIMARY}] (additional to limit)"
                    )

        panel_content = "\n".join(content)
        return Panel(
            panel_content,
            title="⚠️  Test Limit Applied",
            border_style=BugsterColors.WARNING,
            padding=(1, 2),
        )


class DestructiveMessages:
    """Messages for the destructive command."""

    @staticmethod
    def analyzing_changes():
        """Show analyzing changes message."""
        console.print(
            f"[{BugsterColors.PRIMARY}]🔍 Analyzing code changes for destructive testing...[/{BugsterColors.PRIMARY}]"
        )

    @staticmethod
    def no_agents_assigned():
        """Show no agents assigned message."""
        console.print(
            f"[{BugsterColors.WARNING}]⚠️  No destructive agents assigned - no changes require testing[/{BugsterColors.WARNING}]"
        )

    @staticmethod
    def running_agents_status(agent_count, max_concurrent):
        """Show running agents status message."""
        console.print(
            f"[{BugsterColors.INFO}]🤖 Running {agent_count} destructive agents (max {max_concurrent} concurrent)[/{BugsterColors.INFO}]"
        )

    @staticmethod
    def executing_agents():
        """Show executing agents message."""
        console.print(
            f"[{BugsterColors.INFO}]⚡ Executing destructive agents...[/{BugsterColors.INFO}]"
        )

    @staticmethod
    def create_results_panel(results, total_bugs, total_time):
        """Create and show destructive results panel."""
        pages_tested = len(set(r.page for r in results))
        agents_executed = len(results)

        # Get summary by agent type
        agent_summary = {}
        for result in results:
            agent = result.agent
            if agent not in agent_summary:
                agent_summary[agent] = {"executions": 0, "bugs_found": 0}
            agent_summary[agent]["executions"] += 1
            agent_summary[agent]["bugs_found"] += len(result.result.bugs)

        panel_content = f"""
[bold]🔍 Destructive Testing Summary[/bold]

📊 Results:
  • Pages tested: {pages_tested}
  • Agents executed: {agents_executed}
  • Total bugs found: {total_bugs}
  • Execution time: {total_time:.2f}s

🤖 Agent breakdown:
"""
        for agent, stats in agent_summary.items():
            panel_content += (
                f"  • {agent}: {stats['executions']} runs, {stats['bugs_found']} bugs\n"
            )

        if total_bugs > 0:
            panel_content += f"\n[bold][{BugsterColors.WARNING}]⚠️  Review the bugs found above[/{BugsterColors.WARNING}][/bold]"

        style = BugsterColors.SUCCESS if total_bugs == 0 else BugsterColors.WARNING
        console.print(Panel(panel_content.strip(), border_style=style))

    @staticmethod
    def create_bugs_details_panel(results):
        """Create and show detailed bugs found by destructive agents."""
        if not results:
            return

        # Filter results that have bugs
        results_with_bugs = [r for r in results if r.result.bugs]

        if not results_with_bugs:
            return

        console.print()
        console.print(
            f"[bold][{BugsterColors.WARNING}]🐛 Bugs Found Details[/{BugsterColors.WARNING}][/bold]"
        )
        console.print()

        for result in results_with_bugs:
            # Create panel for each page/agent combination
            page_display = result.page.replace("apps/", "").replace("src/", "")
            panel_title = f"🤖 {result.agent} → 📄 {page_display}"

            bugs_content = ""
            for i, bug in enumerate(result.result.bugs, 1):
                bugs_content += f"[bold][{BugsterColors.ERROR}]{i}. {bug.name}[/{BugsterColors.ERROR}][/bold]\n"
                bugs_content += f"   {bug.description}\n"
                if i < len(result.result.bugs):
                    bugs_content += "\n"

            console.print(
                Panel(
                    bugs_content.strip(),
                    title=panel_title,
                    border_style=BugsterColors.ERROR,
                    padding=(1, 2),
                )
            )

    @staticmethod
    def error(message):
        """Show error message."""
        console.print(
            f"[{BugsterColors.ERROR}]Error: {message}[/{BugsterColors.ERROR}]"
        )

    @staticmethod
    def streaming_results_to_run(run_id):
        """Show streaming results message."""
        console.print(
            f"[{BugsterColors.INFO}]Streaming destructive results to run: {run_id}[/{BugsterColors.INFO}]"
        )

    @staticmethod
    def streaming_warning(agent_info, error):
        """Show streaming warning message."""
        console.print(
            f"[{BugsterColors.WARNING}]Warning: Failed to stream result for {agent_info}: {str(error)}[/{BugsterColors.WARNING}]"
        )

    @staticmethod
    def streaming_init_warning(error):
        """Show streaming initialization warning message."""
        console.print(
            f"[{BugsterColors.WARNING}]Warning: Failed to initialize destructive streaming service: {str(error)}[/{BugsterColors.WARNING}]"
        )

    @staticmethod
    def updating_final_status():
        """Show updating final status message."""
        console.print(
            f"[{BugsterColors.INFO}]Updating final destructive run status...[/{BugsterColors.INFO}]"
        )
