"""Command-line interface for Bugster."""

import asyncio
import atexit
import sys
from typing import Optional

import click
import typer
from rich.console import Console
from loguru import logger

from bugster import __version__
from bugster.analytics import get_analytics
from bugster.utils.console_messages import CLIMessages

app = typer.Typer(
    name="bugster",
    add_completion=False,
    rich_markup_mode="rich",
    context_settings={"help_option_names": ["-h", "--help"]},
    help=CLIMessages.get_main_help(),
)
console = Console()


def version_callback(value: bool):
    if value:
        # Create a styled version output
        console = Console()
        console.print()

        # Print version header
        for message, justify in CLIMessages.get_version_header(__version__):
            if justify:
                console.print(message, justify=justify)
            else:
                console.print()

        raise typer.Exit()


def configure_logging(debug: bool):
    """Configure loguru logging based on debug flag."""
    # Remove all existing handlers
    logger.remove()

    if debug:
        # Add comprehensive logging when debug is enabled
        logger.add(
            sys.stdout,
            level="DEBUG",
            filter=lambda record: record["level"].name == "DEBUG",
        )
        logger.add(
            sys.stdout,
            level="INFO",
            filter=lambda record: record["level"].name == "INFO",
        )
        logger.add(
            sys.stdout,
            level="WARNING",
            filter=lambda record: record["level"].name == "WARNING",
        )
        logger.add(
            sys.stderr,
            level="ERROR",
            filter=lambda record: record["level"].name == "ERROR",
        )

    # When debug is False, suppress all logs except CRITICAL
    # This maintains compatibility with existing patterns
    logger.add(sys.stderr, level="CRITICAL")  # Discard the message


# Global variable to track debug state for other modules
_debug_enabled = False


def is_debug_enabled() -> bool:
    """Check if debug logging is enabled."""
    return _debug_enabled


@app.callback()
def main_callback(
    version: bool = typer.Option(
        None,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="Print the version and exit",
    ),
    debug: bool = typer.Option(
        False,
        "--debug",
        help="Enable debug logging",
    ),
):
    """🐛 Bugster CLI - AI-powered end-to-end testing for web applications"""
    global _debug_enabled
    _debug_enabled = debug
    configure_logging(debug)
    analytics = get_analytics()
    atexit.register(analytics.flush)


@app.command()
def init():
    """Initialize Bugster CLI configuration in your project."""
    from bugster.commands.init import init_command

    init_command()


def _run_tests(
    path: Optional[str] = typer.Argument(None, help="Path to test file or directory"),
    headless: Optional[bool] = typer.Option(
        False, "--headless", help="Run tests in headless mode"
    ),
    silent: Optional[bool] = typer.Option(
        False, "--silent", "-s", help="Run in silent mode (less verbose output)"
    ),
    stream_results: Optional[bool] = typer.Option(
        False, "--stream-results", help="Stream test results as they complete"
    ),
    output: Optional[str] = typer.Option(
        None, "--output", help="Save test results to JSON file"
    ),
    run_id: Optional[str] = typer.Option(
        None, "--run-id", help="Run ID to associate with the test run"
    ),
    base_url: Optional[str] = typer.Option(
        None, "--base-url", help="Base URL to use for the test run"
    ),
    only_affected: Optional[bool] = typer.Option(
        None, "--only-affected", help="Only run tests for affected files or directories"
    ),
    max_concurrent: Optional[int] = typer.Option(
        None, "--max-concurrent", help="Maximum number of concurrent tests"
    ),
    verbose: Optional[bool] = typer.Option(False, "--verbose", help="Verbose output"),
):
    """Run your Bugster tests."""
    from bugster.commands.test import test_command

    asyncio.run(
        test_command(
            path,
            headless,
            silent,
            stream_results,
            output,
            run_id,
            base_url,
            only_affected,
            max_concurrent,
            verbose,
        )
    )


# Register the same function with two different command names
app.command(name="test", help=CLIMessages.get_run_help())(_run_tests)
app.command(name="run", help=CLIMessages.get_run_help())(_run_tests)


def _analyze_codebase(
    show_logs: bool = typer.Option(
        False,
        "--show-logs",
        help="Show detailed logs during analysis",
    ),
    force: bool = typer.Option(
        False,
        "-f",
        "--force",
        help="Force analysis even if the codebase has already been analyzed",
    ),
):
    """Analyze your codebase and generate test specs."""
    from bugster.commands.analyze import analyze_command

    analyze_command(options={"show_logs": show_logs, "force": force}, use_new_endpoints=True)


# Register the same function with two different command names
app.command(name="analyze", help=CLIMessages.get_analyze_help())(_analyze_codebase)
app.command(name="generate", help=CLIMessages.get_analyze_help())(_analyze_codebase)


@app.command(help=CLIMessages.get_update_help())
def update(
    update_only: bool = typer.Option(
        False, help="Only update existing specs, no suggestions or deletes"
    ),
    suggest_only: bool = typer.Option(
        False, help="Only suggest new specs, no updates or deletes"
    ),
    delete_only: bool = typer.Option(
        False, help="Only delete specs, no updates or suggestions"
    ),
    show_logs: bool = typer.Option(
        False,
        "--show-logs",
        help="Show detailed logs during analysis",
    ),
):
    """Update your test specs with the latest changes."""
    from bugster.commands.update import update_command

    update_command(
        update_only=update_only,
        suggest_only=suggest_only,
        delete_only=delete_only,
        show_logs=show_logs,
    )


@app.command(help=CLIMessages.get_sync_help())
def sync(
    branch: Optional[str] = typer.Option(
        None, help="Branch to sync with (defaults to current git branch or 'main')"
    ),
    pull: bool = typer.Option(False, help="Only pull specs from remote"),
    push: bool = typer.Option(False, help="Only push specs to remote"),
    clean_remote: bool = typer.Option(
        False, help="Delete remote specs that don't exist locally"
    ),
    dry_run: bool = typer.Option(
        False, help="Show what would happen without making changes"
    ),
    prefer: str = typer.Option(
        None,
        "--prefer",
        help="Prefer 'local' or 'remote' when resolving conflicts",
        click_type=click.Choice(["local", "remote"]),
    ),
):
    """Sync test cases with team."""
    from bugster.commands.sync import sync_command

    sync_command(branch, pull, push, clean_remote, dry_run, prefer)


@app.command(help=CLIMessages.get_upgrade_help())
def upgrade(
    yes: bool = typer.Option(
        False,
        "--yes",
        "-y",
        help="Automatically confirm the upgrade.",
    ),
):
    """Upgrade Bugster CLI to the latest version."""
    from bugster.commands.upgrade import upgrade_command

    upgrade_command(yes=yes)
    
@app.command()
def issues(
    history: bool = typer.Option(
        False,
        "--history",
        help="Get issues from the last week. If more than 10 issues are found, they will be saved to .bugster/issues directory"
    ),
    save: bool = typer.Option(
        False,
        "--save",
        "-s",
        help="Save issues to .bugster/issues directory"
    ),
    project_id: Optional[str] = typer.Option(
        None,
        "--project-id",
        "-p",
        help="Project ID (defaults to the one from config.yaml)"
    )
):
    """[bold red]Get[/bold red] issues from your Bugster project."""
    from bugster.commands.issues import issues_command
    issues_command(history=history, save=save, project_id=project_id)


def main():
    app()


if __name__ == "__main__":
    main()
