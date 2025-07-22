import json
import subprocess
from datetime import datetime
from typing import Optional

from bugster.constants import UPDATE_STATE_PATH


def get_current_commit_hash() -> str:
    """Get the current commit hash."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
            encoding="utf-8",
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return ""


def get_current_branch() -> str:
    """Get the current branch name."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
            encoding="utf-8",
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return ""


def save_update_state():
    """Save the current update state to file."""
    UPDATE_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)

    state = {
        "timestamp": datetime.now().isoformat(),
        "commit_hash": get_current_commit_hash(),
        "branch": get_current_branch(),
    }

    with open(UPDATE_STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def get_last_update_state() -> Optional[dict]:
    """Get the last update state from file."""
    if not UPDATE_STATE_PATH.exists():
        return None

    try:
        with open(UPDATE_STATE_PATH, encoding="utf-8") as f:
            state = json.load(f)
        return state
    except (json.JSONDecodeError, OSError):
        return None


def get_last_update_commit() -> Optional[str]:
    """Get the commit hash from the last update."""
    state = get_last_update_state()
    if state:
        return state.get("commit_hash")
    return None


def has_last_update_state() -> bool:
    """Check if there's a previous update state."""
    return get_last_update_state() is not None


def commit_exists(commit_hash: str) -> bool:
    """Check if a commit hash exists in the repository."""
    if not commit_hash:
        return False

    try:
        result = subprocess.run(
            ["git", "cat-file", "-e", commit_hash],
            capture_output=True,
            text=True,
            check=True,
            encoding="utf-8",
        )
        return result.returncode == 0
    except subprocess.CalledProcessError:
        return False
