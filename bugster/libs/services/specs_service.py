"""
Specs service for Bugster remote operations.
"""

from typing import Dict, List
import requests
from loguru import logger

from bugster.libs.settings import libs_settings
from bugster.utils.user_config import get_api_key


class SpecsService:
    """Service for managing specs with remote operations."""

    def __init__(self, base_url: str = None, api_key: str = None):
        self.base_url = base_url or libs_settings.bugster_api_url
        self.api_key = api_key or get_api_key()

        if not self.api_key:
            raise ValueError(
                "API key is required. Please run 'bugster login' to set up your API key."
            )

    def get_remote_specs(self, branch: str) -> Dict[str, List[Dict]]:
        """Get all specs for a branch from remote"""
        response = requests.get(
            f"{self.base_url}/specs/{branch}",
            headers={"Authorization": f"Bearer {self.api_key}"},
        )
        response.raise_for_status()
        return response.json()

    def upload_specs(self, branch: str, specs_data: Dict[str, List[Dict]]) -> Dict:
        """Upload multiple specs to remote in a single call"""
        response = requests.put(
            f"{self.base_url}/specs/{branch}",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json=specs_data,
        )
        response.raise_for_status()
        return response.json()

    def delete_specs(self, branch: str, file_paths: List[str]) -> None:
        """Delete multiple specs from remote in a single call"""
        response = requests.post(
            f"{self.base_url}/specs/{branch}/delete",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={"files": file_paths},
        )
        response.raise_for_status()
