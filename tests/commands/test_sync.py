"""
Tests for sync command.
"""

import pytest
from pathlib import Path
import os
from datetime import datetime, UTC, timedelta
import responses
from typer.testing import CliRunner
import typer
from unittest.mock import MagicMock, patch
import json

from bugster.commands.sync import sync_command, sync_specs
from bugster.libs.services.specs_service import SyncService
from bugster.utils.yaml_spec import (
    YamlTestcase,
    TestCaseMetadata,
    save_spec,
    load_spec,
)
from bugster.constants import TESTS_DIR

# Create a Typer app for testing
app = typer.Typer()
app.command()(sync_command)

runner = CliRunner()


@pytest.fixture
def specs_service():
    os.environ["BUGSTER_API_KEY"] = "test-key"
    return SyncService(base_url="https://test.bugster.dev", project_id="test-project")


@pytest.fixture
def mock_local_spec():
    return YamlTestcase(
        data={"name": "Local Test", "steps": ["step1"]},
        metadata=TestCaseMetadata(
            id="test-id", last_modified=datetime.now(UTC).isoformat()
        ),
    )


@pytest.fixture
def mock_remote_spec():
    return {
        "content": {"name": "Remote Test", "steps": ["step1"]},
        "metadata": {
            "id": "remote-id",
            "last_modified": (datetime.now(UTC) - timedelta(days=1)).isoformat(),
        },
    }


def test_sync_specs_new_local_uploads_to_remote(specs_service, tmp_path):
    """Test that specs only in local get uploaded to remote"""
    # Create local spec
    local_spec = YamlTestcase(
        data={"name": "Local Only Test", "steps": ["step1", "step2"]},
        metadata=TestCaseMetadata(
            id="local-only-id", last_modified="2024-03-20T10:00:00+00:00"
        ),
    )
    local_specs = {"test/local_only.yaml": [local_spec]}
    remote_specs = {}

    # Create temporary test directory
    test_dir = tmp_path / ".bugster/tests"
    test_dir.mkdir(parents=True)

    # Mock the upload call
    with responses.RequestsMock() as rsps:
        upload_mock = rsps.add(
            responses.PUT,
            "https://test.bugster.dev/api/v1/sync/test-project?branch=main",
            json={"status": "success"},
            status=200,
        )

        sync_specs(specs_service, "main", local_specs, remote_specs, tests_dir=test_dir)

        # Verify upload was called with correct data
        assert len(rsps.calls) == 1
        uploaded_data = json.loads(rsps.calls[0].request.body)

        assert "test/local_only.yaml" in uploaded_data
        assert len(uploaded_data["test/local_only.yaml"]) == 1

        uploaded_spec = uploaded_data["test/local_only.yaml"][0]
        assert uploaded_spec["content"]["name"] == "Local Only Test"
        assert uploaded_spec["content"]["steps"] == ["step1", "step2"]
        assert uploaded_spec["metadata"]["id"] == "local-only-id"
        assert uploaded_spec["metadata"]["last_modified"] == "2024-03-20T10:00:00+00:00"


def test_sync_specs_new_remote_saves_locally(specs_service, tmp_path):
    """Test that specs only in remote get saved locally"""
    local_specs = {}
    remote_spec = {
        "content": {"name": "Remote Only Test", "steps": ["step3", "step4"]},
        "metadata": {
            "id": "remote-only-id",
            "last_modified": "2024-03-20T12:00:00+00:00",
        },
    }
    remote_specs = {"test/remote_only.yaml": [remote_spec]}

    # Create temporary test directory
    test_dir = tmp_path / ".bugster/tests"
    test_dir.mkdir(parents=True)

    sync_specs(specs_service, "main", local_specs, remote_specs, tests_dir=test_dir)

    # Verify the file was created locally with the remote spec
    spec_file = test_dir / "test/remote_only.yaml"
    assert spec_file.exists()

    loaded_specs = load_spec(spec_file)
    assert len(loaded_specs) == 1

    saved_spec = loaded_specs[0]
    assert saved_spec.data["name"] == "Remote Only Test"
    assert saved_spec.data["steps"] == ["step3", "step4"]
    assert saved_spec.metadata.id == "remote-only-id"
    assert saved_spec.metadata.last_modified == "2024-03-20T12:00:00+00:00"


