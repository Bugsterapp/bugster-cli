import os

import typer
from rich.console import Console
from rich.status import Status

from bugster.analytics import track_command
from bugster.analyzer import analyze_codebase
from bugster.analyzer.utils.analysis_tracker import (
    analysis_tracker,
    has_analysis_completed,
)
from bugster.commands.middleware import require_api_key
from bugster.constants import TESTS_DIR, WORKING_DIR
from bugster.libs.services.test_cases_service import TestCasesService

console = Console()


@require_api_key
@track_command("generate")
def analyze_command(options: dict = {}, use_new_endpoints: bool = False):
    """Run Bugster CLI analysis command."""
    force = options.get("force", False)

    try:
        if has_analysis_completed() and not force:
            console.print(
                "🔒 The codebase has already been analyzed and cannot be run again"
            )
            return
        with analysis_tracker():
            console.print("🔍 Starting analysis...")

            with Status(" Analyzing codebase...", spinner="dots") as status:
                analyze_codebase(options=options)
                status.stop()
                console.print("✅ Analysis completed!")

            TestCasesService().generate_test_cases(use_new_endpoints=use_new_endpoints)
            console.print()
            console.print("📁 Test cases saved to:")
            console.print(f"   {os.path.relpath(TESTS_DIR, WORKING_DIR)}")
    except Exception as err:
        console.print(f"[red]Error: {str(err)}[/red]")
        raise typer.Exit(1)
