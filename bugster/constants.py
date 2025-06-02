"""Bugster CLI constants and configurations."""

from pathlib import Path

# Directory Structure
WORKING_DIR = Path.cwd()
BUGSTER_DIR = WORKING_DIR / ".bugster"
CONFIG_PATH = BUGSTER_DIR / "config.yaml"
TESTS_DIR = BUGSTER_DIR / "tests"
EXAMPLE_DIR = TESTS_DIR / "example"
EXAMPLE_TEST_FILE = EXAMPLE_DIR / "tests.yaml"

# Example Test Template
EXAMPLE_TEST = """- name: Basic Login Test
  task: Verify that users can log in with valid credentials
  expected_result: User should be successfully logged in and redirected to the dashboard
  steps:
    - Navigate to login page
    - Enter valid credentials
    - Click login button
    - Verify successful login
"""

# Ignore patterns for the .gitignore file
IGNORE_PATTERNS = [
    # Test files
    "**/*.test.ts",
    "**/*.test.tsx",
    "**/*.test.js",
    "**/*.test.jsx",
    "**/*.spec.ts",
    "**/*.spec.tsx",
    "**/*.spec.js",
    "**/*.spec.jsx",
    # Directories without app logic functionality
    "packages/**",
    "test/**",
    "tests/**",
    "public/**",  # Static assets
    "scripts/**",  # Build/utility scripts
    "cypress/**",  # E2E testing
    ".github/**",  # GitHub workflows/config
    ".bugster/**",  # Bugster CLI folder
    "build/**",  # Build output
    "__pycache__/**",  # Python cache
    "**/*.egg-info/**",  # Python package metadata
    "node_modules/**",  # Node.js dependencies
    ".next/**",  # Next.js build output
    "coverage/**",  # Test coverage reports
    "dist/**",  # Distribution files
    "storybook-static/**",  # Storybook build output
    "**/__snapshots__/**",  # Jest snapshots
    "**/__mocks__/**",  # Jest mocks
]
