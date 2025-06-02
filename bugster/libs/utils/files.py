import os

from bugster.constants import TESTS_DIR


def get_specs_paths() -> list[str]:
    """Get all spec files paths in the tests directory."""
    file_paths = []

    for root, _, files in os.walk(TESTS_DIR):
        if "example" in root:
            continue

        for file in files:
            file_paths.append(os.path.join(root, file))

    return file_paths