def test_sync_specs_conflict_local_newer_updates_remote(specs_service, tmp_path):
    """Test that when local spec is newer, it updates remote"""
    # Local spec is newer
    local_spec = YamlTestcase(
        data={"name": "Updated Local Version", "steps": ["step1", "step2", "step3"]},
        metadata=TestCaseMetadata(
            id="same-id", last_modified="2024-03-20T15:00:00+00:00"
        ),
    )

    # Remote spec is older
    remote_spec = {
        "content": {"name": "Old Remote Version", "steps": ["step1"]},
        "metadata": {
            "id": "same-id",
            "last_modified": "2024-03-20T10:00:00+00:00",
        },
    }

    local_specs = {"test/conflict.yaml": [local_spec]}
    remote_specs = {"test/conflict.yaml": [remote_spec]}

    test_dir = tmp_path / ".bugster/tests"
    test_dir.mkdir(parents=True)

    # Create initial local file
    spec_file = test_dir / "test/conflict.yaml"
    spec_file.parent.mkdir(parents=True)
    save_spec(spec_file, [local_spec])

    with responses.RequestsMock() as rsps:
        upload_mock = rsps.add(
            responses.PUT,
            "https://test.bugster.dev/api/v1/sync/test-project?branch=main",
            json={"status": "success"},
            status=200,
        )

        sync_specs(specs_service, "main", local_specs, remote_specs, tests_dir=test_dir)

        # Verify remote was updated with local version
        assert len(rsps.calls) == 1
        uploaded_data = json.loads(rsps.calls[0].request.body)

        uploaded_spec = uploaded_data["test/conflict.yaml"][0]
        assert uploaded_spec["content"]["name"] == "Updated Local Version"
        assert uploaded_spec["content"]["steps"] == ["step1", "step2", "step3"]
        assert uploaded_spec["metadata"]["last_modified"] == "2024-03-20T15:00:00+00:00"

    # Verify local file remains unchanged (still has the newer version)
    final_specs = load_spec(spec_file)
    assert len(final_specs) == 1
    assert final_specs[0].data["name"] == "Updated Local Version"
    assert final_specs[0].metadata.last_modified == "2024-03-20T15:00:00+00:00"


def test_sync_specs_conflict_remote_newer_updates_local(specs_service, tmp_path):
    """Test that when remote spec is newer, it updates local"""
    # Local spec is older
    local_spec = YamlTestcase(
        data={"name": "Old Local Version", "steps": ["step1"]},
        metadata=TestCaseMetadata(
            id="same-id", last_modified="2024-03-20T10:00:00+00:00"
        ),
    )

    # Remote spec is newer
    remote_spec = {
        "content": {
            "name": "Updated Remote Version",
            "steps": ["step1", "step2", "step3"],
        },
        "metadata": {
            "id": "same-id",
            "last_modified": "2024-03-20T15:00:00+00:00",
        },
    }

    local_specs = {"test/conflict.yaml": [local_spec]}
    remote_specs = {"test/conflict.yaml": [remote_spec]}

    test_dir = tmp_path / ".bugster/tests"
    test_dir.mkdir(parents=True)

    # Create initial local file with old version
    spec_file = test_dir / "test/conflict.yaml"
    spec_file.parent.mkdir(parents=True)
    save_spec(spec_file, [local_spec])

    sync_specs(specs_service, "main", local_specs, remote_specs, tests_dir=test_dir)

    # Verify local file was updated with remote version
    final_specs = load_spec(spec_file)
    assert len(final_specs) == 1

    updated_spec = final_specs[0]
    assert updated_spec.data["name"] == "Updated Remote Version"
    assert updated_spec.data["steps"] == ["step1", "step2", "step3"]
    assert updated_spec.metadata.id == "same-id"
    assert updated_spec.metadata.last_modified == "2024-03-20T15:00:00+00:00"


def test_sync_specs_prefer_local_overrides_timestamp(specs_service, tmp_path):
    """Test that prefer='local' overrides timestamp comparison"""
    # Local spec is older but we prefer local
    local_spec = YamlTestcase(
        data={"name": "Local Version", "steps": ["local_step"]},
        metadata=TestCaseMetadata(
            id="same-id", last_modified="2024-03-20T10:00:00+00:00"
        ),
    )

    # Remote spec is newer
    remote_spec = {
        "content": {"name": "Remote Version", "steps": ["remote_step"]},
        "metadata": {
            "id": "same-id",
            "last_modified": "2024-03-20T15:00:00+00:00",
        },
    }

    local_specs = {"test/prefer_local.yaml": [local_spec]}
    remote_specs = {"test/prefer_local.yaml": [remote_spec]}

    test_dir = tmp_path / ".bugster/tests"
    test_dir.mkdir(parents=True)

    with responses.RequestsMock() as rsps:
        upload_mock = rsps.add(
            responses.PUT,
            "https://test.bugster.dev/api/v1/sync/test-project?branch=main",
            json={"status": "success"},
            status=200,
        )

        sync_specs(
            specs_service,
            "main",
            local_specs,
            remote_specs,
            prefer="local",
            tests_dir=test_dir,
        )

        # Verify local version was uploaded despite being older
        assert len(rsps.calls) == 1
        uploaded_data = json.loads(rsps.calls[0].request.body)

        uploaded_spec = uploaded_data["test/prefer_local.yaml"][0]
        assert uploaded_spec["content"]["name"] == "Local Version"
        assert uploaded_spec["content"]["steps"] == ["local_step"]


