"""
Bugster CLI constants and configurations.
"""

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
