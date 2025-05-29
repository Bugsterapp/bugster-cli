"""
Specs service for Bugster remote operations.
"""

from typing import Dict, List
import requests

from bugster.libs.settings import libs_settings
from bugster.utils.user_config import get_api_key
from bugster.utils.file import load_config


class SyncService:
    """Service for managing specs with remote operations."""

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

    def get_remote_test_cases(self, branch: str) -> Dict[str, List[Dict]]:
        """Get all specs for a branch from remote"""
        project_id = self._get_project_id()
        response = requests.get(
            f"{self.base_url}/api/v1/sync/{project_id}",
            params={"branch": branch},
            headers={"X-API-Key": f"{self.api_key}"},
        )
        response.raise_for_status()
        return response.json()

    def upload_test_cases(self, branch: str, specs_data: Dict[str, List[Dict]]) -> Dict:
        """Upload multiple specs to remote in a single call"""
        project_id = self._get_project_id()
        response = requests.put(
            f"{self.base_url}/api/v1/sync/{project_id}",
            params={"branch": branch},
            headers={"X-API-Key": f"{self.api_key}"},
            json=specs_data,
        )
        response.raise_for_status()
        return response.json()

    def delete_specs(self, branch: str, file_paths: List[str]) -> None:
        """Delete multiple specs from remote in a single call"""
        project_id = self._get_project_id()
        response = requests.post(
            f"{self.base_url}/api/v1/sync/{project_id}/delete",
            params={"branch": branch},
            headers={"X-API-Key": f"{self.api_key}"},
            json={"files": file_paths},
        )
        response.raise_for_status()

    def delete_specific_test_cases(
        self, branch: str, test_cases_to_delete: Dict[str, List[str]]
    ) -> None:
        """Delete specific specs by ID from remote files"""
        project_id = self._get_project_id()
        response = requests.post(
            f"{self.base_url}/api/v1/sync/{project_id}/delete-test-cases",
            params={"branch": branch},
            headers={"X-API-Key": f"{self.api_key}"},
            json={"specs": test_cases_to_delete},
        )
        response.raise_for_status()
