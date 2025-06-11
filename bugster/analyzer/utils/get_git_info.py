from dataclasses import dataclass

from git import InvalidGitRepositoryError, Repo
from loguru import logger


@dataclass
class GitInfo:
    """Git repository information class."""

    branch: str
    commit: str

    def to_dict(self) -> dict:
        """Convert the GitInfo object to a dictionary."""
        return {
            "branch": self.branch,
            "commit": self.commit,
        }


def get_git_info() -> GitInfo:
    """Get Git repository information."""
    try:
        repo = Repo(search_parent_directories=True)
        branch = repo.active_branch.name
        commit = repo.head.commit.hexsha
        return GitInfo(branch=branch, commit=commit).to_dict()
    except (InvalidGitRepositoryError, Exception) as error:
        logger.error("Failed to get git info {}", error)
        return GitInfo(branch=None, commit=None).to_dict()
