import os
from typing import Dict, List, Set

from rich.console import Console

from bugster.analyzer.core.framework_detector.main import get_project_info
from bugster.constants import BUGSTER_DIR
from bugster.libs.utils.nextjs.import_tree_generator import ImportTreeGenerator

console = Console()


def find_pages_that_use_file(file_path: str) -> list[str]:
    """Find the Next.js pages that use the given file."""
    framework_id = get_project_info()["data"]["frameworks"][0]["id"]
    cache_framework_dir = os.path.join(BUGSTER_DIR, framework_id)
    output_file = os.path.join(cache_framework_dir, "import_tree.json")
    generator = ImportTreeGenerator()
    tree = generator.generate_tree()
    generator.save_to_json(tree=tree, filename=output_file)
    results = find_pages_using_file(tree_data=tree, target_file=file_path)

    if results:
        return [result["page"] for result in results]
    else:
        console.print(f"✗ File '{file_path}' is not imported by any page")
        return []


def find_pages_using_file(tree_data: Dict, target_file: str) -> List[Dict]:
    """Find all pages that directly or indirectly import the target file.

    :param tree_data: The import tree JSON data.
    :param target_file: The file path to search for (e.g., "src/components/not-authenticated/about/index.js").
    :return: List of dictionaries with page info and import path.
    """
    results = []

    for page_path, page_data in tree_data.items():
        # Search recursively through this page's imports
        import_chain = find_file_in_imports(
            page_data.get("imports", {}), target_file, []
        )

        if import_chain:
            results.append(
                {
                    "page": page_path,
                    "import_chain": import_chain,
                    "depth": len(import_chain) - 1,  # How many levels deep
                }
            )

    return results


def find_file_in_imports(
    imports: Dict, target_file: str, current_chain: List[str]
) -> List[str]:
    """Recursively search through imports to find the target file."""
    for import_path, import_data in imports.items():
        if isinstance(import_data, dict):
            # Check if this is the target file
            if import_data.get("path") == target_file:
                return current_chain + [import_path]

            # If not circular, search deeper
            if not import_data.get("circular", False) and "imports" in import_data:
                nested_result = find_file_in_imports(
                    import_data["imports"], target_file, current_chain + [import_path]
                )
                if nested_result:
                    return nested_result

    return []


def get_all_imported_files(tree_data: Dict) -> Set[str]:
    """Get a set of all files that are imported anywhere in the tree."""
    all_files = set()

    def collect_files(imports: Dict):
        for import_data in imports.values():
            if isinstance(import_data, dict) and "path" in import_data:
                all_files.add(import_data["path"])
                if "imports" in import_data and not import_data.get("circular", False):
                    collect_files(import_data["imports"])

    for page_data in tree_data.values():
        collect_files(page_data.get("imports", {}))

    return all_files


def create_reverse_index(tree_data: Dict) -> Dict[str, List[str]]:
    """Create a reverse index: file -> list of pages that use it. This is more efficient for multiple lookups."""
    reverse_index = {}

    for page_path, page_data in tree_data.items():
        imported_files = get_files_from_imports(page_data.get("imports", {}))

        for file_path in imported_files:
            if file_path not in reverse_index:
                reverse_index[file_path] = []
            reverse_index[file_path].append(page_path)

    return reverse_index


def get_files_from_imports(imports: Dict, visited: Set[str] = None) -> Set[str]:
    """Get all files imported from this import tree."""
    if visited is None:
        visited = set()

    files = set()

    for import_data in imports.values():
        if isinstance(import_data, dict) and "path" in import_data:
            file_path = import_data["path"]
            files.add(file_path)

            # Avoid circular references
            if file_path not in visited and not import_data.get("circular", False):
                visited.add(file_path)
                if "imports" in import_data:
                    files.update(
                        get_files_from_imports(import_data["imports"], visited)
                    )

    return files
