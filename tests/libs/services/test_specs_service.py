"""
Tests for SpecsService.
"""

import pytest
import responses
from datetime import datetime, UTC
from unittest.mock import MagicMock

from bugster.libs.services.specs_service import SpecsService
from bugster.utils.yaml_spec import YamlSpec, SpecMetadata


@pytest.fixture
def specs_service():
    return SpecsService(
        base_url="https://test.bugster.dev",
        api_key="test-key",
        project_id="test-project",
    )


@pytest.fixture
def mock_spec():
    return YamlSpec(
        data={"name": "Test Spec", "steps": ["step1", "step2"]},
        metadata=SpecMetadata(
            id="test-id", last_modified=datetime.now(UTC).isoformat()
        ),
    )


@responses.activate
def test_get_remote_specs(specs_service):
    """Test getting specs from remote"""
    responses.add(
        responses.GET,
        "https://test.bugster.dev/api/v1/specs/test-project?branch=main",
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

    result = specs_service.get_remote_specs("main")
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
        "https://test.bugster.dev/api/v1/specs/test-project?branch=main",
        json={"status": "success"},
        status=200,
    )

    result = specs_service.upload_specs("main", specs_data)
    assert result["status"] == "success"


@responses.activate
def test_delete_specs(specs_service):
    """Test deleting specs from remote"""
    responses.add(
        responses.POST,
        "https://test.bugster.dev/api/v1/specs/test-project/delete?branch=main",
        status=200,
    )

    # Should not raise any exception
    specs_service.delete_specs("main", ["test/file1.yaml", "test/file2.yaml"])


@responses.activate
def test_delete_specific_specs(specs_service):
    """Test deleting specific specs by ID from remote"""
    responses.add(
        responses.POST,
        "https://test.bugster.dev/api/v1/specs/test-project/delete-specs?branch=main",
        status=200,
    )

    specs_to_delete = {
        "test/file1.yaml": ["spec-id-1", "spec-id-2"],
        "test/file2.yaml": ["spec-id-3"],
    }

    # Should not raise any exception
    specs_service.delete_specific_specs("main", specs_to_delete)


def test_specs_service_requires_api_key(monkeypatch):
    """Test that SpecsService requires an API key"""
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
        SpecsService()
