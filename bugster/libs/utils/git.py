import os
import subprocess
from collections import defaultdict

import pathspec
from loguru import logger

from bugster.constants import WORKING_DIR
from bugster.libs.utils.diff_parser import parse_git_diff
from bugster.libs.utils.enums import GitCommand
from bugster.libs.utils.files import filter_path


def run_git_command(
    cmd_key: GitCommand,
    capture_output: bool = True,
    text: bool = True,
    check: bool = True,
):
    """Run a git command with automatic staging/unstaging."""
    try:
        # Add the unstaged files — diff head only works with intent-to-add files
        if cmd_key == GitCommand.DIFF_HEAD:
            subprocess.run(GitCommand.ADD_INTENT, check=True)

        result = subprocess.run(
            cmd_key,
            capture_output=capture_output,
            text=text,
            check=check,
        )
        return result.stdout
    finally:
        # Reset the intent-to-add files
        if cmd_key == GitCommand.DIFF_HEAD:
            subprocess.run(GitCommand.RESET, check=True)


def get_gitignore(dir_path: str = WORKING_DIR):
    """Get the `.gitignore` rules for a directory."""
    try:
        gitignore_path = os.path.join(dir_path, ".gitignore")

        if os.path.exists(gitignore_path):
            with open(gitignore_path) as f:
                gitignore = pathspec.PathSpec.from_lines(
                    pathspec.patterns.GitWildMatchPattern, f.readlines()
                )
        else:
            gitignore = None
    except ImportError:
        gitignore = None

    return gitignore


def parse_diff_status(diff_status: str):
    """Parse git status --porcelain output into categorized file lists.

    Git status codes (first char = staged, second char = unstaged):
    Staged codes (X_):
    - M = Modified
    - A = Added (new file)
    - D = Deleted
    - R = Renamed
    - C = Copied
    - U = Updated but unmerged

    Unstaged codes (_Y):
    - M = Modified
    - D = Deleted
    - R = Type changed (file/symlink/submodule)
    - U = Updated but unmerged
    - ? = Untracked
    - ! = Ignored

    Special cases:
    - ?? = Untracked file
    - !! = Ignored file

    :param diff_status: Raw output from 'git status --porcelain'.
    :return: Dictionary with 'modified', 'deleted', and 'new' file lists.
    """
    result = {"modified": [], "deleted": [], "new": []}

    # Split by newlines and filter out empty lines
    lines = [line for line in diff_status.strip().split("\n") if line.strip()]

    for line in lines:
        if len(line) < 3:  # Skip malformed lines
            continue

        status_code = line[:2]  # First two characters are the status
        filename = line[2:]  # Rest is the filename
        filename = filename.strip()  # Remove any leading/trailing whitespace

        if not filter_path(path=filename):
            continue

        # Handle special two-character codes first
        if status_code == "??":
            # Untracked file - treat as new
            result["new"].append(filename)
            continue
        elif status_code == "!!":
            # Ignored file - skip (not typically needed for most use cases)
            continue

        # Get individual status characters
        staged = status_code[0]
        unstaged = status_code[1]

        # Determine file category based on status codes
        # Priority: deleted > new > modified (since a file can have multiple states)

        is_deleted = False
        is_new = False
        is_modified = False

        # Check for deletions (highest priority)
        if staged == "D" or unstaged == "D":
            is_deleted = True

        # Check for new files
        elif staged == "A" or staged == "C":  # Added/staged new file
            is_new = True

        # Check for modifications
        elif (
            staged == "M"
            or unstaged == "M"
            or staged == "R"
            or unstaged == "R"
            or staged == "U"
            or unstaged == "U"
        ):
            is_modified = True

        # Handle edge cases where both staged and unstaged have status
        # For example: "AM" = added then modified, "AD" = added then deleted
        if staged != " " and unstaged != " ":
            if staged == "A" and unstaged == "D":
                # Added then deleted - treat as deleted
                is_deleted = True
                is_new = False
            elif staged == "A" and unstaged == "M":
                # Added then modified - treat as new (since it's still a new file overall)
                is_new = True
                is_modified = False
            elif staged == "M" and unstaged == "D":
                # Modified then deleted - treat as deleted
                is_deleted = True
                is_modified = False
            elif staged == "D" and unstaged == "M":
                # This shouldn't normally happen, but treat as modified
                is_modified = True
                is_deleted = False

        # Categorize the file
        if is_deleted:
            result["deleted"].append(filename)
        elif is_new:
            result["new"].append(filename)
        elif is_modified:
            result["modified"].append(filename)
        # If none of the above, it might be an unhandled status code
        # For robustness, you could add an 'unknown' category or default to 'modified'

    logger.info("Parsed diff status!")
    return result


def parse_diff_name_status(diff_name_status: str):
    """Parse git diff --name-status output into categorized file lists.

    Git diff --name-status output format:
    - M = Modified
    - A = Added
    - D = Deleted
    - R = Renamed (shows as R100 filename1 filename2)
    - C = Copied (shows as C100 filename1 filename2)

    :param diff_name_status: Raw output from 'git diff --name-status'.
    :return: Dictionary with 'modified', 'deleted', and 'new' file lists.
    """
    result = {"modified": [], "deleted": [], "new": []}

    # Split by newlines and filter out empty lines
    lines = [line for line in diff_name_status.strip().split("\n") if line.strip()]

    for line in lines:
        if not line.strip():
            continue

        parts = line.split("\t")
        if len(parts) < 2:
            continue

        status_code = parts[0].strip()
        filename = parts[1].strip()

        if not filter_path(path=filename):
            continue

        # Handle the status codes
        if status_code.startswith("D"):
            result["deleted"].append(filename)
        elif status_code.startswith("A"):
            result["new"].append(filename)
        elif status_code.startswith("M"):
            result["modified"].append(filename)
        elif status_code.startswith("R") or status_code.startswith("C"):
            result["modified"].append(filename)
            continue

    logger.info("Parsed diff name status!")
    return result


def get_diff_changes_per_page(
    import_tree: dict, git_command: GitCommand
) -> dict[str, list[str]]:
    """Get the diff changes per page.

    :param import_tree: The import tree of the user's repository.
    :return: A dictionary with the page path as the key and the diff changes as the values.
    """
    from bugster.libs.utils.nextjs.pages_finder import (
        find_pages_that_use_file,
        is_nextjs_page,
    )

    diff_changes_per_page = defaultdict(list)
    diff_changes = run_git_command(cmd_key=git_command)
    parsed_diff = parse_git_diff(diff_text=diff_changes)

    for file_change in parsed_diff.files:
        old_path = file_change.old_path

        if is_nextjs_page(file_path=old_path):
            new_diff = parsed_diff.to_llm_format(file_change=file_change)
            git_prefix_path = get_git_prefix_path()
            relative_path = old_path[len(git_prefix_path) :].lstrip("/")
            diff_changes_per_page[relative_path].append(new_diff)
        else:
            pages = find_pages_that_use_file(
                file_path=old_path, import_tree=import_tree
            )

            if pages:
                for page in pages:
                    new_diff = parsed_diff.to_llm_format(file_change=file_change)
                    diff_changes_per_page[page].append(new_diff)

    return diff_changes_per_page


def get_git_prefix_path():
    """Get the git prefix path."""
    return run_git_command(cmd_key=GitCommand.GIT_WORKTREE_PREFIX).strip()
