"""
Results streaming service for Bugster test execution.
"""

from pathlib import Path
from typing import Optional
import requests

from bugster.libs.settings import libs_settings
from bugster.utils.user_config import get_api_key
from bugster.utils.file import load_config


class ResultsStreamService:
    """Service for streaming test results to the API."""

    def __init__(
        self, base_url: str = None, api_key: str = None, project_id: str = None
    ):
        self.base_url = base_url or libs_settings.bugster_api_url
        self.api_key = api_key or get_api_key()
        self.project_id = project_id

        if not self.api_key:
            raise ValueError(
                "API key is required. Please run 'bugster login' to set up your API key."
            )

    def _get_project_id(self) -> str:
        """Get project_id from config or use provided one"""
        if self.project_id:
            return self.project_id

        config = load_config()
        return config.project_id

    def create_run(self, run_data: dict) -> dict:
        """Create a new test run."""
        project_id = self._get_project_id()
        # print("create_run")
        # return {}
        response = requests.post(
            f"{self.base_url}/api/v1/runs",
            headers={"X-API-Key": self.api_key},
            json={**run_data, "project_id": project_id},
        )
        response.raise_for_status()
        return response.json()

    def update_run(self, run_id: str, run_data: dict) -> dict:
        """Update an existing test run."""
        # print("update_run")
        # return {}
        response = requests.patch(
            f"{self.base_url}/api/v1/runs/{run_id}",
            headers={"X-API-Key": self.api_key},
            json=run_data,
        )
        response.raise_for_status()
        return response.json()

    def add_test_case(self, run_id: str, test_case_data: dict) -> dict:
        """Add a test case result to a run."""
        # print("add_test_case")
        # return {}
        response = requests.post(
            f"{self.base_url}/api/v1/runs/{run_id}/test-cases",
            headers={"X-API-Key": self.api_key},
            json=test_case_data,
        )
        response.raise_for_status()
        return response.json()

    def upload_video(self, video_path: Path) -> str:
        """Upload a video file and return the URL."""
        # print("upload_video")
        # return "url"
        if not video_path.exists():
            return ""

        with open(video_path, "rb") as video_file:
            files = {"video": video_file}
            response = requests.post(
                f"{self.base_url}/api/v1/videos/upload",
                headers={"X-API-Key": self.api_key},
                files=files,
            )
            response.raise_for_status()
            return response.json().get("url", "")

    def update_test_case_with_video(
        self, run_id: str, test_case_id: str, video_url: str
    ) -> dict:
        """Update test case with video URL."""
        # print("update_test_case_with_video")
        # return {}
        response = requests.patch(
            f"{self.base_url}/api/v1/runs/{run_id}/test-cases/{test_case_id}",
            headers={"X-API-Key": self.api_key},
            json={"video": video_url},
        )
        response.raise_for_status()
        return response.json()
