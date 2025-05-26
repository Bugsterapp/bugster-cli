"""
YAML Spec parser with metadata handling.
"""

from datetime import datetime, UTC
import uuid
from typing import List, Dict, Any, Optional
from pathlib import Path
import yaml
import json
from dataclasses import dataclass
from loguru import logger


@dataclass
class SpecMetadata:
    id: str
    last_modified: str

    @classmethod
    def create_new(cls) -> "SpecMetadata":
        """Create new metadata with default values"""
        return cls(id=str(uuid.uuid4()), last_modified=datetime.now(UTC).isoformat())

    @classmethod
    def from_comment(cls, comment: str) -> Optional["SpecMetadata"]:
        """Try to parse metadata from a comment string"""
        try:
            if not comment.startswith("# @META:"):
                return None

            meta_dict = json.loads(comment[8:].strip())
            # Ensure all required fields exist
            meta_dict.setdefault("id", str(uuid.uuid4()))
            meta_dict.setdefault("last_modified", datetime.now(UTC).isoformat())

            # Remove version if present (for backwards compatibility)
            meta_dict.pop("version", None)

            return cls(**meta_dict)
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Failed to parse metadata from comment: {e}")
            return None

    def to_comment(self) -> str:
        """Convert metadata to YAML comment format"""
        return f"# @META:{json.dumps(self.__dict__)}"


class YamlSpec:
    def __init__(self, data: Any, metadata: Optional[SpecMetadata] = None):
        self.data = data[0] if isinstance(data, list) and len(data) == 1 else data
        self.metadata = metadata or SpecMetadata.create_new()

    def to_yaml(self) -> str:
        """Convert spec to YAML string with metadata comment"""
        # Ensure data is wrapped in a list if it's a dict
        yaml_data = [self.data] if isinstance(self.data, dict) else self.data
        yaml_str = yaml.dump(yaml_data, sort_keys=False)
        return f"{self.metadata.to_comment()}\n{yaml_str}"


def parse_yaml_with_specs(content: str) -> List[YamlSpec]:
    """Parse YAML content and extract specs with their metadata"""
    specs = []
    current_lines = []
    current_metadata = None

    lines = content.splitlines()

    for line in lines:
        if line.strip().startswith("# @META:"):
            # If we have accumulated lines, process them as a spec
            if current_lines:
                try:
                    spec_data = yaml.safe_load("\n".join(current_lines))
                    if spec_data:
                        specs.append(YamlSpec(spec_data, current_metadata))
                except yaml.YAMLError as e:
                    logger.warning(f"Failed to parse YAML content: {e}")
                current_lines = []

            current_metadata = SpecMetadata.from_comment(line)
        elif line.strip() and not line.strip().startswith("#"):
            current_lines.append(line)

        # Empty line could be a separator between specs
        elif not line.strip() and current_lines:
            try:
                spec_data = yaml.safe_load("\n".join(current_lines))
                if spec_data:
                    specs.append(YamlSpec(spec_data, current_metadata))
                current_lines = []
                current_metadata = None
            except yaml.YAMLError as e:
                logger.warning(f"Failed to parse YAML content: {e}")

    # Process any remaining lines
    if current_lines:
        try:
            spec_data = yaml.safe_load("\n".join(current_lines))
            if spec_data:
                specs.append(YamlSpec(spec_data, current_metadata))
        except yaml.YAMLError as e:
            logger.warning(f"Failed to parse YAML content: {e}")

    return specs


def load_yaml_specs(file_path: Path) -> List[YamlSpec]:
    """Load specs from a YAML file"""
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(file_path) as f:
        content = f.read()

    return parse_yaml_with_specs(content)


def save_yaml_specs(file_path: Path, specs: List[YamlSpec]) -> None:
    """Save specs to a YAML file"""
    content = "\n\n".join(spec.to_yaml() for spec in specs)
    with open(file_path, "w") as f:
        f.write(content)
