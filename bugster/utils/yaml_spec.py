"""
YAML Spec parser with metadata handling.
"""

from datetime import datetime, timezone
import uuid
from typing import List, Dict, Any, Optional
from pathlib import Path
import yaml
import json
from dataclasses import dataclass
from loguru import logger


@dataclass
class TestCaseMetadata:
    id: str
    last_modified: str

    @classmethod
    def create_new(cls) -> "TestCaseMetadata":
        """Create new metadata with default values"""
        return cls(
            id=str(uuid.uuid4()), last_modified=datetime.now(timezone.utc).isoformat()
        )

    @classmethod
    def from_comment(cls, comment: str) -> Optional["TestCaseMetadata"]:
        """Try to parse metadata from a comment string"""
        try:
            if not comment.startswith("# @META:"):
                return None

            meta_dict = json.loads(comment[8:].strip())
            # Ensure all required fields exist
            meta_dict.setdefault("id", str(uuid.uuid4()))
            meta_dict.setdefault(
                "last_modified", datetime.now(timezone.utc).isoformat()
            )

            # Remove version if present (for backwards compatibility)
            meta_dict.pop("version", None)

            return cls(**meta_dict)
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Failed to parse metadata from comment: {e}")
            return None

    def to_comment(self) -> str:
        """Convert metadata to YAML comment format"""
        return f"# @META:{json.dumps(self.__dict__)}\n# This comment contains machine-readable metadata that should not be modified"


class YamlTestcase:
    def __init__(self, data: Any, metadata: Optional[TestCaseMetadata] = None):
        self.data = data[0] if isinstance(data, list) and len(data) == 1 else data
        self.metadata = metadata or TestCaseMetadata.create_new()

    def to_yaml(self) -> str:
        """Convert spec to YAML string with metadata comment"""
        # Ensure data is wrapped in a list if it's a dict
        yaml_data = [self.data] if isinstance(self.data, dict) else self.data
        yaml_str = yaml.dump(yaml_data, sort_keys=False)
        return f"{self.metadata.to_comment()}\n{yaml_str}"


def parse_yaml_with_testcases(content: str) -> List[YamlTestcase]:
    """Parse YAML content and extract test cases with their metadata"""
    test_cases = []
    current_lines = []
    current_metadata = None

    lines = content.splitlines()

    for line in lines:
        if line.strip().startswith("# @META:"):
            # If we have accumulated lines, process them as a test case
            if current_lines:
                try:
                    test_case_data = yaml.safe_load("\n".join(current_lines))
                    if test_case_data:
                        test_cases.append(
                            YamlTestcase(test_case_data, current_metadata)
                        )
                except yaml.YAMLError as e:
                    logger.warning(f"Failed to parse YAML content: {e}")
                current_lines = []

            current_metadata = TestCaseMetadata.from_comment(line)
        elif line.strip() and not line.strip().startswith("#"):
            current_lines.append(line)

        # Empty line could be a separator between test cases
        elif not line.strip() and current_lines:
            try:
                test_case_data = yaml.safe_load("\n".join(current_lines))
                if test_case_data:
                    test_cases.append(YamlTestcase(test_case_data, current_metadata))
                current_lines = []
                current_metadata = None
            except yaml.YAMLError as e:
                logger.warning(f"Failed to parse YAML content: {e}")

    # Process any remaining lines
    if current_lines:
        try:
            test_case_data = yaml.safe_load("\n".join(current_lines))
            if test_case_data:
                test_cases.append(YamlTestcase(test_case_data, current_metadata))
        except yaml.YAMLError as e:
            logger.warning(f"Failed to parse YAML content: {e}")

    return test_cases


def load_spec(file_path: Path) -> List[YamlTestcase]:
    """Load test cases from a YAML file"""
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(file_path) as f:
        content = f.read()

    return parse_yaml_with_testcases(content)


def save_spec(file_path: Path, test_cases: List[YamlTestcase]) -> None:
    """Save test cases to a YAML file"""
    content = "\n\n".join(test_case.to_yaml() for test_case in test_cases)
    with open(file_path, "w") as f:
        f.write(content)
