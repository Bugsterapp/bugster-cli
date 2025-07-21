"""
Test limit logic for Bugster CLI
"""

from collections import defaultdict
from pathlib import Path
from typing import List, Optional


def apply_test_limit(
    test_files: List[dict], max_tests: Optional[int] = None
) -> tuple[List[dict], dict]:
    """
    Apply test limit logic to select a representative subset of tests.

    Args:
        test_files: List of test file dictionaries with 'file' and 'content' keys
        max_tests: Maximum number of tests to run (if None, no limit)

    Returns:
        Tuple of (limited list of test files, folder distribution dict)
    """
    if max_tests is None:
        return test_files, {}

    # Count total individual test cases
    total_test_cases = count_total_tests(test_files)

    if total_test_cases <= max_tests:
        return test_files, {}

    # Group tests by folder
    folder_groups = group_tests_by_folder(test_files)

    # Apply distribution logic
    selected_tests, folder_distribution = select_representative_tests(
        folder_groups, max_tests
    )

    return selected_tests, folder_distribution


def group_tests_by_folder(test_files: List[dict]) -> dict[str, List[dict]]:
    """
    Group test files by their parent folder.

    Args:
        test_files: List of test file dictionaries

    Returns:
        Dictionary mapping folder paths to lists of test files
    """
    folder_groups = defaultdict(list)

    for test_file in test_files:
        file_path = Path(test_file["file"])

        # Get the parent folder relative to the tests directory
        # Handle different path structures
        parts = file_path.parts
        if len(parts) >= 3 and parts[0] == ".bugster" and parts[1] == "tests":
            # Standard case: .bugster/tests/folder/file.yaml
            if len(parts) > 3:
                folder = parts[2]  # The folder after 'tests'
            else:
                folder = "root"  # File directly in tests folder
        else:
            # Fallback: use parent directory name
            folder = (
                file_path.parent.name if file_path.parent.name != "tests" else "root"
            )

        folder_groups[folder].append(test_file)

    return dict(folder_groups)


def select_representative_tests(
    folder_groups: dict[str, List[dict]], max_tests: int
) -> tuple[List[dict], dict]:
    """
    Select representative tests from folder groups based on distribution logic.

    Args:
        folder_groups: Dictionary mapping folder names to test files
        max_tests: Maximum number of tests to select

    Returns:
        Tuple of (list of selected test files, folder distribution dict)
    """
    num_folders = len(folder_groups)
    selected_tests = []
    folder_distribution = {}

    if num_folders == 0:
        return [], {}

    # Calculate tests per folder: A = MAX / M
    tests_per_folder = max_tests / num_folders

    if tests_per_folder >= 1:
        # Case 1: We can run multiple tests per folder
        tests_per_folder_int = int(tests_per_folder)
        remaining_tests = max_tests % num_folders

        # Sort folders by name for consistent behavior
        sorted_folders = sorted(folder_groups.keys())

        for i, folder in enumerate(sorted_folders):
            folder_tests = folder_groups[folder]

            # Some folders get one extra test to use up remaining slots
            tests_to_take = tests_per_folder_int + (1 if i < remaining_tests else 0)
            tests_to_take = min(tests_to_take, len(folder_tests))

            if tests_to_take > 0:
                selected_tests.extend(folder_tests[:tests_to_take])
                folder_distribution[folder] = tests_to_take

            if len(selected_tests) >= max_tests:
                break

    else:
        # Case 2: More folders than max_tests, select one test from first M folders
        sorted_folders = sorted(folder_groups.keys())

        for i, folder in enumerate(sorted_folders):
            if i >= max_tests:
                break

            folder_tests = folder_groups[folder]
            if folder_tests:
                selected_tests.append(folder_tests[0])
                folder_distribution[folder] = 1
    return selected_tests[:max_tests], folder_distribution


def count_total_tests(test_files: List[dict]) -> int:
    """
    Count total number of individual test cases across all files.

    Args:
        test_files: List of test file dictionaries

    Returns:
        Total number of test cases
    """
    total = 0
    for test_file in test_files:
        content = test_file.get("content", [])
        if isinstance(content, list):
            total += len(content)
        else:
            total += 1
    return total


def get_test_limit_from_config() -> Optional[int]:
    """
    Get test limit from configuration.

    Returns:
        Maximum number of tests to run, or None if no limit
    """
    try:
        from bugster.utils.file import load_config

        config = load_config()

        # Check if limit is configured in preferences.tests
        if config.preferences and config.preferences.limit is not None:
            return config.preferences.limit

        # Fallback to default
        return 10
    except Exception:
        # If config loading fails, return default
        return 10
