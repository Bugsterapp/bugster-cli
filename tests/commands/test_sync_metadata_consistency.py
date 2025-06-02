"""
Test for metadata consistency issue in sync command.
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock
from datetime import datetime, timezone

from bugster.commands.sync import sync_command
from bugster.utils.yaml_spec import load_spec, save_spec


def test_sync_metadata_consistency_for_spec_without_metadata(tmp_path, monkeypatch):
    """Test that metadata remains consistent when syncing a spec without initial metadata"""

    # Setup test directory
    test_dir = tmp_path / ".bugster/tests"
    test_dir.mkdir(parents=True)

    # Create a spec file WITHOUT metadata
    spec_file = test_dir / "test_spec.yaml"
    spec_content = """- name: Test Spec
  description: A test spec without metadata
  steps:
    - step 1
    - step 2
"""
    spec_file.write_text(spec_content)

    # Mock the specs service
    mock_specs_service = MagicMock()
    mock_specs_service.get_remote_test_cases.return_value = {}  # No remote specs
    mock_specs_service.upload_test_cases = MagicMock()

    # Mock the SyncService constructor
    def mock_specs_service_constructor():
        return mock_specs_service

    # Mock constants
    monkeypatch.setattr("bugster.commands.sync.TESTS_DIR", test_dir)
    monkeypatch.setattr(
        "bugster.commands.sync.SyncService", mock_specs_service_constructor
    )

    # Mock require_api_key decorator
    def mock_require_api_key(func):
        return func

    monkeypatch.setattr("bugster.commands.sync.require_api_key", mock_require_api_key)

    # Run sync command
    sync_command(branch="main", push=True)

    # Verify upload_test_cases was called
    assert mock_specs_service.upload_test_cases.called

    # Get the uploaded spec metadata
    upload_call_args = mock_specs_service.upload_test_cases.call_args[0]
    uploaded_specs = upload_call_args[1]  # Second argument is the specs dict
    uploaded_spec = uploaded_specs["test_spec.yaml"][0]
    uploaded_metadata = uploaded_spec["metadata"]

    # Load the final local spec
    final_specs = load_spec(spec_file)
    final_spec = final_specs[0]
    final_metadata = final_spec.metadata

    # The metadata should be consistent between what was uploaded and what's saved locally
    assert (
        uploaded_metadata["id"] == final_metadata.id
    ), f"Uploaded ID {uploaded_metadata['id']} != Final ID {final_metadata.id}"
    assert (
        uploaded_metadata["last_modified"] == final_metadata.last_modified
    ), f"Uploaded timestamp {uploaded_metadata['last_modified']} != Final timestamp {final_metadata.last_modified}"
