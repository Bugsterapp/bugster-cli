import os
import subprocess
import sys

import yaml
from loguru import logger
from rich.console import Console
from rich.text import Text
from yaspin import yaspin

from bugster.analyzer.core.app_analyzer.utils.get_tree_structure import (
    filter_paths,
    get_gitignore,
)
from bugster.constants import TESTS_DIR, WORKING_DIR
from bugster.libs.services.test_cases_service import TestCasesService
from bugster.libs.utils.diff_parser import parse_git_diff
from bugster.libs.utils.files import get_specs_paths
from bugster.libs.utils.nextjs.pages_finder import find_pages_that_use_file

console = Console()


def update_command(options: dict = {}):
    """Run Bugster CLI update command."""
    logger.remove()
    logger.add(sys.stderr, level="CRITICAL")
    console.print("✓ Analyzing code changes...")
    cmd = ["git", "diff", "--", "."]

    for pattern in [
        "package-lock.json",
        ".env.local",
        ".gitignore",
        "tsconfig.json",
        ".env",
    ]:
        cmd.append(f":!{pattern}")

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=True,
    )
    diff_changes = result.stdout
    cmd.insert(2, "--name-only")
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=True,
    )
    diff_files = result.stdout
    diff_files_paths = [path for path in diff_files.split("\n") if path.strip()]
    gitignore = get_gitignore(dir_path=WORKING_DIR)
    diff_files_paths = filter_paths(all_paths=diff_files_paths, gitignore=gitignore)
    console.print(f"✓ Found {len(diff_files_paths)} modified files")
    affected_pages = set()
    is_page_file = lambda file: file.endswith(
        (".page.js", ".page.jsx", ".page.ts", ".page.tsx")
    )

    for file in diff_files_paths:
        if is_page_file(file=file):
            affected_pages.add(file)
        else:
            pages = find_pages_that_use_file(file_path=file)

            if pages:
                for page in pages:
                    affected_pages.add(page)

    specs_files_paths = get_specs_paths()
    specs_pages = {}

    for spec_path in specs_files_paths:
        with open(spec_path, "r", encoding="utf-8") as file:
            data = yaml.safe_load(file)
            page_path = data["page_path"]
            relative_path = os.path.relpath(spec_path, TESTS_DIR)
            specs_pages[page_path] = {
                "data": data,
                "path": relative_path,
            }

    diff_changes_per_page = {}
    parsed_diff = parse_git_diff(diff_text=diff_changes)

    for diff in parsed_diff.files:
        old_path = diff.old_path

        if is_page_file(file=old_path):
            diff_changes_per_page[old_path] = parsed_diff.to_llm_format(
                file_change=diff
            )
        else:
            pages = find_pages_that_use_file(file_path=old_path)

            if pages:
                for page in pages:
                    diff_changes_per_page[page] = parsed_diff.to_llm_format(
                        file_change=diff
                    )

    service = TestCasesService()
    updated_specs = 0
    suggested_specs = []

    for page in affected_pages:
        if page in specs_pages:
            spec = specs_pages[page]
            spec_data = spec["data"]
            spec_path = spec["path"]

            with yaspin(text=f"Updating: {spec_path}", color="yellow") as spinner:
                diff = diff_changes_per_page[page]
                service.update_spec_by_diff(
                    spec_data=spec_data, diff_changes=diff, spec_path=spec_path
                )

                with spinner.hidden():
                    console.print(f"✓ [green]{spec_path}[/green] updated")

                updated_specs += 1
        else:
            text = Text("✗ Page ")
            text.append(page, style="red")
            text.append(" not found in test cases")
            console.print(text)

            # TODO: Implement the real logic for this
            import re

            def camel_to_kebab(text):
                """Convert camelCase to kebab-case."""
                return re.sub(r"([a-z0-9])([A-Z])", r"\1-\2", text).lower()

            def suggest_spec_from_page(page_path):
                clean_path = re.sub(r"^src/pages/", "", page_path)
                clean_path = re.sub(r"\.(tsx?|jsx?)$", "", clean_path)

                def replace_dynamic(match):
                    param = match.group(1)
                    return camel_to_kebab(param)

                clean_path = re.sub(r"\[([^\]]+)\]", replace_dynamic, clean_path)

                clean_path = camel_to_kebab(clean_path)
                return f"{clean_path}.yaml"

            suggested_specs.append(suggest_spec_from_page(page))

    if len(suggested_specs) > 0:
        for spec in suggested_specs:
            console.print(f"⚠️  Suggested new spec: {spec}")

    if updated_specs > 0 and len(suggested_specs) > 0:
        console.print(
            f"✓ Updated {updated_specs} spec{'' if updated_specs == 1 else 's'}, {len(suggested_specs)} suggestion{'' if len(suggested_specs) == 1 else 's'}"
        )
    elif updated_specs > 0:
        console.print(
            f"✓ Updated {updated_specs} spec{'' if updated_specs == 1 else 's'}"
        )