def test_sync_specs_prefer_remote_overrides_timestamp(specs_service, tmp_path):
    """Test that prefer='remote' overrides timestamp comparison"""
    # Local spec is newer but we prefer remote
    local_spec = YamlTestcase(
        data={"name": "Local Version", "steps": ["local_step"]},
        metadata=TestCaseMetadata(
            id="same-id", last_modified="2024-03-20T15:00:00+00:00"
        ),
    )

    # Remote spec is older
    remote_spec = {
        "content": {"name": "Remote Version", "steps": ["remote_step"]},
        "metadata": {
            "id": "same-id",
            "last_modified": "2024-03-20T10:00:00+00:00",
        },
    }

    local_specs = {"test/prefer_remote.yaml": [local_spec]}
    remote_specs = {"test/prefer_remote.yaml": [remote_spec]}

    test_dir = tmp_path / ".bugster/tests"
    test_dir.mkdir(parents=True)

    # Create initial local file
    spec_file = test_dir / "test/prefer_remote.yaml"
    spec_file.parent.mkdir(parents=True)
    save_spec(spec_file, [local_spec])

    sync_specs(
        specs_service,
        "main",
        local_specs,
        remote_specs,
        prefer="remote",
        tests_dir=test_dir,
    )

    # Verify local file was updated with remote version despite local being newer
    final_specs = load_spec(spec_file)
    assert len(final_specs) == 1

    updated_spec = final_specs[0]
    assert updated_spec.data["name"] == "Remote Version"
    assert updated_spec.data["steps"] == ["remote_step"]


def test_sync_specs_multiple_specs_partial_update(specs_service, tmp_path):
    """Test syncing when a file has multiple specs and only some need updates"""
    # Create 3 local specs
    local_spec1 = YamlTestcase(
        data={"name": "Spec 1", "steps": ["step1"]},
        metadata=TestCaseMetadata(
            id="spec-1", last_modified="2024-03-20T10:00:00+00:00"
        ),
    )
    local_spec2 = YamlTestcase(
        data={"name": "Old Spec 2", "steps": ["step2"]},
        metadata=TestCaseMetadata(
            id="spec-2", last_modified="2024-03-20T10:00:00+00:00"
        ),
    )
    local_spec3 = YamlTestcase(
        data={"name": "Spec 3", "steps": ["step3"]},
        metadata=TestCaseMetadata(
            id="spec-3", last_modified="2024-03-20T10:00:00+00:00"
        ),
    )

    local_specs = {"test/multi.yaml": [local_spec1, local_spec2, local_spec3]}

    # Remote has spec-2 updated and spec-4 new
    remote_specs = {
        "test/multi.yaml": [
            {
                "content": {"name": "Updated Spec 2", "steps": ["step2", "step2b"]},
                "metadata": {
                    "id": "spec-2",
                    "last_modified": "2024-03-20T15:00:00+00:00",  # Newer
                },
            },
            {
                "content": {"name": "New Spec 4", "steps": ["step4"]},
                "metadata": {
                    "id": "spec-4",
                    "last_modified": "2024-03-20T12:00:00+00:00",
                },
            },
        ]
    }

    test_dir = tmp_path / ".bugster/tests"
    test_dir.mkdir(parents=True)

    # Create initial local file
    spec_file = test_dir / "test/multi.yaml"
    spec_file.parent.mkdir(parents=True)
    save_spec(spec_file, [local_spec1, local_spec2, local_spec3])

    with responses.RequestsMock() as rsps:
        upload_mock = rsps.add(
            responses.PUT,
            "https://test.bugster.dev/api/v1/sync/test-project?branch=main",
            json={"status": "success"},
            status=200,
        )

        sync_specs(specs_service, "main", local_specs, remote_specs, tests_dir=test_dir)

        # Verify spec-1 and spec-3 were uploaded (they don't exist in remote)
        assert len(rsps.calls) == 1
        uploaded_data = json.loads(rsps.calls[0].request.body)

        uploaded_specs = uploaded_data["test/multi.yaml"]
        assert len(uploaded_specs) == 2

        uploaded_ids = {spec["metadata"]["id"] for spec in uploaded_specs}
        assert uploaded_ids == {"spec-1", "spec-3"}

    # Verify final local state
    final_specs = load_spec(spec_file)
    assert len(final_specs) == 4  # All 4 specs should be present

    specs_by_id = {spec.metadata.id: spec for spec in final_specs}

    # Spec 1 and 3 should be unchanged
    assert specs_by_id["spec-1"].data["name"] == "Spec 1"
    assert specs_by_id["spec-3"].data["name"] == "Spec 3"

    # Spec 2 should be updated from remote
    assert specs_by_id["spec-2"].data["name"] == "Updated Spec 2"
    assert specs_by_id["spec-2"].data["steps"] == ["step2", "step2b"]
    assert specs_by_id["spec-2"].metadata.last_modified == "2024-03-20T15:00:00+00:00"

    # Spec 4 should be new from remote
    assert specs_by_id["spec-4"].data["name"] == "New Spec 4"
    assert specs_by_id["spec-4"].data["steps"] == ["step4"]


