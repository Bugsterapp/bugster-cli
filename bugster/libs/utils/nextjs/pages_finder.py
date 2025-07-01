from pathlib import Path
from typing import Dict, List, Set

from rich.console import Console

console = Console()


def find_pages_that_use_file(file_path: str, import_tree: Dict) -> list[str]:
    """Find the Next.js pages that use the given file."""
    results = find_pages_using_file(tree_data=import_tree, target_file=file_path)

    if results:
        return [result["page"] for result in results]

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
            if target_file.endswith(import_data.get("path")):
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


def is_nextjs_page(file_path: str) -> bool:
    """Determine if a file path represents a Next.js page.

    Next.js pages are typically located in:
    - pages/ directory (Pages Router)
    - app/ directory (App Router - page.tsx/jsx files)
    - src/pages/ directory
    - src/app/ directory

    This excludes:
    - Components (usually in components/, ui/, shared/ etc.)
    - Hooks (files starting with 'use' or in hooks/ directory)
    - Utilities (utils/, lib/, helpers/ directories)
    - API routes (api/ subdirectory)
    - Layout files, loading files, error files, etc.
    - Non-JS/TS files
    """
    if not file_path:
        return False

    # Convert to Path object for easier manipulation
    path = Path(file_path)

    # Must be a JavaScript/TypeScript file
    if path.suffix not in [".js", ".jsx", ".ts", ".tsx"]:
        return False

    # Get path parts for analysis
    parts = path.parts

    # Skip if it's in common non-page directories
    non_page_dirs = {
        "components",
        "hooks",
        "utils",
        "lib",
        "helpers",
        "shared",
        "common",
        "constants",
        "types",
        "interfaces",
        "services",
        "store",
        "context",
        "providers",
        "styles",
        "public",
    }

    if any(part.lower() in non_page_dirs for part in parts):
        return False

    # Skip hook files (files starting with 'use')
    if path.stem.startswith("use") and path.stem != "use":
        return False

    # Check for App Router pages (app directory structure)
    if "app" in parts:
        app_index = parts.index("app")
        # Must be named 'page' (page.tsx, page.jsx, etc.)
        if path.stem == "page":
            # Skip API routes in app directory
            remaining_parts = parts[app_index + 1 :]
            if "api" not in remaining_parts:
                return True
        return False

    # Check for Pages Router (pages directory structure)
    if "pages" in parts:
        pages_index = parts.index("pages")
        remaining_parts = parts[pages_index + 1 :]

        # Skip API routes
        if remaining_parts and remaining_parts[0] == "api":
            return False

        # Skip special Next.js files
        special_files = {
            "_app",
            "_document",
            "_error",
            "404",
            "500",
            "_middleware",
            "middleware",
        }

        if path.stem in special_files:
            return False

        return True

    # For files in src/ directory, check if they follow the same patterns
    if "src" in parts:
        src_index = parts.index("src")
        remaining_parts = parts[src_index + 1 :]

        if len(remaining_parts) > 0:
            # Recursively check the path after src/
            sub_path = "/".join(remaining_parts)
            return is_nextjs_page(sub_path)

    return False


def get_affected_pages(file_paths: list[str], import_tree: dict) -> set[str]:
    """Get the affected pages."""
    affected_pages = set()

    for file_path in file_paths:
        if is_nextjs_page(file_path=file_path):
            affected_pages.add(file_path)
        else:
            pages = find_pages_that_use_file(
                file_path=file_path, import_tree=import_tree
            )

            if pages:
                for page in pages:
                    affected_pages.add(page)

    return affected_pages
