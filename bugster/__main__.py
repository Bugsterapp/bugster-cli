import os
import sys


def setup_encoding():
    """Configure UTF-8 encoding for the application."""
    # Set environment variables for Python encoding
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    os.environ.setdefault("LC_ALL", "C.UTF-8")
    os.environ.setdefault("LANG", "C.UTF-8")

    # Force stdout/stderr to use UTF-8 encoding
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    else:
        # For older Python versions, wrap the streams
        import codecs

        sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, errors="replace")
        sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, errors="replace")


# Call this before any other imports that might use Unicode
setup_encoding()

# Now import your main module
from bugster.cli import app

if __name__ == "__main__":
    app()