def test_sync_specs_same_content_no_sync_needed(specs_service, tmp_path):
    """Test that when specs have same content, no sync is performed regardless of timestamps"""
    # Create specs with same content but different timestamps
    local_spec = YamlTestcase(
        data={"name": "Same Content", "steps": ["step1", "step2"]},
        metadata=TestCaseMetadata(
            id="same-id", last_modified="2024-03-20T10:00:00+00:00"
        ),
    )

    remote_spec = {
        "content": {"name": "Same Content", "steps": ["step1", "step2"]},
        "metadata": {
            "id": "same-id",
            "last_modified": "2024-03-20T15:00:00+00:00",  # Different timestamp
        },
    }

    local_specs = {"test/same_content.yaml": [local_spec]}
    remote_specs = {"test/same_content.yaml": [remote_spec]}

    test_dir = tmp_path / ".bugster/tests"
    test_dir.mkdir(parents=True)

    with responses.RequestsMock() as rsps:
        # No requests should be made since content is the same
        sync_specs(specs_service, "main", local_specs, remote_specs, tests_dir=test_dir)

        # Verify no API calls were made
        assert len(rsps.calls) == 0


def test_sync_specs_same_timestamp_different_content_prefers_local(
    specs_service, tmp_path
):
    """Test that when timestamps are equal but content differs, local is preferred with updated timestamp"""
    # Create specs with different content but same timestamp
    local_spec = YamlTestcase(
        data={"name": "Local Content", "steps": ["step1", "step2"]},
        metadata=TestCaseMetadata(
            id="same-id", last_modified="2024-03-20T10:00:00+00:00"
        ),
    )

    remote_spec = {
        "content": {"name": "Remote Content", "steps": ["step1", "step2", "step3"]},
        "metadata": {
            "id": "same-id",
            "last_modified": "2024-03-20T10:00:00+00:00",  # Same timestamp
        },
    }

    local_specs = {"test/equal_timestamp.yaml": [local_spec]}
    remote_specs = {"test/equal_timestamp.yaml": [remote_spec]}

    test_dir = tmp_path / ".bugster/tests"
    test_dir.mkdir(parents=True)

    # Create initial local file
    spec_file = test_dir / "test/equal_timestamp.yaml"
    spec_file.parent.mkdir(parents=True)
    save_spec(spec_file, [local_spec])

    with responses.RequestsMock() as rsps:
        upload_mock = rsps.add(
            responses.PUT,
            "https://test.bugster.dev/api/v1/sync/test-project?branch=main",
            json={"status": "success"},
            status=200,
        )

        sync_specs(specs_service, "main", local_specs, remote_specs, tests_dir=test_dir)

        # Verify upload was called with local content and updated timestamp
        assert len(rsps.calls) == 1
        uploaded_data = json.loads(rsps.calls[0].request.body)

        uploaded_spec = uploaded_data["test/equal_timestamp.yaml"][0]
        assert uploaded_spec["content"]["name"] == "Local Content"
        assert uploaded_spec["content"]["steps"] == ["step1", "step2"]

        # Timestamp should be updated to current time (not the original equal timestamp)
        uploaded_timestamp = uploaded_spec["metadata"]["last_modified"]
        assert uploaded_timestamp != "2024-03-20T10:00:00+00:00"

        # Verify the timestamp is a valid ISO format (should be current time)
        datetime.fromisoformat(uploaded_timestamp)

    # Verify local file was also updated with the new timestamp
    final_specs = load_spec(spec_file)
    assert len(final_specs) == 1

    updated_spec = final_specs[0]
    assert updated_spec.data["name"] == "Local Content"
    assert updated_spec.metadata.last_modified != "2024-03-20T10:00:00+00:00"
    assert updated_spec.metadata.last_modified == uploaded_timestamp


