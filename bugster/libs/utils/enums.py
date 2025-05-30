from enum import Enum, auto


class BugsterApiPath(str, Enum):
    """Bugster API paths."""

    TEST_CASES = "/api/v1/test-cases"
    TEST_CASES_NEW = "/api/v1/test-cases/new"


class GitCommand(str, Enum):
    """Git commands."""

    DIFF_STATUS = auto()
    DIFF_FILES = auto()
    DIFF_CHANGES = auto()
    DIFF_CACHED = auto()
