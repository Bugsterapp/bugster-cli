import os
import time
from collections import OrderedDict
from random import randint
from typing import Any, List, Optional

import yaml
from loguru import logger
from rich.console import Console
from rich.status import Status

from bugster.analyzer.core.framework_detector import get_project_info
from bugster.clients.http_client import BugsterHTTPClient
from bugster.constants import BUGSTER_DIR, TESTS_DIR
from bugster.libs.utils.enums import BugsterApiPath
from bugster.libs.utils.errors import BugsterError
from bugster.libs.utils.files import get_specs_pages, get_specs_paths
from bugster.libs.utils.llm import format_tests_for_llm
from bugster.libs.utils.nextjs.extract_page_folder import extract_page_folder
from bugster.utils.user_config import get_api_key

console = Console()


def _ordered_dict_representer(dumper: yaml.Dumper, data: OrderedDict):
    """Custom representer for OrderedDict to maintain field order in YAML."""
    return dumper.represent_mapping("tag:yaml.org,2002:map", data.items())


yaml.add_representer(OrderedDict, _ordered_dict_representer)


def get_or_create_folder(folder_name: str) -> str:
    """Get or create a folder with a given name."""
    folder_path = os.path.join(TESTS_DIR, folder_name)
    logger.info("Creating folder {}", folder_path)
    os.makedirs(folder_path, exist_ok=True)
    return folder_path


def normalize_name(name: str) -> str:
    """Normalize a name to a valid name."""
    return name.lower().replace(" ", "_")