@responses.activate
def test_sync_command_full_integration(tmp_path, monkeypatch):
    """Test full sync command integration with all scenarios"""
    os.environ["BUGSTER_API_KEY"] = "test-key"

    # Mock TESTS_DIR to use temporary directory
    test_dir = tmp_path / ".bugster/tests"
    monkeypatch.setattr("bugster.commands.sync.TESTS_DIR", test_dir)
    monkeypatch.setattr("bugster.commands.sync.get_current_branch", lambda: "main")

    monkeypatch.setattr(
        "bugster.libs.services.specs_service.SyncService._get_project_id",
        lambda self: "test-project",
    )

    # Mock libs_settings
    mock_settings = MagicMock()
    mock_settings.bugster_api_url = "https://api.bugster.dev"
    monkeypatch.setattr(
        "bugster.libs.services.specs_service.libs_settings", mock_settings
    )

    # Create test directory and files
    test_dir.mkdir(parents=True)

    # File 1: Local only spec
    local_only_file = test_dir / "local_only.yaml"
    local_only_spec = YamlTestcase(
        data={"name": "Local Only", "steps": ["local_step"]},
        metadata=TestCaseMetadata(
            id="local-only", last_modified="2024-03-20T10:00:00+00:00"
        ),
    )
    save_spec(local_only_file, [local_only_spec])

    # File 2: Spec without metadata (should get metadata added)
    no_metadata_file = test_dir / "no_metadata.yaml"
    with open(no_metadata_file, "w") as f:
        f.write(
            """- name: No Metadata Spec
  steps:
    - step1
    - step2
"""
        )

    # Create conflicting local file (newer than remote)
    conflict_file = test_dir / "conflict.yaml"
    conflict_spec = YamlTestcase(
        data={"name": "New Local Version", "steps": ["new_step"]},
        metadata=TestCaseMetadata(
            id="conflict-id", last_modified="2024-03-20T14:00:00+00:00"
        ),
    )
    save_spec(conflict_file, [conflict_spec])

    # Mock remote response with remote-only and conflicting specs
    # This will be called twice (once for pull, once for push)
    responses.add(
        responses.GET,
        "https://api.bugster.dev/api/v1/sync/test-project?branch=main",
        json={
            "remote_only.yaml": [
                {
                    "content": {"name": "Remote Only", "steps": ["remote_step"]},
                    "metadata": {
                        "id": "remote-only",
                        "last_modified": "2024-03-20T12:00:00+00:00",
                    },
                }
            ],
            "conflict.yaml": [
                {
                    "content": {"name": "Old Remote Version", "steps": ["old_step"]},
                    "metadata": {
                        "id": "conflict-id",
                        "last_modified": "2024-03-20T08:00:00+00:00",  # Older
                    },
                }
            ],
        },
        status=200,
    )

    # Mock upload response
    responses.add(
        responses.PUT,
        "https://api.bugster.dev/api/v1/sync/test-project?branch=main",
        json={"status": "success"},
        status=200,
    )

    # Run sync command
    result = runner.invoke(app)
    print(result.stdout)
    assert result.exit_code == 0

    # Verify all expected files exist
    assert local_only_file.exists()
    assert no_metadata_file.exists()
    assert conflict_file.exists()

    # Verify local_only file unchanged but has metadata
    local_only_specs = load_spec(local_only_file)
    assert len(local_only_specs) == 1
    assert local_only_specs[0].data["name"] == "Local Only"
    assert local_only_specs[0].metadata.id == "local-only"

    # Verify no_metadata file now has metadata
    no_metadata_specs = load_spec(no_metadata_file)
    assert len(no_metadata_specs) == 1
    assert no_metadata_specs[0].data["name"] == "No Metadata Spec"
    assert no_metadata_specs[0].metadata.id is not None
    assert no_metadata_specs[0].metadata.last_modified is not None

    # Verify conflict file has local version (local was newer)
    conflict_specs = load_spec(conflict_file)
    assert len(conflict_specs) == 1
    assert conflict_specs[0].data["name"] == "New Local Version"
    assert conflict_specs[0].metadata.last_modified == "2024-03-20T14:00:00+00:00"

    # Verify remote_only.yaml was downloaded
    remote_only_file = test_dir / "remote_only.yaml"
    assert remote_only_file.exists()
    remote_only_specs = load_spec(remote_only_file)
    assert len(remote_only_specs) == 1
    assert remote_only_specs[0].data["name"] == "Remote Only"
    assert remote_only_specs[0].metadata.id == "remote-only"
    assert remote_only_specs[0].metadata.last_modified == "2024-03-20T12:00:00+00:00"

    # Verify upload was called (for local_only, no_metadata, and conflict specs)
    upload_calls = [call for call in responses.calls if call.request.method == "PUT"]
    assert len(upload_calls) >= 1


