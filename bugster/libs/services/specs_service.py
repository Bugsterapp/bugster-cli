"""
Specs service for Bugster remote operations.
"""

from typing import Dict, List
import requests
from loguru import logger
from datetime import datetime, UTC, timedelta

from bugster.libs.settings import libs_settings
from bugster.utils.user_config import get_api_key
from bugster.utils.file import load_config


class SpecsService:
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

    def get_remote_specs(self, branch: str) -> Dict[str, List[Dict]]:
        """Get all specs for a branch from remote"""
        project_id = self._get_project_id()
        response = requests.get(
            f"{self.base_url}/api/v1/specs/{project_id}",
            params={"branch": branch},
            headers={"X-API-Key": f"{self.api_key}"},
        )
        response.raise_for_status()
        return response.json()

    def upload_specs(self, branch: str, specs_data: Dict[str, List[Dict]]) -> Dict:
        """Upload multiple specs to remote in a single call"""
        project_id = self._get_project_id()
        response = requests.put(
            f"{self.base_url}/api/v1/specs/{project_id}",
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
            f"{self.base_url}/api/v1/specs/{project_id}/delete",
            params={"branch": branch},
            headers={"X-API-Key": f"{self.api_key}"},
            json={"files": file_paths},
        )
        response.raise_for_status()

    def delete_specific_specs(
        self, branch: str, specs_to_delete: Dict[str, List[str]]
    ) -> None:
        """Delete specific specs by ID from remote files"""
        project_id = self._get_project_id()
        response = requests.post(
            f"{self.base_url}/api/v1/specs/{project_id}/delete-specs",
            params={"branch": branch},
            headers={"X-API-Key": f"{self.api_key}"},
            json={"specs": specs_to_delete},
        )
        response.raise_for_status()


