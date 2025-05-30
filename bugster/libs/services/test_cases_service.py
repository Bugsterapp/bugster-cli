import os
from random import randint
from typing import Any, Optional

import yaml
from loguru import logger

from bugster.analyzer.core.framework_detector import get_project_info
from bugster.clients.http_client import BugsterHTTPClient
from bugster.constants import BUGSTER_DIR, TESTS_DIR
from bugster.libs.utils.enums import BugsterApiPath
from bugster.libs.utils.errors import BugsterError
from bugster.libs.utils.files import get_specs_paths


class TestCasesService:
    """Service to generate test cases for a given codebase analysis."""

    def __init__(self):
        """Initialize the service."""
        self.analysis_json_path = None

    def _set_analysis_json_path(self) -> str:
        """Set the `analysis.json` file path."""
        project_info = get_project_info()
        cache_framework_dir = os.path.join(
            BUGSTER_DIR, project_info["data"]["frameworks"][0]["id"]
        )
        self.analysis_json_path = os.path.join(cache_framework_dir, "analysis.json")

    def _post_analysis_json(self) -> list[dict[Any, str]]:
        """Post the `analysis.json` file to the API and receive the test cases."""
        logger.info("Posting analysis.json file to the API...")
        if not self.analysis_json_path:
            raise BugsterError("Analysis JSON path is not set")

        if not os.path.exists(self.analysis_json_path):
            raise BugsterError(
                "Analysis JSON file not found, execute bugster analyze first"
            )

        with open(self.analysis_json_path, "rb") as file:
            files = {"file": ("analysis.json", file, "application/json")}

            with BugsterHTTPClient() as client:
                return client.post(
                    endpoint=BugsterApiPath.TEST_CASES.value, files=files
                )

    def _save_test_case_as_yaml(
        self, test_case: dict[Any, str], index: Optional[int] = None
    ):
        """Save test case as a YAML file."""
        try:
            if not index:
                specs_paths = get_specs_paths(relatives_to=TESTS_DIR)
                sorted_paths = sorted(specs_paths, key=lambda x: int(x.split("_")[0]))
                index = int(sorted_paths[-1].split("_")[0]) + 1
        except Exception:
            index = randint(1, 1000000)

        file_name = f"{index}_{test_case['name'].lower().replace(' ', '_')}.yaml"
        file_path = os.path.join(TESTS_DIR, file_name)

        with open(file_path, "w") as f:
            yaml.dump(test_case, f, default_flow_style=False)

        logger.info("Saved test case to {}", file_path)
        return file_path

    def _save_test_cases_as_yaml(self, test_cases: list[dict[Any, str]]):
        """Save test cases as individual YAML files."""
        logger.info("Saving test cases as YAML files...")
        output_dir = TESTS_DIR
        output_dir.mkdir(parents=True, exist_ok=True)

        for i, test_case in enumerate(test_cases):
            self._save_test_case_as_yaml(test_case=test_case, index=i + 1)

        logger.info("Test cases saved successfully")
        return output_dir

    def generate_test_cases(self):
        """Generate test cases for the given codebase analysis."""
        self._set_analysis_json_path()
        test_cases = self._post_analysis_json()
        return self._save_test_cases_as_yaml(test_cases=test_cases)

    def delete_spec_by_spec_path(self, spec_path: str):
        """Delete a spec file by spec path."""
        path = os.path.join(TESTS_DIR, spec_path)
        os.remove(path)

    def _update_spec_yaml_file(self, spec_path: str, spec_data: dict[Any, str]):
        """Update the spec YAML file."""
        path = os.path.join(TESTS_DIR, spec_path)

        with open(path, "w") as f:
            yaml.dump(spec_data, f, default_flow_style=False)

    def update_spec_by_diff(
        self, spec_data: dict[Any, str], diff_changes: str, spec_path: str
    ):
        """Update a spec file by diff changes."""
        with BugsterHTTPClient() as client:
            payload = {"test_case": spec_data, "git_diff": diff_changes}
            data = client.put(endpoint=BugsterApiPath.TEST_CASES.value, json=payload)
            self._update_spec_yaml_file(spec_path=spec_path, spec_data=data)
            return data

    def suggest_spec_by_diff(self, page_path: str, diff_changes: str):
        """Suggest a spec file by page."""
        payload = {"page_path": page_path, "git_diff": diff_changes}

        with BugsterHTTPClient() as client:
            payload = {"page_path": page_path, "git_diff": diff_changes}
            data = client.post(
                endpoint=BugsterApiPath.TEST_CASES_NEW.value, json=payload
            )
            self._save_test_case_as_yaml(test_case=data)
            return data