@responses.activate
def test_sync_command_pull_only_downloads_remote_specs(tmp_path, monkeypatch):
    """Test sync command with --pull flag downloads remote specs"""
    os.environ["BUGSTER_API_KEY"] = "test-key"

    test_dir = tmp_path / ".bugster/tests"
    monkeypatch.setattr("bugster.commands.sync.TESTS_DIR", test_dir)
    monkeypatch.setattr("bugster.commands.sync.get_current_branch", lambda: "main")
    monkeypatch.setattr(
        "bugster.libs.services.specs_service.SyncService._get_project_id",
        lambda self: "test-project",
    )

    mock_settings = MagicMock()
    mock_settings.bugster_api_url = "https://api.bugster.dev"
    monkeypatch.setattr(
        "bugster.libs.services.specs_service.libs_settings", mock_settings
    )

    # Create test directory (empty initially)
    test_dir.mkdir(parents=True)

    # Mock remote response with remote-only specs
    responses.add(
        responses.GET,
        "https://api.bugster.dev/api/v1/sync/test-project?branch=main",
        json={
            "remote_only.yaml": [
                {
                    "content": {"name": "Remote Only", "steps": ["remote_step"]},
                    "metadata": {
                        "id": "remote-only",
                        "last_modified": "2024-03-20T12:00:00+00:00",
                    },
                }
            ],
        },
        status=200,
    )

    # Run sync command with --pull
    result = runner.invoke(app, ["--pull"])
    assert result.exit_code == 0

    # Verify the command shows it would download the spec
    assert "Will download new test case: remote_only.yaml" in result.stdout

    # Verify the file was actually downloaded
    remote_only_file = test_dir / "remote_only.yaml"
    assert remote_only_file.exists(), "remote_only.yaml should have been downloaded"

    # Verify the content is correct
    downloaded_specs = load_spec(remote_only_file)
    assert len(downloaded_specs) == 1
    assert downloaded_specs[0].data["name"] == "Remote Only"
    assert downloaded_specs[0].data["steps"] == ["remote_step"]
    assert downloaded_specs[0].metadata.id == "remote-only"
    assert downloaded_specs[0].metadata.last_modified == "2024-03-20T12:00:00+00:00"


