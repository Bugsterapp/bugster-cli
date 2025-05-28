"""
Tests for SyncService.
"""

import pytest
import responses
from datetime import datetime, UTC
from unittest.mock import MagicMock

from bugster.libs.services.specs_service import SyncService
from bugster.utils.yaml_spec import YamlTestcase, TestCaseMetadata


@pytest.fixture
def specs_service():
    return SyncService(
        base_url="https://test.bugster.dev",
        api_key="test-key",
        project_id="test-project",
    )


@pytest.fixture
def mock_spec():
    return YamlTestcase(
        data={"name": "Test Spec", "steps": ["step1", "step2"]},
        metadata=TestCaseMetadata(
            id="test-id", last_modified=datetime.now(UTC).isoformat()
        ),
    )


@responses.activate
def test_get_remote_specs(specs_service):
    """Test getting specs from remote"""
    responses.add(
        responses.GET,
        "https://test.bugster.dev/api/v1/sync/test-project?branch=main",
        json={
            "test/file.yaml": [
                {
                    "content": {"name": "Test", "steps": ["step1"]},
                    "metadata": {
                        "id": "test-id",
                        "last_modified": "2024-03-20T10:00:00+00:00",
                    },
                }
            ]
        },
        status=200,
    )

    result = specs_service.get_remote_test_cases("main")
    assert "test/file.yaml" in result
    assert len(result["test/file.yaml"]) == 1
    assert result["test/file.yaml"][0]["metadata"]["id"] == "test-id"


@responses.activate
def test_upload_specs(specs_service, mock_spec):
    """Test uploading specs to remote"""
    specs_data = {
        "test/file.yaml": [
            {
                "content": mock_spec.data,
                "metadata": {
                    "id": mock_spec.metadata.id,
                    "last_modified": mock_spec.metadata.last_modified,
                },
            }
        ]
    }

    responses.add(
        responses.PUT,
        "https://test.bugster.dev/api/v1/sync/test-project?branch=main",
        json={"status": "success"},
        status=200,
    )

    result = specs_service.upload_test_cases("main", specs_data)
    assert result["status"] == "success"


@responses.activate
def test_delete_specs(specs_service):
    """Test deleting specs from remote"""
    responses.add(
        responses.POST,
        "https://test.bugster.dev/api/v1/sync/test-project/delete?branch=main",
        status=200,
    )

    # Should not raise any exception
    specs_service.delete_specs("main", ["test/file1.yaml", "test/file2.yaml"])


@responses.activate
def test_delete_specific_specs(specs_service):
    """Test deleting specific specs by ID from remote"""
    responses.add(
        responses.POST,
        "https://test.bugster.dev/api/v1/sync/test-project/delete-test-cases?branch=main",
        status=200,
    )

    test_cases_to_delete = {
        "test/file1.yaml": ["spec-id-1", "spec-id-2"],
        "test/file2.yaml": ["spec-id-3"],
    }

    # Should not raise any exception
    specs_service.delete_specific_test_cases("main", test_cases_to_delete)


def test_specs_service_requires_api_key(monkeypatch):
    """Test that SyncService requires an API key"""
    # Mock environment variable
    monkeypatch.delenv("BUGSTER_CLI_API_KEY", raising=False)

    # Mock get_api_key to return None
    monkeypatch.setattr("bugster.utils.user_config.load_user_config", lambda: {})

    # Mock libs_settings
    mock_settings = MagicMock()
    mock_settings.bugster_api_url = "https://test.bugster.dev"
    monkeypatch.setattr(
        "bugster.libs.services.specs_service.libs_settings", mock_settings
    )

    with pytest.raises(
        ValueError,
        match="API key is required. Please run 'bugster login' to set up your API key.",
    ):
        SyncService()
