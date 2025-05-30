"""
Results streaming service for Bugster test execution.
"""

from pathlib import Path
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
        if not hasattr(config, "project_id") or not config.project_id:
            raise ValueError(
                "Project ID not found in configuration. Please run 'bugster init' to set up your project."
            )
        return config.project_id

    def create_run(self, run_data: dict) -> dict:
        """Create a new test run."""
        project_id = self._get_project_id()
        response = requests.post(
            f"{self.base_url}/api/v1/runs",
            headers={"X-API-Key": self.api_key},
            json={**run_data, "project_id": project_id},
        )
        response.raise_for_status()
        return response.json()

    def update_run(self, run_id: str, run_data: dict) -> dict:
        """Update an existing test run."""
        response = requests.patch(
            f"{self.base_url}/api/v1/runs/{run_id}",
            headers={"X-API-Key": self.api_key},
            json=run_data,
        )
        response.raise_for_status()
        return response.json()

    def add_test_case(self, run_id: str, test_case_data: dict) -> dict:
        """Add a test case result to a run."""
        response = requests.post(
            f"{self.base_url}/api/v1/runs/{run_id}/test-cases",
            headers={"X-API-Key": self.api_key},
            json=test_case_data,
        )
        response.raise_for_status()
        return response.json()

    def upload_video(self, video_path: Path) -> str:
        """Upload a video file and return the URL."""
        if not video_path.exists():
            # Consider logging this for debugging purposes
            return ""

        if not video_path.is_file():
            raise ValueError(f"Path is not a file: {video_path}")

        # Check file size to avoid uploading extremely large files
        max_size = 100 * 1024 * 1024  # 100MB limit
        if video_path.stat().st_size > max_size:
            raise ValueError(f"Video file too large: {video_path.stat().st_size} bytes")

        try:
            with open(video_path, "rb") as video_file:
                files = {"video": (video_path.name, video_file, "video/mp4")}
                response = requests.post(
                    f"{self.base_url}/api/v1/videos/upload",
                    headers={"X-API-Key": self.api_key},
                    files=files,
                )
                response.raise_for_status()
                return response.json().get("url", "")
        except (OSError, IOError) as e:
            raise RuntimeError(f"Failed to read video file {video_path}: {e}") from e

    def update_test_case_with_video(
        self, run_id: str, test_case_id: str, video_url: str
    ) -> dict:
        """Update test case with video URL."""
        response = requests.patch(
            f"{self.base_url}/api/v1/runs/{run_id}/test-cases/{test_case_id}",
            headers={"X-API-Key": self.api_key},
            json={"video": video_url},
        )
        response.raise_for_status()
        return response.json()
