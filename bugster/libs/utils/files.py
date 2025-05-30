import fnmatch
import os
from typing import Optional

import yaml

from bugster.constants import IGNORE_PATTERNS, TESTS_DIR


def get_specs_paths(relatives_to: Optional[str] = None) -> list[str]:
    """Get all spec files paths in the tests directory."""
    file_paths = []

    for root, _, files in os.walk(TESTS_DIR):
        if "example" in root:
            continue

        for file in files:
            full_path = os.path.join(root, file)

            if relatives_to:
                full_path = os.path.relpath(full_path, start=relatives_to)

            file_paths.append(full_path)

    return file_paths


def get_specs_pages():
    """Get the specs pages."""
    specs_files_paths = get_specs_paths()
    specs_pages = {}

    for spec_path in specs_files_paths:
        with open(spec_path, encoding="utf-8") as file:
            data = yaml.safe_load(file)
            page_path = data["page_path"]
            relative_path = os.path.relpath(spec_path, TESTS_DIR)
            specs_pages[page_path] = {
                "data": data,
                "path": relative_path,
            }

    return specs_pages


def filter_path(path: str):
    """Filter a single path based on ignore patterns and `.gitignore` rules."""
    from bugster.libs.utils.git import get_gitignore

    gitignore = get_gitignore()
    GITIGNORE_PATH = ".gitignore"
    ALLOWED_EXTENSIONS = [".ts", ".tsx", ".js", ".jsx"]

    if not any(path.endswith(ext) for ext in ALLOWED_EXTENSIONS):
        return None

    if os.path.isdir(path):
        return None

    if any(fnmatch.fnmatch(path, pattern) for pattern in IGNORE_PATTERNS):
        return None

    if gitignore and gitignore.match_file(path):
        return None

    if path == GITIGNORE_PATH:
        return None

    return path.replace(os.sep, "/")
