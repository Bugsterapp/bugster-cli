from typing import Optional

from loguru import logger
from rich.console import Console

from bugster.clients.http_client import BugsterHTTPClient
from bugster.libs.utils.enums import BugsterApiPath, GitCommand
from bugster.libs.utils.git import get_diff_changes_per_page
from bugster.libs.utils.nextjs.import_tree_generator import generate_import_tree

console = Console()


class PageAgent:
    """Represents a page and its assigned agents."""

    def __init__(self, page: str, agents: list[str]):
        self.page = page
        self.agents = agents


class DestructiveService:
    """Service for destructive agent testing."""

    def __init__(self):
        self._import_tree: Optional[dict] = None
        self._diff_changes_per_page: Optional[dict[str, list[str]]] = None

    @property
    def import_tree(self) -> dict:
        """Get the import tree."""
        if self._import_tree is None:
            self._import_tree = self._get_import_tree()
        return self._import_tree

    @property
    def diff_changes_per_page(self) -> dict[str, list[str]]:
        """Get the diff changes per page."""
        if self._diff_changes_per_page is None:
            self._diff_changes_per_page = self._get_diff_changes_per_page()
        return self._diff_changes_per_page

    def _get_import_tree(self) -> dict:
        """Get the import tree of the user's repository."""
        return generate_import_tree()

    def _get_diff_changes_per_page(self) -> dict[str, list[str]]:
        """Get the diff changes per page using git changes."""
        return get_diff_changes_per_page(
            import_tree=self.import_tree, git_command=GitCommand.DIFF_CHANGES
        )

    def get_page_agents_assignments(self) -> list[PageAgent]:
        """Get page agent assignments from the API."""
        if not self.diff_changes_per_page:
            console.print("✓ No changes detected - no pages need destructive testing")
            return []

        console.print(f"✓ Found {len(self.diff_changes_per_page)} pages with changes")

        # Prepare payload for API
        pages_data = []
        for page, diffs in self.diff_changes_per_page.items():
            combined_diff = "\n==========\n".join(diffs)
            pages_data.append({"page": page, "diff": combined_diff})

        payload = {"pages": pages_data}

        try:
            with BugsterHTTPClient() as client:
                logger.info("Requesting destructive agent assignments from API...")
                response = client.post(
                    endpoint=BugsterApiPath.DESTRUCTIVE_AGENTS.value, json=payload
                )

                # Parse response
                page_agents = []
                for page_agent_data in response.get("page_agents", []):
                    page_agent = PageAgent(
                        page=page_agent_data["page"], agents=page_agent_data["agents"]
                    )
                    page_agents.append(page_agent)

                logger.info(f"Received {len(page_agents)} page agent assignments")
                return page_agents

        except Exception as e:
            logger.error(f"Failed to get page agent assignments: {e}")
            console.print(f"[red]Error getting agent assignments: {e}[/red]")
            raise

    def get_diff_for_page(self, page: str) -> str:
        """Get the combined diff for a specific page."""
        if page not in self.diff_changes_per_page:
            return ""

        return "\n==========\n".join(self.diff_changes_per_page[page])