@responses.activate
def test_sync_command_clean_remote(tmp_path, monkeypatch):
    """Test that --clean-remote deletes remote specs not present locally"""
    os.environ["BUGSTER_API_KEY"] = "test-key"

    test_dir = tmp_path / ".bugster/tests"
    monkeypatch.setattr("bugster.commands.sync.TESTS_DIR", test_dir)
    monkeypatch.setattr("bugster.commands.sync.get_current_branch", lambda: "main")
    monkeypatch.setattr(
        "bugster.libs.services.specs_service.SyncService._get_project_id",
        lambda self: "test-project",
    )

    mock_settings = MagicMock()
    mock_settings.bugster_api_url = "https://api.bugster.dev"
    monkeypatch.setattr(
        "bugster.libs.services.specs_service.libs_settings", mock_settings
    )

    # Create only one local file
    test_dir.mkdir(parents=True)
    local_file = test_dir / "local.yaml"
    local_spec = YamlTestcase(
        data={"name": "Local Spec", "steps": ["step1"]},
        metadata=TestCaseMetadata(
            id="local-id", last_modified="2024-03-20T10:00:00+00:00"
        ),
    )
    save_spec(local_file, [local_spec])

    # Mock remote response with multiple files (some should be deleted)
    responses.add(
        responses.GET,
        "https://api.bugster.dev/api/v1/sync/test-project?branch=main",
        json={
            "local.yaml": [
                {
                    "content": {"name": "Local Spec", "steps": ["step1"]},
                    "metadata": {
                        "id": "local-id",
                        "last_modified": "2024-03-20T10:00:00+00:00",
                    },
                }
            ],
            "remote_only1.yaml": [
                {
                    "content": {"name": "Remote Only 1", "steps": ["step1"]},
                    "metadata": {
                        "id": "remote-1",
                        "last_modified": "2024-03-20T10:00:00+00:00",
                    },
                }
            ],
            "remote_only2.yaml": [
                {
                    "content": {"name": "Remote Only 2", "steps": ["step2"]},
                    "metadata": {
                        "id": "remote-2",
                        "last_modified": "2024-03-20T10:00:00+00:00",
                    },
                }
            ],
        },
        status=200,
    )

    # Mock upload response
    responses.add(
        responses.PUT,
        "https://api.bugster.dev/api/v1/sync/test-project?branch=main",
        json={"status": "success"},
        status=200,
    )

    # Mock delete response (for complete files)
    delete_mock = responses.add(
        responses.POST,
        "https://api.bugster.dev/api/v1/sync/test-project/delete?branch=main",
        json={"status": "success"},
        status=200,
    )

    # Mock delete_specific_test_cases response (for individual specs)
    delete_specific_mock = responses.add(
        responses.POST,
        "https://api.bugster.dev/api/v1/sync/test-project/delete-test-cases?branch=main",
        json={"status": "success"},
        status=200,
    )

    # Run sync command with --clean-remote
    result = runner.invoke(app, ["--clean-remote"])
    assert result.exit_code == 0

    # Verify delete was called with the correct files
    delete_calls = [
        call
        for call in responses.calls
        if call.request.method == "POST"
        and "delete" in call.request.url
        and "delete-test-cases" not in call.request.url
    ]
    assert len(delete_calls) == 1

    delete_data = json.loads(delete_calls[0].request.body)
    deleted_files = set(delete_data["files"])
    expected_deleted = {"remote_only1.yaml", "remote_only2.yaml"}
    assert deleted_files == expected_deleted

    # Verify delete_specific_test_cases was NOT called (since we're deleting entire files)
    delete_specific_calls = [
        call
        for call in responses.calls
        if call.request.method == "POST" and "delete-test-cases" in call.request.url
    ]
    assert len(delete_specific_calls) == 0

    # Verify local file still exists and is unchanged
    assert local_file.exists()
    local_specs = load_spec(local_file)
    assert len(local_specs) == 1
    assert local_specs[0].data["name"] == "Local Spec"


@responses.activate
def test_sync_command_clean_remote_individual_specs(tmp_path, monkeypatch):
    """Test that --clean-remote deletes individual specs but keeps files with remaining specs"""
    os.environ["BUGSTER_API_KEY"] = "test-key"

    test_dir = tmp_path / ".bugster/tests"
    monkeypatch.setattr("bugster.commands.sync.TESTS_DIR", test_dir)
    monkeypatch.setattr("bugster.commands.sync.get_current_branch", lambda: "main")
    monkeypatch.setattr(
        "bugster.libs.services.specs_service.SyncService._get_project_id",
        lambda self: "test-project",
    )

    mock_settings = MagicMock()
    mock_settings.bugster_api_url = "https://api.bugster.dev"
    monkeypatch.setattr(
        "bugster.libs.services.specs_service.libs_settings", mock_settings
    )

    # Create local file with one spec
    test_dir.mkdir(parents=True)
    local_file = test_dir / "shared.yaml"
    local_spec = YamlTestcase(
        data={"name": "Local Spec", "steps": ["step1"]},
        metadata=TestCaseMetadata(
            id="local-id", last_modified="2024-03-20T10:00:00+00:00"
        ),
    )
    save_spec(local_file, [local_spec])

    # Mock remote response with the same file but additional specs
    responses.add(
        responses.GET,
        "https://api.bugster.dev/api/v1/sync/test-project?branch=main",
        json={
            "shared.yaml": [
                {
                    "content": {"name": "Local Spec", "steps": ["step1"]},
                    "metadata": {
                        "id": "local-id",
                        "last_modified": "2024-03-20T10:00:00+00:00",
                    },
                },
                {
                    "content": {"name": "Remote Only Spec 1", "steps": ["step2"]},
                    "metadata": {
                        "id": "remote-only-1",
                        "last_modified": "2024-03-20T10:00:00+00:00",
                    },
                },
                {
                    "content": {"name": "Remote Only Spec 2", "steps": ["step3"]},
                    "metadata": {
                        "id": "remote-only-2",
                        "last_modified": "2024-03-20T10:00:00+00:00",
                    },
                },
            ]
        },
        status=200,
    )

    # Mock upload response
    responses.add(
        responses.PUT,
        "https://api.bugster.dev/api/v1/sync/test-project?branch=main",
        json={"status": "success"},
        status=200,
    )

    # Mock delete response (for complete files)
    delete_mock = responses.add(
        responses.POST,
        "https://api.bugster.dev/api/v1/sync/test-project/delete?branch=main",
        json={"status": "success"},
        status=200,
    )

    # Mock delete_specific_test_cases response (for individual specs)
    delete_specific_mock = responses.add(
        responses.POST,
        "https://api.bugster.dev/api/v1/sync/test-project/delete-test-cases?branch=main",
        json={"status": "success"},
        status=200,
    )

    # Run sync command with --clean-remote
    result = runner.invoke(app, ["--clean-remote"])
    assert result.exit_code == 0

    # Verify individual spec deletion was called
    delete_specific_calls = [
        call
        for call in responses.calls
        if call.request.method == "POST" and "delete-test-cases" in call.request.url
    ]
    assert len(delete_specific_calls) == 1

    delete_specific_data = json.loads(delete_specific_calls[0].request.body)
    assert "shared.yaml" in delete_specific_data["specs"]
    deleted_spec_ids = set(delete_specific_data["specs"]["shared.yaml"])
    expected_deleted_ids = {"remote-only-1", "remote-only-2"}
    assert deleted_spec_ids == expected_deleted_ids

    # Verify complete file deletion was NOT called
    delete_file_calls = [
        call
        for call in responses.calls
        if call.request.method == "POST"
        and "delete" in call.request.url
        and "delete-test-cases" not in call.request.url
    ]
    assert len(delete_file_calls) == 0

    # Verify output shows individual spec deletions
    assert "Will delete remote test case: shared.yaml (remote-only-1)" in result.stdout
    assert "Will delete remote test case: shared.yaml (remote-only-2)" in result.stdout
    assert "Will delete entire remote file" not in result.stdout

    # Verify local file still exists and is unchanged
    assert local_file.exists()
    local_specs = load_spec(local_file)
    assert len(local_specs) == 1
    assert local_specs[0].data["name"] == "Local Spec"