class HardcodedSpecsService:
    """Hardcoded version of SpecsService for testing without real API."""

    def __init__(
        self, base_url: str = None, api_key: str = None, project_id: str = None
    ):
        self.base_url = base_url or "https://mock.bugster.dev"
        self.api_key = api_key or "mock-api-key"
        self.project_id = project_id

        # Simulated remote storage - persists during the session
        self._remote_storage: Dict[str, Dict[str, List[Dict]]] = {
            "giovaborgogno/sync-command": {
                "examples/login.yaml": [
                    {
                        "content": {
                            "name": "Login Test",
                            "description": "Test user login functionality",
                            "steps": [
                                "Navigate to login page",
                                "Enter valid credentials",
                                "Click login button",
                                "Verify successful login",
                            ],
                        },
                        "metadata": {
                            "id": "login-test-001",
                            "last_modified": (
                                datetime.now(UTC) - timedelta(hours=2)
                            ).isoformat(),
                        },
                    }
                ],
                "examples/checkout.yaml": [
                    {
                        "content": {
                            "name": "Checkout Process",
                            "description": "Test e-commerce checkout flow",
                            "steps": [
                                "Add items to cart",
                                "Go to checkout",
                                "Fill shipping information",
                                "Select payment method",
                                "Complete purchase",
                            ],
                        },
                        "metadata": {
                            "id": "checkout-test-001",
                            "last_modified": "2025-05-27T01:13:33.395789+00:00",
                        },
                    },
                    {
                        "content": {
                            "name": "Guest Checkout",
                            "description": "Test checkout without account",
                            "steps": [
                                "Add items to cart",
                                "Proceed as guest",
                                "Fill all required information",
                                "Complete purchase",
                            ],
                        },
                        "metadata": {
                            "id": "guest-checkout-001",
                            "last_modified": (
                                datetime.now(UTC) - timedelta(minutes=30)
                            ).isoformat(),
                        },
                    },
                ],
                "api/user_management.yaml": [
                    {
                        "content": {
                            "name": "Create User API",
                            "description": "Test user creation endpoint",
                            "steps": [
                                "Send POST request to /api/users",
                                "Include valid user data",
                                "Verify 201 status code",
                                "Verify user data in response",
                            ],
                        },
                        "metadata": {
                            "id": "create-user-api-001",
                            "last_modified": (
                                datetime.now(UTC) - timedelta(hours=3)
                            ).isoformat(),
                        },
                    }
                ],
            },
            "develop": {
                "examples/login.yaml": [
                    {
                        "content": {
                            "name": "Login Test - Dev",
                            "description": "Development version of login test",
                            "steps": [
                                "Navigate to dev login page",
                                "Enter test credentials",
                                "Click login button",
                                "Verify dev environment login",
                            ],
                        },
                        "metadata": {
                            "id": "login-test-dev-001",
                            "last_modified": (
                                datetime.now(UTC) - timedelta(hours=1)
                            ).isoformat(),
                        },
                    }
                ]
            },
        }

        logger.info(f"🧪 Using HardcodedSpecsService with mock data")
        logger.info(f"📊 Available branches: {list(self._remote_storage.keys())}")
        for branch, files in self._remote_storage.items():
            logger.info(
                f"   {branch}: {len(files)} files, {sum(len(specs) for specs in files.values())} specs"
            )

    def _get_project_id(self) -> str:
        """Get project_id from config or use provided one"""
        if self.project_id:
            return self.project_id

        config = load_config()
        return config.project_id

    def get_remote_specs(self, branch: str) -> Dict[str, List[Dict]]:
        """Get all specs for a branch from mock storage"""
        project_id = self._get_project_id()
        logger.info(
            f"📥 Getting remote specs for project {project_id}, branch: {branch}"
        )

        if branch not in self._remote_storage:
            logger.warning(f"Branch '{branch}' not found, returning empty specs")
            return {}

        specs = self._remote_storage[branch]
        logger.info(
            f"📋 Found {len(specs)} files with {sum(len(file_specs) for file_specs in specs.values())} total specs"
        )

        return specs

    def upload_specs(self, branch: str, specs_data: Dict[str, List[Dict]]) -> Dict:
        """Upload multiple specs to mock storage"""
        project_id = self._get_project_id()
        logger.info(f"📤 Uploading specs to project {project_id}, branch: {branch}")
        logger.info(f"📁 Files to upload: {list(specs_data.keys())}")

        # Initialize branch if it doesn't exist
        if branch not in self._remote_storage:
            self._remote_storage[branch] = {}

        # Update or add specs
        for file_path, file_specs in specs_data.items():
            if file_path not in self._remote_storage[branch]:
                self._remote_storage[branch][file_path] = []

            # Remove existing specs with same IDs and add new ones
            existing_specs = self._remote_storage[branch][file_path]
            new_spec_ids = {spec["metadata"]["id"] for spec in file_specs}

            # Keep specs that are not being updated
            updated_specs = [
                spec
                for spec in existing_specs
                if spec["metadata"]["id"] not in new_spec_ids
            ]

            # Add new/updated specs
            updated_specs.extend(file_specs)
            self._remote_storage[branch][file_path] = updated_specs

            logger.info(f"   ✅ {file_path}: {len(file_specs)} specs uploaded")

        return {"status": "success", "uploaded_files": len(specs_data)}

    def delete_specs(self, branch: str, file_paths: List[str]) -> None:
        """Delete multiple specs from mock storage"""
        project_id = self._get_project_id()
        logger.info(f"🗑️  Deleting specs from project {project_id}, branch: {branch}")
        logger.info(f"📁 Files to delete: {file_paths}")

        if branch not in self._remote_storage:
            logger.warning(f"Branch '{branch}' not found")
            return

        deleted_count = 0
        for file_path in file_paths:
            if file_path in self._remote_storage[branch]:
                del self._remote_storage[branch][file_path]
                deleted_count += 1
                logger.info(f"   ✅ Deleted {file_path}")
            else:
                logger.warning(f"   ⚠️  File not found: {file_path}")

        logger.info(f"🗑️  Deleted {deleted_count} files")

    def delete_specific_specs(
        self, branch: str, specs_to_delete: Dict[str, List[str]]
    ) -> None:
        """Delete specific specs by ID from mock storage"""
        project_id = self._get_project_id()
        logger.info(
            f"🗑️  Deleting specific specs from project {project_id}, branch: {branch}"
        )
        logger.info(f"📁 Files with specs to delete: {list(specs_to_delete.keys())}")

        if branch not in self._remote_storage:
            logger.warning(f"Branch '{branch}' not found")
            return

        total_deleted = 0
        for file_path, spec_ids_to_delete in specs_to_delete.items():
            if file_path not in self._remote_storage[branch]:
                logger.warning(f"   ⚠️  File not found: {file_path}")
                continue

            # Remove specs with matching IDs
            original_specs = self._remote_storage[branch][file_path]
            filtered_specs = [
                spec
                for spec in original_specs
                if spec["metadata"]["id"] not in spec_ids_to_delete
            ]

            deleted_count = len(original_specs) - len(filtered_specs)
            self._remote_storage[branch][file_path] = filtered_specs
            total_deleted += deleted_count

            logger.info(f"   ✅ {file_path}: deleted {deleted_count} specs")

            # If file is now empty, remove it entirely
            if not filtered_specs:
                del self._remote_storage[branch][file_path]
                logger.info(f"   ✅ Removed empty file: {file_path}")

        logger.info(f"🗑️  Deleted {total_deleted} individual specs")

    def get_storage_info(self) -> Dict:
        """Get information about current mock storage state (for debugging)"""
        info = {}
        for branch, files in self._remote_storage.items():
            info[branch] = {
                "files": len(files),
                "total_specs": sum(len(specs) for specs in files.values()),
                "file_list": list(files.keys()),
            }
        return info
