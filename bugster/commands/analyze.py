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
from bugster.utils.console_messages import AnalyzeMessages

console = Console()


@require_api_key
@track_command("generate")
def analyze_command(options: dict = {}):
    """Run Bugster CLI analysis command."""
    force = options.get("force", False)
    page_filter = options.get("page_filter", None)
    count = options.get("count", None)
    try:
        if has_analysis_completed() and not force:
            AnalyzeMessages.analysis_already_completed()
            return
        with analysis_tracker():
            AnalyzeMessages.starting_analysis()

            with Status(
                AnalyzeMessages.analyzing_codebase_status(), spinner="dots"
            ) as status:
                analyze_codebase(options=options)
                status.stop()
                AnalyzeMessages.analysis_completed()
            TestCasesService().generate_test_cases(page_filter=page_filter, count=count)
            console.print()

            path = os.path.relpath(TESTS_DIR, WORKING_DIR)
            if page_filter:
                AnalyzeMessages.specs_generated_for_files()
                for file_path in page_filter:
                    AnalyzeMessages.print_file_path(file_path)
                AnalyzeMessages.specs_saved_to(path)
            else:
                AnalyzeMessages.generic_specs_saved_to(path)

    except Exception as err:
        AnalyzeMessages.error(str(err))
        raise typer.Exit(1)
