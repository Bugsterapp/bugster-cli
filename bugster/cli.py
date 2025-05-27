"""
Command-line interface for Bugster.
"""

import asyncio
import typer
from rich.console import Console
from typing import Optional


HELP_TEXT = """
🐛 [bold cyan]Bugster CLI[/bold cyan]
"""
app = typer.Typer(
    name="bugster",
    help=HELP_TEXT,
    add_completion=False,
    rich_markup_mode="rich",
    context_settings={"help_option_names": ["-h", "--help"]},
)
console = Console()


@app.command()
def login():
    """[bold blue]Login[/bold blue] to Bugster by setting up your API key."""
    from bugster.commands.login import login_command

    login_command()


@app.command()
def init():
    """[bold green]Initialize[/bold green] Bugster CLI configuration in your project."""
    from bugster.commands.init import init_command

    init_command()


@app.command()
def test(
    path: Optional[str] = typer.Argument(None, help="Path to test file or directory"),
    headless: Optional[bool] = typer.Option(
        False, "--headless", help="Run tests in headless mode"
    ),
    silent: Optional[bool] = typer.Option(
        False, "--silent", "-s", help="Run in silent mode (less verbose output)"
    ),
):
    """[bold yellow]Run[/bold yellow] Bugster tests. If no path is provided, runs all tests in .bugster/tests."""
    from bugster.commands.test import test_command

    asyncio.run(test_command(path, headless, silent))


@app.command()
def analyze(
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
    """[bold magenta]Analyze[/bold magenta] your codebase generates test specs"""
    from bugster.commands.analyze import analyze_command

    analyze_command(options={"show_logs": show_logs, "force": force})


@app.command()
def sync():
    """[bold magenta]Sync[/bold magenta] your codebase with Bugster."""
    from bugster.commands.sync import sync_command

    sync_command()


def main():
    app()


if __name__ == "__main__":
    main()
