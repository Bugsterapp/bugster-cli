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
