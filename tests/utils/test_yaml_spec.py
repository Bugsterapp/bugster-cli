"""
Tests for YAML spec parser.
"""

import pytest
from pathlib import Path
import tempfile
from datetime import datetime
import uuid
import json

from bugster.utils.yaml_spec import (
    TestCaseMetadata,
    YamlTestcase,
    parse_yaml_with_testcases,
    load_spec,
    save_spec,
)


def test_spec_metadata_creation():
    """Test creation of new metadata"""
    metadata = TestCaseMetadata.create_new()
    assert isinstance(metadata.id, str)
    assert uuid.UUID(metadata.id)  # Validates UUID format
    assert datetime.fromisoformat(metadata.last_modified)  # Validates ISO format


def test_metadata_from_comment():
    """Test parsing metadata from comment"""
    comment = '# @META:{"id":"123","last_modified":"2024-03-20T10:00:00"}'
    metadata = TestCaseMetadata.from_comment(comment)
    assert metadata is not None
    assert metadata.id == "123"
    assert metadata.last_modified == "2024-03-20T10:00:00"


def test_metadata_from_legacy_comment():
    """Test parsing metadata from legacy comment with version field"""
    comment = '# @META:{"id":"123","version":2,"last_modified":"2024-03-20T10:00:00"}'
    metadata = TestCaseMetadata.from_comment(comment)
    assert metadata is not None
    assert metadata.id == "123"
    assert metadata.last_modified == "2024-03-20T10:00:00"
    # Version field should be ignored
    assert not hasattr(metadata, "version")


def test_metadata_from_invalid_comment():
    """Test parsing invalid metadata comment"""
    comment = "# Invalid comment"
    metadata = TestCaseMetadata.from_comment(comment)
    assert metadata is None


def test_yaml_spec_creation():
    """Test creation of YamlTestcase"""
    data = {"name": "Test", "steps": ["step1", "step2"]}
    spec = YamlTestcase(data)
    assert spec.data == data
    assert isinstance(spec.metadata, TestCaseMetadata)


def test_parse_yaml_with_specs():
    """Test parsing YAML content with multiple specs"""
    content = """# @META:{"id":"123","last_modified":"2024-03-20T10:00:00"}
# This comment contains machine-readable metadata that should not be modified
- name: Test 1
  steps: [step1, step2]

# A spec without metadata
- name: Test 2
  steps: [step3, step4]

# @META:{"id":"456","last_modified":"2024-03-20T11:00:00"}
- name: Test 3
  steps: [step5, step6]
"""
    specs = parse_yaml_with_testcases(content)
    assert len(specs) == 3

    # First spec should have metadata
    assert specs[0].metadata.id == "123"
    assert specs[0].data == {"name": "Test 1", "steps": ["step1", "step2"]}

    # Second spec should have auto-generated metadata
    assert uuid.UUID(specs[1].metadata.id)  # Should be valid UUID
    assert specs[1].data == {"name": "Test 2", "steps": ["step3", "step4"]}

    # Third spec should have metadata
    assert specs[2].metadata.id == "456"
    assert specs[2].data == {"name": "Test 3", "steps": ["step5", "step6"]}


def test_load_and_save_yaml_specs():
    """Test loading and saving specs to/from file"""
    # Create a temporary file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as tmp:
        content = """# @META:{"id":"123","last_modified":"2024-03-20T10:00:00"}
# This comment contains machine-readable metadata that should not be modified
- name: Test 1
  steps: [step1, step2]

# @META:{"id":"456","last_modified":"2024-03-20T11:00:00"}
- name: Test 2
  steps: [step3, step4]
"""
        tmp.write(content)
        tmp_path = Path(tmp.name)

    try:
        # Load specs
        specs = load_spec(tmp_path)
        assert len(specs) == 2
        assert specs[0].metadata.id == "123"
        assert specs[1].metadata.id == "456"

        # Save specs to new file
        new_path = tmp_path.parent / "new_test.yaml"
        save_spec(new_path, specs)

        # Load saved specs and verify
        loaded_specs = load_spec(new_path)
        assert len(loaded_specs) == 2
        assert loaded_specs[0].metadata.id == "123"
        assert loaded_specs[1].metadata.id == "456"

    finally:
        # Cleanup
        tmp_path.unlink()
        if new_path.exists():
            new_path.unlink()


def test_load_yaml_specs_file_not_found():
    """Test loading specs from non-existent file"""
    with pytest.raises(FileNotFoundError):
        load_spec(Path("non_existent.yaml"))
