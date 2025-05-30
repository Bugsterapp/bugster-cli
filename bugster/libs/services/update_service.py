from abc import ABC, abstractmethod
from typing import Optional

from bugster.libs.mixins import DeleteMixin, SuggestMixin, UpdateMixin
from bugster.libs.services.test_cases_service import TestCasesService
from bugster.libs.utils.enums import GitCommand
from bugster.libs.utils.git import parse_diff_status, run_git_command
from bugster.libs.utils.nextjs.import_tree_generator import (
    generate_and_save_import_tree,
)


class UpdateService(ABC):
    """Base class for update services."""

    def __init__(self, test_cases_service: Optional["TestCasesService"] = None):
        self._test_cases_service = test_cases_service
        self._mapped_changes: Optional[dict] = None
        self._import_tree: Optional[dict] = None

    @property
    def test_cases_service(self) -> TestCasesService:
        """Get the test cases service."""
        if self._test_cases_service is None:
            self._test_cases_service = TestCasesService()
        return self._test_cases_service

    @property
    def mapped_changes(self) -> dict:
        """Get the mapped changes."""
        if self._mapped_changes is None:
            self._setup()
        return self._mapped_changes

    @property
    def import_tree(self) -> dict:
        """Get the import tree."""
        if self._import_tree is None:
            self._setup()
        return self._import_tree

    def _get_mapped_changes(self) -> dict:
        """Get the mapped changes of the user's repository."""
        diff_status = run_git_command(cmd_key=GitCommand.DIFF_STATUS)
        return parse_diff_status(diff_status=diff_status)

    def _get_import_tree(self) -> dict:
        """Get the import tree of the user's repository."""
        return generate_and_save_import_tree()

    def _setup(self):
        """Setup the update service."""
        self._import_tree = self._get_import_tree()
        self._mapped_changes = self._get_mapped_changes()

    @abstractmethod
    def run(self):
        """Run the update service."""
        pass


class SuggestOnlyService(UpdateService, SuggestMixin):
    """Suggest only service."""

    def run(self):
        """Run the suggest only service."""
        self.suggest()


class DeleteOnlyService(UpdateService, DeleteMixin):
    """Delete only service."""

    def run(self):
        """Run the delete only service."""
        self.delete()


class UpdateOnlyService(UpdateService, UpdateMixin):
    """Update only service."""

    def run(self):
        """Run the update only service."""
        self.update()


class DefaultUpdateService(UpdateService, UpdateMixin, SuggestMixin, DeleteMixin):
    """Default update service."""

    def run(self):
        """Run the default update service."""
        self.update()
        self.suggest()
        self.delete()


def get_update_service(update_only: bool, suggest_only: bool, delete_only: bool):
    """Get the update service based on the flags."""
    if update_only:
        return UpdateOnlyService()
    elif suggest_only:
        return SuggestOnlyService()
    elif delete_only:
        return DeleteOnlyService()
    else:
        return DefaultUpdateService()