class TestCasesService:
    """Service to generate test cases for a given codebase analysis."""

    def __init__(self):
        """Initialize the service."""
        self._analysis_json_path = None

    @property
    def analysis_json_path(self) -> str:
        """Get the `analysis.json` file path."""
        if self._analysis_json_path is None:
            project_info = get_project_info()
            cache_framework_dir = os.path.join(
                BUGSTER_DIR, project_info["data"]["frameworks"][0]["id"]
            )
            self._analysis_json_path = os.path.join(
                cache_framework_dir, "analysis.json"
            )
        return self._analysis_json_path

    def _init_generation(
        self, page_filter: Optional[List[str]] = None, count: Optional[int] = None
    ) -> list[dict[Any, str]]:
        """Post the `analysis.json` file to the API and receive the test cases."""
        logger.info("Posting analysis.json file to the API...")

        if not self.analysis_json_path:
            raise BugsterError("Analysis JSON path is not set")

        if not os.path.exists(self.analysis_json_path):
            raise BugsterError(
                "Analysis JSON file not found, execute bugster analyze first"
            )

        data = {}

        if page_filter:
            data["page_filter"] = ",".join(page_filter)

        context = ""

        if page_filter:
            specs_pages = {
                page_path: specs
                for page_path, specs in specs_pages.items()
                if page_path in page_filter
            }
        else:
            specs_pages = get_specs_pages()

        for page_path, specs_by_page in specs_pages.items():
            logger.info("Adding context for page: {}...", page_path)

            if context:
                context += "\n\n"

            context += format_tests_for_llm(
                existing_specs=specs_by_page, include_page_path=True
            )

        logger.info("Resulting context: '{}'", context)

        if context:
            data["context"] = context

        if count is not None:
            data["count"] = count

        with open(self.analysis_json_path) as file:
            analysis_data = yaml.safe_load(file)
            payload = {"json": analysis_data, "data": data}

            with BugsterHTTPClient() as client:
                api_key = get_api_key()

                if api_key:
                    client.set_headers({"x-api-key": api_key})

                return client.post(
                    endpoint=BugsterApiPath.GENERATE_INIT.value,
                    json=payload,
                )

    def _save_test_case_as_yaml(self, test_case: dict[Any, str]):
        """Save test case as a YAML file.

        :param test_case: The test case to save. V.g., `{"name": "Test Case 1", "page": "Home", "page_path": "/",
            "task": "Test Case 1", "steps": ["Step 1", "Step 2"], "expected_result": "Expected Result"}`
        :return: The path to the saved test case file. V.g., `tests/<page>/<spec>.yaml`
        """
        folder_name = extract_page_folder(file_path=test_case["page_path"])
        folder_path = get_or_create_folder(folder_name=folder_name)
        file_name = normalize_name(name=test_case["name"])

        try:
            specs_paths = get_specs_paths(
                relatives_to=folder_path, folder_name=folder_name
            )
            has_numeric_prefix = any(
                s.startswith(("1", "2", "3", "4", "5", "6", "7", "8", "9"))
                for s in specs_paths
            )

            if specs_paths and has_numeric_prefix:
                sorted_paths = sorted(specs_paths, key=lambda x: int(x.split("_")[0]))
                index = int(sorted_paths[-1].split("_")[0]) + 1
            else:
                index = 1
        except Exception as err:
            logger.error("Error getting specs paths: {}", err)
            index = randint(1, 1000000)

        file_name = f"{index}_{file_name}.yaml"
        file_path = os.path.join(folder_path, file_name)

        # Convert dict to OrderedDict with desired field order
        ordered_test_case = OrderedDict()
        field_order = ["name", "page", "page_path", "task", "steps", "expected_result"]

        for field in field_order:
            if field in test_case:
                ordered_test_case[field] = test_case[field]

        # Add any remaining fields not in the predefined order
        for key, value in test_case.items():
            if key not in field_order:
                ordered_test_case[key] = value

        with open(file_path, "w") as f:
            yaml.dump(ordered_test_case, f, default_flow_style=False, sort_keys=False)

        logger.info("Saved test case to {}", file_path)
        return file_path

    def _check_results(self, job_id: str) -> str:
        """Get the status of a job."""
        with BugsterHTTPClient() as client:
            api_key = get_api_key()

            if api_key:
                client.set_headers({"x-api-key": api_key})

            return client.get(
                endpoint=BugsterApiPath.GENERATE_CHECK_RESULTS.value,
                params={"job_id": job_id},
            )

    def _polling_test_cases(self, result):
        """Polling test cases."""
        console.print()
        console.print("🧪 Generating test cases...")
        console.print(f"   Job submitted (ID: {result['job_id']})")
        console.print()
        start_time = time.time()
        timeout_seconds = 3 * 60
        poll_interval = 5
        poll_end_time = start_time + timeout_seconds

        with Status("Generating tests...", spinner="dots") as status:
            console.print("⏳ Processing...")
            while time.time() < poll_end_time:
                time.sleep(poll_interval)
                response = self._check_results(job_id=result["job_id"])
                elapsed_time = time.time() - start_time
                response_status = response["status"]

                if response_status == "completed":
                    status.stop()
                    console.print(
                        f"   Status: {response_status} • Elapsed: {elapsed_time:.0f}s"
                    )
                    console.print()
                    console.print("✅ Test generation complete")
                    return response.get("test_cases") or response.get("result")
                elif response_status == "failed":
                    status.stop()
                    console.print(
                        f"   Status: {response_status} • Elapsed: {elapsed_time:.0f}s"
                    )
                    console.print()
                    console.print("❌ Test generation failed")
                    return None
                else:
                    status.update(
                        f" Status: {response_status} • Elapsed: {elapsed_time:.0f}s"
                    )

            status.stop()
            console.print(f"   Status: timeout • Elapsed: {elapsed_time:.0f}s")
            console.print()
            console.print("❌ Test generation timeout")
            return None

    def generate_test_cases(
        self, page_filter: list[str] = None, count: Optional[int] = None
    ):
        """Generate test cases for the given codebase analysis."""
        result = self._init_generation(page_filter=page_filter, count=count)
        test_cases = self._polling_test_cases(result=result)

        if not test_cases:
            raise BugsterError("Test cases not found")

        logger.info("Saving test cases as YAML files...")

        for test_case in test_cases:
            self._save_test_case_as_yaml(test_case=test_case)

        logger.info("Test cases saved successfully")

    def delete_spec_by_spec_path(self, spec_path: str):
        """Delete a spec file by spec path."""
        path = os.path.join(TESTS_DIR, spec_path)

        try:
            os.remove(path)
            logger.info("Deleted spec file {}", path)
        except Exception as err:
            msg = f"Failed to delete spec file {path}: {err}"
            logger.error(msg)
            raise BugsterError(msg)

    def _update_spec_yaml_file(self, spec_path: str, spec_data: dict[Any, str]):
        """Update the spec YAML file."""
        path = os.path.join(TESTS_DIR, spec_path)

        # Convert dict to OrderedDict with desired field order
        ordered_spec_data = OrderedDict()
        field_order = ["name", "page", "page_path", "task", "steps", "expected_result"]

        for field in field_order:
            if field in spec_data:
                ordered_spec_data[field] = spec_data[field]

        # Add any remaining fields not in the predefined order
        for key, value in spec_data.items():
            if key not in field_order:
                ordered_spec_data[key] = value

        with open(path, "w") as f:
            yaml.dump(ordered_spec_data, f, default_flow_style=False, sort_keys=False)

    def update_spec_by_diff(
        self,
        spec_data: dict[Any, str],
        diff_changes: str,
        spec_path: str,
        context: Optional[str] = None,
    ):
        """Update a spec file by diff changes."""
        with BugsterHTTPClient() as client:
            payload = {
                "test_case": spec_data,
                "git_diff": diff_changes,
            }

            if context:
                payload["context"] = context

            data = client.put(endpoint=BugsterApiPath.TEST_CASES.value, json=payload)
            self._update_spec_yaml_file(spec_path=spec_path, spec_data=data)
            return data

    def suggest_spec_by_diff(
        self, page_path: str, diff_changes: str, context: Optional[str] = None
    ):
        """Suggest a spec file by page."""
        with BugsterHTTPClient() as client:
            payload = {
                "page_path": page_path,
                "git_diff": diff_changes,
            }

            if context:
                payload["context"] = context

            data = client.post(
                endpoint=BugsterApiPath.TEST_CASES_NEW.value, json=payload
            )
            self._save_test_case_as_yaml(test_case=data)
            return data
