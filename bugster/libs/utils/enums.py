from enum import Enum


class BugsterApiPath(str, Enum):
    """Bugster API paths."""

    TEST_CASES = "/api/v1/test-cases"
    TEST_CASES_NEW = "/api/v1/test-cases/new"


class GitCommand(list, Enum):
    """Git commands.

    - CURRENT_BRANCH: Get the current branch name.
    - DIFF_STATUS_PORCELAIN: Get the file paths of all files that have been added, deleted, or modified in the repository.
    - ADD_INTENT: Add the unstaged files.
    - DIFF_HEAD: Get the changed content of all files that have been added, deleted, or modified in the repository.
    - DIFF_CHANGES: Get the changed content of the modified and deleted *UNSTAGED* files.
    - DIFF_BRANCH_HEAD: Get the changed content between the current branch and the target branch.
    - DIFF_CACHED: Get the changed content of the modified or deleted *STAGED* files.
    - RESET: Remove all intent-to-add files.
    """

    CURRENT_BRANCH = ["git", "rev-parse", "--abbrev-ref", "HEAD"]
    DIFF_STATUS_PORCELAIN = [
        "git",
        "status",
        "--porcelain",
        "--",
        "*.tsx",
        "*.ts",
        "*.js",
        "*.jsx",
    ]
    ADD_INTENT = ["git", "add", "-N", "."]
    DIFF_HEAD = [
        "git",
        "diff",
        "HEAD",
        "--",
        "*.tsx",
        "*.ts",
        "*.js",
        "*.jsx",
    ]
    DIFF_CHANGES = ["git", "diff", "--", "*.tsx", "*.ts", "*.js", "*.jsx"]
    DIFF_BRANCH_HEAD = [
        "git",
        "diff",
        "{target_branch}..HEAD",
        "--",
        "*.tsx",
        "*.ts",
        "*.js",
        "*.jsx",
    ]
    DIFF_BRANCH_AGAINST_TARGET = [
        "git",
        "diff",
        "{target_branch}",
        "--",
        "*.tsx",
        "*.ts",
        "*.js",
        "*.jsx",
    ]
    DIFF_CACHED = ["git", "diff", "--cached", "--", "*.tsx", "*.ts", "*.js", "*.jsx"]
    RESET = ["git", "reset", "--quiet"]