def test_sync_command_no_api_key(monkeypatch):
    """Test sync command fails gracefully without API key"""
    monkeypatch.delenv("BUGSTER_CLI_API_KEY", raising=False)
    monkeypatch.setattr("bugster.utils.user_config.load_user_config", lambda: {})

    mock_settings = MagicMock()
    mock_settings.bugster_api_url = "https://test.bugster.dev"
    monkeypatch.setattr(
        "bugster.libs.services.specs_service.libs_settings", mock_settings
    )

    result = runner.invoke(app)
    assert result.exit_code == 1
    assert "API key not found" in result.stdout


@responses.activate
def test_sync_command_dry_run_shows_changes_without_executing(tmp_path, monkeypatch):
    """Test that dry-run shows what would happen without making changes"""
    os.environ["BUGSTER_API_KEY"] = "test-key"

    test_dir = tmp_path / ".bugster/tests"
    monkeypatch.setattr("bugster.commands.sync.TESTS_DIR", test_dir)
    monkeypatch.setattr("bugster.commands.sync.get_current_branch", lambda: "main")
    monkeypatch.setattr(
        "bugster.libs.services.specs_service.SyncService._get_project_id",
        lambda self: "test-project",
    )

    mock_settings = MagicMock()
    mock_settings.bugster_api_url = "https://api.bugster.dev"
    monkeypatch.setattr(
        "bugster.libs.services.specs_service.libs_settings", mock_settings
    )

    # Create local spec
    test_dir.mkdir(parents=True)
    local_file = test_dir / "local.yaml"
    local_spec = YamlTestcase(
        data={"name": "Local Test", "steps": ["step1"]},
        metadata=TestCaseMetadata(
            id="local-id", last_modified="2024-03-20T10:00:00+00:00"
        ),
    )
    save_spec(local_file, [local_spec])

    # Mock remote response
    responses.add(
        responses.GET,
        "https://api.bugster.dev/api/v1/sync/test-project?branch=main",
        json={
            "remote.yaml": [
                {
                    "content": {"name": "Remote Test", "steps": ["step2"]},
                    "metadata": {
                        "id": "remote-id",
                        "last_modified": "2024-03-20T12:00:00+00:00",
                    },
                }
            ]
        },
        status=200,
    )

    # Run dry-run
    result = runner.invoke(app, ["--dry-run"])
    assert result.exit_code == 0

    # Verify output shows what would happen
    assert "Will upload new test case" in result.stdout
    assert "Will download new test case" in result.stdout

    # Verify no actual changes were made
    # - No upload calls should have been made
    upload_calls = [call for call in responses.calls if call.request.method == "PUT"]
    assert len(upload_calls) == 0

    # - Remote file should not exist locally
    assert not (test_dir / "remote.yaml").exists()

    # - Local file should be unchanged
    local_specs = load_spec(local_file)
    assert len(local_specs) == 1
    assert local_specs[0].data["name"] == "Local Test"
