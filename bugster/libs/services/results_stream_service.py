"""Results streaming service for Bugster test execution."""

import os
from pathlib import Path

import requests

from bugster.libs.settings import libs_settings
from bugster.utils.file import load_config
from bugster.utils.user_config import get_api_key


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

    def _get_headers(self) -> dict:
        """Get headers for API requests."""
        headers = {"X-API-Key": self.api_key}
        if os.getenv("IS_GITHUB_APP"):
            headers["X-GitHub-App"] = "true"
        return headers

    def _get_project_id(self) -> str:
        """Get project_id from config or use provided one."""
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
            headers=self._get_headers(),
            json={**run_data, "project_id": project_id},
        )
        response.raise_for_status()
        return response.json()

    def update_run(self, run_id: str, run_data: dict) -> dict:
        """Update an existing test run."""
        response = requests.patch(
            f"{self.base_url}/api/v1/runs/{run_id}",
            headers=self._get_headers(),
            json=run_data,
        )
        response.raise_for_status()
        return response.json()

    def add_test_case(self, run_id: str, test_case_data: dict) -> dict:
        """Add a test case result to a run."""
        response = requests.post(
            f"{self.base_url}/api/v1/runs/{run_id}/test-cases",
            headers=self._get_headers(),
            json=test_case_data,
        )
        response.raise_for_status()
        return response.json()

    def upload_video(self, video_path: Path) -> str:
        """Upload a video file using presigned URL and return the final video URL."""
        if not video_path.exists():
            # Consider logging this for debugging purposes
            return ""

        if not video_path.is_file():
            raise ValueError(f"Path is not a file: {video_path}")

        # Check file size to avoid uploading extremely large files
        max_size = 100 * 1024 * 1024  # 100MB limit
        file_size = video_path.stat().st_size
        if file_size > max_size:
            raise ValueError(f"Video file too large: {file_size} bytes")

        # Detect content type based on file extension
        content_type_map = {
            ".mp4": "video/mp4",
            ".webm": "video/webm",
            ".avi": "video/x-msvideo",
            ".mov": "video/quicktime",
        }

        file_extension = video_path.suffix.lower()
        content_type = content_type_map.get(file_extension, "video/mp4")

        try:
            # Step 1: Get presigned URL
            headers = self._get_headers()
            headers["Content-Type"] = "application/json"

            presigned_response = requests.post(
                f"{self.base_url}/api/v1/videos/presigned-url",
                headers=headers,
                json={"filename": video_path.name, "content_type": content_type},
            )
            presigned_response.raise_for_status()
            presigned_data = presigned_response.json()

            # Validate required keys in presigned URL response
            required_keys = ["upload_url", "headers", "final_url"]
            missing_keys = [key for key in required_keys if key not in presigned_data]
            if missing_keys:
                raise RuntimeError(
                    f"Invalid presigned URL response: missing keys {missing_keys}"
                )

            # Step 2: Upload video directly to S3 using presigned URL
            with open(video_path, "rb") as video_file:
                upload_response = requests.put(
                    presigned_data["upload_url"],
                    headers=presigned_data["headers"],
                    data=video_file,
                )
                upload_response.raise_for_status()

            # Step 3: Return the final URL where video will be accessible
            return presigned_data["final_url"]

        except OSError as e:
            raise RuntimeError(f"Failed to read video file {video_path}: {e}") from e

    def update_test_case_with_video(
        self, run_id: str, test_case_id: str, video_url: str
    ) -> dict:
        """Update test case with video URL."""
        response = requests.patch(
            f"{self.base_url}/api/v1/runs/{run_id}/test-cases/{test_case_id}",
            headers=self._get_headers(),
            json={"video": video_url},
        )
        response.raise_for_status()
        return response.json()