import uuid
from datetime import datetime, timezone
from pathlib import PosixPath

from loguru import logger
from rich.console import Console
from rich.status import Status
from rich.text import Text

from bugster.libs.utils.enums import GitCommand
from bugster.libs.utils.files import get_specs_pages
from bugster.libs.utils.git import get_diff_changes_per_page
from bugster.libs.utils.nextjs.pages_finder import (
    is_nextjs_page,
)

console = Console()


def parse_spec_page_with_file_path(data, spec_path):
    """Parser for spec page with file path."""
    return {
        "file": PosixPath(spec_path),
        "content": [
            {
                **data,
                "metadata": {
                    "id": str(uuid.uuid4()),
                    "last_modified": datetime.now(timezone.utc).isoformat(),
                },
            }
        ],
    }


def format_diff_branch_head_command():
    """Format the diff branch head command.

    NOTE: At the moment, we only support diffing against the main branch. We will support diffing against any branch the user wants in the future.
    """
    target_branch = "origin/main"
    return (
        " ".join(GitCommand.DIFF_BRANCH_AGAINST_TARGET)
        .format(target_branch=target_branch)
        .split(" ")
    )


class DetectAffectedSpecsMixin:
    """Detect affected specs mixin."""

    def detect(self, *args, **kwargs):
        """Detect affected specs."""
        diff_changes_per_page = get_diff_changes_per_page(
            import_tree=self.import_tree, git_command=format_diff_branch_head_command()
        )
        affected_specs = []
        specs_pages = get_specs_pages(parser=parse_spec_page_with_file_path)

        for page in diff_changes_per_page.keys():
            if page in specs_pages:
                affected_specs.append(specs_pages[page])

        logger.info("Affected specs: {}", affected_specs)
        return affected_specs


class UpdateMixin:
    """Update mixin."""

    def update(self, *args, **kwargs):
        """Update existing specs."""
        file_paths = self.mapped_changes["modified"]
        console.print(f"✓ Found {len(file_paths)} modified files")
        diff_changes_per_page = get_diff_changes_per_page(
            import_tree=self.import_tree, git_command=GitCommand.DIFF_CHANGES
        )
        affected_pages = [
            page for page in diff_changes_per_page.keys() if page in file_paths
        ]
        updated_specs = 0
        specs_pages = get_specs_pages()

        for page in affected_pages:
            if page in specs_pages:
                spec = specs_pages[page]
                spec_data = spec["data"]
                spec_path = spec["path"]

                with Status(
                    f"[yellow]Updating: {spec_path}[/yellow]", spinner="dots"
                ) as status:
                    diff = "\n==========\n".join(diff_changes_per_page[page])
                    self.test_cases_service.update_spec_by_diff(
                        spec_data=spec_data, diff_changes=diff, spec_path=spec_path
                    )
                    status.stop()
                    console.print(f"✓ [green]{spec_path}[/green] updated")
                    updated_specs += 1
            else:
                text = Text("✗ Page ")
                text.append(page, style="red")
                text.append(" not found in test cases")
                console.print(text)

        if updated_specs > 0:
            console.print(
                f"✓ Updated {updated_specs} spec{'' if updated_specs == 1 else 's'}"
            )


class SuggestMixin:
    """Suggest mixin."""

    def suggest(self, *args, **kwargs):
        """Suggest new specs."""
        file_paths = self.mapped_changes["new"]
        console.print(f"✓ Found {len(file_paths)} added files")
        diff_changes_per_page = get_diff_changes_per_page(
            import_tree=self.import_tree, git_command=GitCommand.DIFF_HEAD
        )
        suggested_specs = []

        for page in diff_changes_per_page.keys():
            with Status(
                f"[yellow]Suggesting new spec for {page}[/yellow]", spinner="dots"
            ) as status:
                diff = "\n==========\n".join(diff_changes_per_page[page])
                self.test_cases_service.suggest_spec_by_diff(
                    page_path=page, diff_changes=diff
                )
                status.stop()
                console.print(f"✓ [green]{page}[/green] suggested")
                suggested_specs.append(page)

        if len(suggested_specs) > 0:
            for spec in suggested_specs:
                console.print(f"⚠️  Suggested new spec: {spec}")


class DeleteMixin:
    """Delete mixin."""

    def delete(self, *args, **kwargs):
        """Delete existing specs."""
        file_paths = self.mapped_changes["deleted"]
        console.print(f"✓ Found {len(file_paths)} deleted files")
        deleted_pages = set()

        for file_path in file_paths:
            if is_nextjs_page(file_path=file_path):
                deleted_pages.add(file_path)

        specs_pages = get_specs_pages()
        deleted_specs = 0

        for page in deleted_pages:
            if page in specs_pages:
                spec = specs_pages[page]
                spec_path = spec["path"]

                with Status(
                    f"[yellow]Deleting: {spec_path}[/yellow]", spinner="dots"
                ) as status:
                    self.test_cases_service.delete_spec_by_spec_path(
                        spec_path=spec_path
                    )
                    status.stop()
                    console.print(f"✓ [green]{spec_path}[/green] deleted")
                    deleted_specs += 1
            else:
                text = Text("✗ Page ")
                text.append(page, style="red")
                text.append(" not found in test cases")
                console.print(text)

        if deleted_specs > 0:
            console.print(
                f"✓ Deleted {deleted_specs} spec{'' if deleted_specs == 1 else 's'}"
            )
