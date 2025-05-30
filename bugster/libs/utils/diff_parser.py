import re
from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class FileChange:
    """Single file changes."""

    old_path: str
    new_path: str
    old_hash: str
    new_hash: str
    hunks: List[Dict[str, Any]]
    is_deleted: bool = False
    is_new: bool = False
    file_mode: str = None


@dataclass
class ParsedDiff:
    """Entire parsed diff."""

    files: List[FileChange]

    def to_llm_format(self, file_change: FileChange = None) -> str:
        """Convert to human-readable format for LLMs."""
        if file_change:
            return self._format_single_file(file_change)
        else:
            result = []

            for file_change in self.files:
                result.append(self._format_single_file(file_change))
                result.append("=" * 60)
                result.append("")

            return "\n".join(result)

    def _format_single_file(self, file_change: FileChange) -> str:
        """Format a single file change for LLM consumption."""
        result = []

        if file_change.is_deleted:
            result.append(f"🗑️  File DELETED: {file_change.old_path}")
            result.append(f"   File mode: {file_change.file_mode}")
            result.append(f"   Old version: {file_change.old_hash}")
            result.append(f"   New version: {file_change.new_hash}")
            result.append("   This file was completely removed from the repository.")
        elif file_change.is_new:
            result.append(f"✨ File ADDED: {file_change.new_path}")
            result.append(f"   File mode: {file_change.file_mode}")
            result.append(f"   Old version: {file_change.old_hash}")
            result.append(f"   New version: {file_change.new_hash}")
            result.append("   This is a completely new file added to the repository.")
        else:
            result.append(f"📁 File MODIFIED: {file_change.new_path}")
            result.append(f"   Old version: {file_change.old_hash}")
            result.append(f"   New version: {file_change.new_hash}")

        result.append("")

        for i, hunk in enumerate(file_change.hunks, 1):
            result.append(f"   📝 Change #{i}:")
            result.append(
                f"      Location: Lines {hunk['old_start']}-{hunk['old_start'] + hunk['old_count'] - 1} → Lines {hunk['new_start']}-{hunk['new_start'] + hunk['new_count'] - 1}"
            )

            if hunk["added_lines"]:
                result.append("      ✅ Added lines:")
                for line in hunk["added_lines"]:
                    result.append(f"         + {line}")

            if hunk["removed_lines"]:
                result.append("      ❌ Removed lines:")
                for line in hunk["removed_lines"]:
                    result.append(f"         - {line}")

            if hunk["context_lines"]:
                result.append("      📄 Context (unchanged):")
                for line in hunk["context_lines"]:
                    result.append(f"           {line}")

            result.append("")

        return "\n".join(result)


def parse_git_diff(diff_text: str) -> ParsedDiff:
    """Parse a git diff string into a structured format.

    :param diff_text: Raw git diff output as string.
    :return: ParsedDiff object containing structured diff information.
    """
    files = []
    lines = diff_text.strip().split("\n")
    i = 0

    while i < len(lines):
        line = lines[i]

        # Look for file header (diff --git)
        if line.startswith("diff --git"):
            # Extract file paths
            git_match = re.match(r"diff --git a/(.*) b/(.*)", line)
            if not git_match:
                i += 1
                continue

            old_path = git_match.group(1)
            new_path = git_match.group(2)

            # Check for deleted/new file in the next few lines
            is_deleted = False
            is_new = False
            file_mode = None
            j = i + 1

            # Look ahead for file mode changes or index line
            while j < len(lines) and j < i + 5:  # Check next few lines
                if lines[j].startswith("deleted file mode"):
                    is_deleted = True
                    mode_match = re.match(r"deleted file mode (\d+)", lines[j])
                    file_mode = mode_match.group(1) if mode_match else None
                    break
                elif lines[j].startswith("new file mode"):
                    is_new = True
                    mode_match = re.match(r"new file mode (\d+)", lines[j])
                    file_mode = mode_match.group(1) if mode_match else None
                    break
                elif lines[j].startswith("index"):
                    break
                j += 1

            # Skip to index line
            i += 1
            while i < len(lines) and not lines[i].startswith("index"):
                i += 1

            if i >= len(lines):
                break

            # Extract hash information
            index_match = re.match(r"index ([a-f0-9]+)\.\.([a-f0-9]+)", lines[i])
            old_hash = index_match.group(1) if index_match else ""
            new_hash = index_match.group(2) if index_match else ""

            # Additional check for new files based on hash (0000000 indicates new file)
            if old_hash == "0000000" or old_hash.startswith("000000"):
                is_new = True
            elif new_hash == "0000000" or new_hash.startswith("000000"):
                is_deleted = True

            # Skip file mode and path lines
            i += 1
            while i < len(lines) and (
                lines[i].startswith("---")
                or lines[i].startswith("+++")
                or lines[i].startswith("deleted file mode")
                or lines[i].startswith("new file mode")
            ):
                i += 1

            # Parse hunks (deleted files typically have no hunks, new files have only additions)
            hunks = []
            while i < len(lines) and lines[i].startswith("@@"):
                hunk = parse_hunk(lines, i)
                hunks.append(hunk["hunk"])
                i = hunk["next_index"]

                # Stop if we hit another file
                if i < len(lines) and lines[i].startswith("diff --git"):
                    break

            files.append(
                FileChange(
                    old_path=old_path,
                    new_path=new_path,
                    old_hash=old_hash,
                    new_hash=new_hash,
                    hunks=hunks,
                    is_deleted=is_deleted,
                    is_new=is_new,
                    file_mode=file_mode,
                )
            )
        else:
            i += 1

    return ParsedDiff(files)


def parse_hunk(lines: List[str], start_index: int) -> Dict[str, Any]:
    """Parse a single hunk starting at the given index."""
    hunk_header = lines[start_index]

    # Extract hunk information: @@ -old_start,old_count +new_start,new_count @@
    hunk_match = re.match(r"@@ -(\d+),?(\d*) \+(\d+),?(\d*) @@", hunk_header)
    if not hunk_match:
        return {"hunk": {}, "next_index": start_index + 1}

    old_start = int(hunk_match.group(1))
    old_count = int(hunk_match.group(2)) if hunk_match.group(2) else 1
    new_start = int(hunk_match.group(3))
    new_count = int(hunk_match.group(4)) if hunk_match.group(4) else 1

    # Parse hunk content
    i = start_index + 1
    added_lines = []
    removed_lines = []
    context_lines = []

    while i < len(lines):
        line = lines[i]

        # Stop at next hunk or file
        if line.startswith("@@") or line.startswith("diff --git"):
            break

        if line.startswith("+"):
            added_lines.append(line[1:])  # Remove the + prefix
        elif line.startswith("-"):
            removed_lines.append(line[1:])  # Remove the - prefix
        elif line.startswith(" "):
            context_lines.append(line[1:])  # Remove the space prefix
        elif line.strip() == "":
            context_lines.append("")  # Empty line

        i += 1

    hunk_data = {
        "old_start": old_start,
        "old_count": old_count,
        "new_start": new_start,
        "new_count": new_count,
        "added_lines": added_lines,
        "removed_lines": removed_lines,
        "context_lines": context_lines,
    }

    return {"hunk": hunk_data, "next_index": i}
