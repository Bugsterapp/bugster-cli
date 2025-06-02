from rich.console import Console
from yaspin import yaspin

from bugster.analyzer import analyze_codebase

# from bugster.commands.middleware import require_api_key
from bugster.libs.services.test_cases_service import TestCasesService

console = Console()


# @require_api_key
def analyze_command(options: dict = {}):
    """Run Bugster CLI analysis command."""
    console.print("🔍 Running codebase analysis...")
    analyze_codebase(options=options)
    console.print("✅ Analysis completed!")

    with yaspin(text=" Generating test cases...", color="yellow") as spinner:
        test_cases_dir_path = TestCasesService().generate_test_cases()
        spinner.text = "Test cases generation completed!"
        spinner.ok("🎉")

    console.print(f"💾 Test cases saved to directory '{test_cases_dir_path}'")
