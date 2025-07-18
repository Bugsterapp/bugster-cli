import json
from contextlib import contextmanager
from datetime import datetime

from bugster.constants import BUGSTER_DIR

STATE_FILE = BUGSTER_DIR / ".analysis_state.json"


def has_analysis_completed():
    """Check if the analysis has already been completed."""
    if not STATE_FILE.exists():
        return False

    try:
        with open(STATE_FILE, encoding="utf-8") as f:
            state = json.load(f)
        return state.get("completed", False)
    except (json.JSONDecodeError, KeyError):
        return False


@contextmanager
def analysis_tracker(version: str = "1.0"):
    """Context manager that tracks analysis completion state."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    start_time = datetime.now()
    state = {
        "status": "running",
        "started_at": start_time.isoformat(),
        "version": version,
        "completed": False,
    }

    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)

        yield state

        state.update(
            {
                "status": "completed",
                "completed": True,
                "completed_at": datetime.now().isoformat(),
                "duration_seconds": (datetime.now() - start_time).total_seconds(),
            }
        )
    except Exception as err:
        state.update(
            {
                "status": "failed",
                "completed": False,
                "failed_at": datetime.now().isoformat(),
                "duration_seconds": (datetime.now() - start_time).total_seconds(),
                "error": {"type": type(err).__name__, "message": str(err)},
            }
        )
        raise
    finally:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
