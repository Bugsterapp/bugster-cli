import glob
import os
from typing import Dict, List, Literal, TypedDict, Union

from loguru import logger

from bugster.libs.utils.files import filter_path


def filter_paths(all_paths: List[str]):
    """Filter paths based on ignore patterns and `.gitignore` rules."""
    filtered_paths = []

    for path in all_paths:
        filtered_path = filter_path(path=path)

        if filtered_path:
            filtered_paths.append(filtered_path)

    filtered_paths.sort()
    return filtered_paths


def get_paths(dir_path: str) -> List[str]:
    """Get all file paths in a directory, excluding test files and specific directories, while respecting
    `.gitignore` rules."""
    original_dir = os.getcwd()
    os.chdir(dir_path)
    all_paths = glob.glob("**/*", recursive=True)
    paths = filter_paths(all_paths=all_paths)
    os.chdir(original_dir)
    return paths


class FileNode(TypedDict):
    path: str
    name: str
    type: Literal["file"]
    extension: str


class DirectoryNode(TypedDict):
    path: str
    name: str
    type: Literal["directory"]
    children: List[Union["DirectoryNode", FileNode]]


TreeNode = Union[DirectoryNode, FileNode]


def get_tree_structure(source_dir) -> TreeNode:
    """Get the tree structure of the source directory."""
    logger.info("Building application structure tree...")
    paths = get_paths(source_dir)
    root_node: DirectoryNode = {
        "path": "",
        "name": os.path.basename(source_dir),
        "type": "directory",
        "children": [],
    }
    dir_map: Dict[str, DirectoryNode] = {}
    dir_map[""] = root_node

    def ensure_directory_path(dir_path: str) -> DirectoryNode:
        """Helper function to ensure a directory path exists in the tree and returns the node for that
        directory."""
        if dir_path in dir_map:
            return dir_map[dir_path]

        parent_path = os.path.dirname(dir_path)
        parent_node = (
            root_node if parent_path == "." else ensure_directory_path(parent_path)
        )
        dir_name = os.path.basename(dir_path)
        dir_node: DirectoryNode = {
            "path": dir_path,
            "name": dir_name,
            "type": "directory",
            "children": [],
        }
        parent_node["children"].append(dir_node)
        dir_map[dir_path] = dir_node
        return dir_node

    for file_path in paths:
        if not file_path:
            continue

        is_directory = not os.path.splitext(file_path)[1]

        if is_directory:
            ensure_directory_path(file_path)
        else:
            dir_path = os.path.dirname(file_path)
            parent_node = (
                root_node if dir_path == "." else ensure_directory_path(dir_path)
            )
            file_name = os.path.basename(file_path)
            file_node: FileNode = {
                "path": file_path,
                "name": file_name,
                "type": "file",
                "extension": os.path.splitext(file_path)[1],
            }
            parent_node["children"].append(file_node)

    return root_node
