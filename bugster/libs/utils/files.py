import fnmatch
import os
from typing import Callable, Optional

import yaml
from loguru import logger

from bugster.constants import IGNORE_PATTERNS, TESTS_DIR


def get_specs_paths(
    relatives_to: Optional[str] = None, folder_name: Optional[str] = None
) -> list[str]:
    """Get all spec files paths in the tests directory."""
    file_paths = []
    dir = os.path.join(TESTS_DIR, folder_name) if folder_name else TESTS_DIR

    for root, _, files in os.walk(dir):
        for file in files:
            full_path = os.path.join(root, file)

            if relatives_to:
                full_path = os.path.relpath(full_path, start=relatives_to)

            file_paths.append(full_path)

    return file_paths


def parse_spec_page(data, spec_path) -> dict[str, dict]:
    """Default parser for spec page."""
    return {
        "data": data,
        "path": os.path.relpath(spec_path, TESTS_DIR),
    }


def get_specs_pages(parser: Callable = parse_spec_page) -> dict[str, list[dict]]:
    """Get the specs pages."""
    specs_paths = get_specs_paths()
    specs_pages = {}

    for spec_path in specs_paths:
        with open(spec_path, encoding="utf-8") as file:
            try:
                data = yaml.safe_load(file)

                if isinstance(data, list):
                    if not data:
                        raise ValueError(f"Empty list in spec file: {spec_path}")

                    data = data[0]
                elif not isinstance(data, dict):
                    raise ValueError(f"Invalid spec file: {spec_path}")

                if "page_path" not in data:
                    raise ValueError(f"Missing 'page_path' in spec file: {spec_path}")

                page_path = data["page_path"]
                parsed_spec = parser(data=data, spec_path=spec_path)

                # Handle multiple specs with the same page_path
                if page_path in specs_pages:
                    specs_pages[page_path].append(parsed_spec)
                else:
                    specs_pages[page_path] = [parsed_spec]
            except Exception as err:
                logger.error("Error parsing spec file '{}': {}", spec_path, err)

    return specs_pages


def filter_path(
    path: str, allowed_extensions: Optional[list[str]] = None
) -> Optional[str]:
    """Filter a single path based on ignore patterns and `.gitignore` rules."""
    from bugster.libs.utils.git import get_gitignore

    gitignore = get_gitignore()
    GITIGNORE_PATH = ".gitignore"

    if not allowed_extensions:
        allowed_extensions = [".ts", ".tsx", ".js", ".jsx"]

    if not any(path.endswith(ext) for ext in allowed_extensions):
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
