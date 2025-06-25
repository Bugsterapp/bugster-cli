"""File utility functions for Bugster."""

import json
import tempfile
from pathlib import Path
from typing import List, Optional
import uuid

import typer
import yaml
from rich.console import Console

from bugster.constants import CONFIG_PATH, TESTS_DIR
from bugster.types import Config
from bugster.utils.yaml_spec import load_spec

console = Console()


def load_config() -> Config:
    """Load configuration from config.yaml."""
    if not CONFIG_PATH.exists():
        console.print(
            "[red]Error: Configuration file not found. Please run 'bugster init' first.[/red]"
        )
        raise typer.Exit(1)

    with open(CONFIG_PATH) as f:
        return Config(**yaml.safe_load(f))


def load_test_files(test_path: Optional[Path] = None) -> List[dict]:
    """Load test files from the given path or all tests if no path specified."""
    test_files = []

    if test_path is None:
        test_path = TESTS_DIR
    if not test_path.exists():
        console.print(f"[red]Error: Path {test_path} does not exist[/red]")
        raise typer.Exit(1)

    def process_yaml_file(file_path: Path) -> dict:
        """Process a single YAML file and return its specs."""
        try:
            test_cases = load_spec(file_path)
            # Convert specs to the expected format
            content = []
            for test_case in test_cases:
                test_data = test_case.data
                # Add metadata as hidden fields
                test_data["metadata"] = {
                    "id": test_case.metadata.id,
                    "last_modified": test_case.metadata.last_modified,
                }
                content.append(test_data)
            return {"file": file_path, "content": content}
        except Exception as e:
            console.print(
                f"[yellow]Warning: Failed to load test file {file_path}: {e}[/yellow]"
            )
            return None

    if test_path.is_file():
        if test_path.suffix == ".yaml":
            result = process_yaml_file(test_path)
            if result:
                test_files.append(result)
    else:
        # Recursively find all .yaml files
        for file in test_path.rglob("*.yaml"):
            result = process_yaml_file(file)
            if result:
                test_files.append(result)

    return test_files


def get_mcp_config_path(mcp_config: dict, version: str) -> str:
    """Get the MCP config file path.

    Creates a temporary config file with browser settings.
    """

    # Create a temporary file with a specific name
    temp_dir = tempfile.gettempdir()
    unique_id = str(uuid.uuid4())
    config_path = Path(temp_dir) / f"bugster_mcp_{version}_{unique_id}.config.json"

    # Only create the file if it doesn't exist
    # if not config_path.exists():
    #     # Write the configuration
    #     with open(config_path, "w") as f:
    #         json.dump(mcp_config, f, indent=2)
    with open(config_path, "w") as f:
        json.dump(mcp_config, f, indent=2)

    return str(config_path)


def load_always_run_tests(config: Config) -> List[dict]:
    """Load test files that should always be executed based on config preferences."""
    if not config.preferences or not config.preferences.always_run:
        console.print("[dim]No always-run tests configured[/dim]")
        return []
    
    console.print(f"[dim]Loading always-run tests: {config.preferences.always_run}[/dim]")
    always_run_tests = []
    
    # Check if we exceed the limit of 3
    total_configured = len(config.preferences.always_run)
    if total_configured > 3:
        ignored_tests = config.preferences.always_run[3:]
        console.print(f"[yellow]Warning: Always-run limit exceeded. Only first 3 tests will be executed. Ignoring: {ignored_tests}[/yellow]")
    
    # Limit to 3 tests maximum
    limited_paths = config.preferences.always_run[:3]
    
    for test_path in limited_paths:
        # Remove 'tests/' prefix if present to avoid path duplication
        clean_path = test_path.replace('tests/', '', 1) if test_path.startswith('tests/') else test_path
        
        # Try multiple path variations to find the file
        possible_paths = []
        
        # If path already has extension, try both .yaml and .yml
        if clean_path.endswith('.yaml'):
            possible_paths = [
                TESTS_DIR / clean_path,
                TESTS_DIR / clean_path.replace('.yaml', '.yml')
            ]
        elif clean_path.endswith('.yml'):
            possible_paths = [
                TESTS_DIR / clean_path,
                TESTS_DIR / clean_path.replace('.yml', '.yaml')
            ]
        else:
            # No extension specified, try both
            possible_paths = [
                TESTS_DIR / f"{clean_path}.yaml",
                TESTS_DIR / f"{clean_path}.yml"
            ]
        
        test_found = False
        for full_test_path in possible_paths:
            console.print(f"[dim]Checking always-run test: {full_test_path}[/dim]")
            
            if not full_test_path.exists():
                continue
                
            try:
                test_cases = load_spec(full_test_path)
                content = []
                for test_case in test_cases:
                    test_data = test_case.data
                    test_data["metadata"] = {
                        "id": test_case.metadata.id,
                        "last_modified": test_case.metadata.last_modified,
                    }
                    content.append(test_data)
                
                always_run_tests.append({
                    "file": full_test_path, 
                    "content": content,
                    "always_run": True
                })
                console.print(f"[green]✓ Loaded always-run test: {test_path}[/green]")
                test_found = True
                break
                
            except Exception as e:
                console.print(f"[yellow]Warning: Failed to load always-run test {test_path}: {e}[/yellow]")
                continue
        
        if not test_found:
            console.print(f"[yellow]Warning: Always-run test not found: {test_path}[/yellow]")
    
    console.print(f"[dim]Total always-run tests loaded: {len(always_run_tests)}[/dim]")
    return always_run_tests


def merge_always_run_with_affected_tests(affected_tests: List[dict], always_run_tests: List[dict]) -> List[dict]:
    """Merge always-run tests with affected tests, avoiding duplicates."""
    merged_tests = []
    processed_files = set()
    
    # Add always-run tests first
    for test_file in always_run_tests:
        file_path = str(test_file["file"])
        merged_tests.append(test_file)
        processed_files.add(file_path)
    
    # Add affected tests that aren't already in always-run
    for test_file in affected_tests:
        file_path = str(test_file["file"])
        if file_path not in processed_files:
            merged_tests.append(test_file)
            processed_files.add(file_path)
    
    return merged_tests
