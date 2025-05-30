import json
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Set

from loguru import logger

from bugster.analyzer.core.framework_detector.main import get_project_info
from bugster.constants import BUGSTER_DIR


class ImportTreeGenerator:
    """Generator for analyzing a Next.js application and building a tree structure showing all file imports and
    their dependencies recursively."""

    def __init__(self, root_path: str = "."):
        self.root_path = Path(root_path).resolve()
        self.processed_files: Set[str] = set()
        self.import_tree: Dict[str, Dict] = {}
        self.file_extensions = {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"}

        # Common Next.js directories to scan
        self.scan_dirs = [
            "src",
            "pages",
            "app",
            "components",
            "lib",
            "utils",
            "hooks",
            "styles",
        ]

    def is_valid_file(self, filepath: Path) -> bool:
        """Check if file should be analyzed for imports."""
        return (
            filepath.suffix in self.file_extensions
            and not filepath.name.startswith(".")
            and "node_modules" not in str(filepath)
            and ".next" not in str(filepath)
        )

    def extract_imports(self, filepath: Path) -> List[str]:
        """Extract import statements from a JavaScript/TypeScript file."""
        imports = []

        try:
            with open(filepath, encoding="utf-8") as file:
                content = file.read()

            # Remove comments to avoid false positives
            content = re.sub(r"//.*$", "", content, flags=re.MULTILINE)
            content = re.sub(r"/\*.*?\*/", "", content, flags=re.DOTALL)

            # Match various import patterns
            import_patterns = [
                # import ... from '...'
                r'import\s+(?:.*?\s+from\s+)?[\'"]([^\'"]+)[\'"]',
                # require('...')
                r'require\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)',
                # dynamic import()
                r'import\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)',
                # Next.js dynamic imports
                r'dynamic\s*\(\s*\(\s*\)\s*=>\s*import\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)',
            ]

            for pattern in import_patterns:
                matches = re.findall(pattern, content, re.MULTILINE)
                imports.extend(matches)

        except Exception as e:
            logger.error("Error reading {}: {}", filepath, e)

        return imports

    def resolve_import_path(
        self, import_path: str, current_file: Path
    ) -> Optional[Path]:
        """Resolve import path to actual file path, including TypeScript path mappings."""
        self.load_tsconfig_paths()
        current_dir = current_file.parent
        resolved_path = None

        # Handle TypeScript path mappings (e.g., ~/components/*)
        if self._is_path_mapping(import_path):
            resolved_path = self._resolve_path_mapping(import_path)

        # Handle relative imports (starting with . or ..)
        elif import_path.startswith("./") or import_path.startswith("../"):
            resolved_path = (current_dir / import_path).resolve()

        # Handle absolute imports from root (starting with /)
        elif import_path.startswith("/"):
            resolved_path = (self.root_path / import_path.lstrip("/")).resolve()

        # Handle project-relative imports (no leading . or /)
        else:
            resolved_path = self._resolve_project_relative(import_path, current_dir)

        # If we found a potential path, validate it exists with proper extension
        if resolved_path:
            return self._resolve_with_extensions(resolved_path)

        return None

    def _is_path_mapping(self, import_path: str) -> bool:
        """Check if import path matches any TypeScript path mapping patterns."""
        if not hasattr(self, "path_mappings") or not self.path_mappings:
            return False

        for alias_pattern in self.path_mappings.keys():
            # Convert TypeScript glob pattern to prefix check
            if alias_pattern.endswith("/*"):
                alias_prefix = alias_pattern[:-2]  # Remove /*
                if import_path.startswith(alias_prefix + "/"):
                    return True
            elif import_path == alias_pattern:
                return True

        return False

    def _resolve_path_mapping(self, import_path: str) -> Optional[Path]:
        """Resolve TypeScript path mapping to actual file path."""
        if not hasattr(self, "path_mappings") or not self.path_mappings:
            return None

        for alias_pattern, target_patterns in self.path_mappings.items():
            # Handle glob patterns (e.g., ~/components/*)
            if alias_pattern.endswith("/*"):
                alias_prefix = alias_pattern[:-2]  # Remove /*
                if import_path.startswith(alias_prefix + "/"):
                    # Extract the remaining path after the alias
                    remaining_path = import_path[len(alias_prefix) + 1 :]

                    # Try each target pattern
                    for target_pattern in target_patterns:
                        if target_pattern.endswith("/*"):
                            target_base = target_pattern[:-2]  # Remove /*
                            full_target = f"{target_base}/{remaining_path}"
                        else:
                            full_target = f"{target_pattern}/{remaining_path}"

                        # Resolve relative to project root
                        if full_target.startswith("./"):
                            resolved_path = (self.root_path / full_target[2:]).resolve()
                        else:
                            resolved_path = (self.root_path / full_target).resolve()

                        if self._check_file_exists(resolved_path):
                            return resolved_path

            # Handle exact matches (e.g., ~/configuration)
            elif import_path == alias_pattern:
                for target_pattern in target_patterns:
                    if target_pattern.startswith("./"):
                        resolved_path = (self.root_path / target_pattern[2:]).resolve()
                    else:
                        resolved_path = (self.root_path / target_pattern).resolve()

                    if self._check_file_exists(resolved_path):
                        return resolved_path

        return None

    def _resolve_project_relative(
        self, import_path: str, current_dir: Path
    ) -> Optional[Path]:
        """Resolve project-relative imports with fallback hierarchy."""
        # First try from current directory
        test_from_current = (current_dir / import_path).resolve()
        if self._check_file_exists(test_from_current):
            return test_from_current

        # Try from project root
        test_from_root = (self.root_path / import_path).resolve()
        if self._check_file_exists(test_from_root):
            return test_from_root

        # Try from src directory if it exists
        src_path = self.root_path / "src"
        if src_path.exists():
            test_from_src = (src_path / import_path).resolve()
            if self._check_file_exists(test_from_src):
                return test_from_src

        return None

    def load_tsconfig_paths(self, tsconfig_path: Optional[Path] = None) -> None:
        """Load TypeScript path mappings from tsconfig.json."""
        if tsconfig_path is None:
            tsconfig_path = self.root_path / "tsconfig.json"

        if not tsconfig_path.exists():
            self.path_mappings = {}
            return

        try:
            with open(tsconfig_path) as f:
                tsconfig = json.load(f)

            compiler_options = tsconfig.get("compilerOptions", {})
            self.path_mappings = compiler_options.get("paths", {})

            # Store base URL if present
            self.base_url = compiler_options.get("baseUrl", "./")

        except (OSError, json.JSONDecodeError) as e:
            logger.warning("Could not load tsconfig.json: {}", e)
            self.path_mappings = {}

    def _check_file_exists(self, path: Path) -> bool:
        """Check if a file exists with any valid extension."""
        return self._resolve_with_extensions(path) is not None

    def _resolve_with_extensions(self, resolved_path: Path) -> Optional[Path]:
        """Try to resolve a path with different file extensions."""
        # If path already has extension and exists
        if resolved_path.suffix and resolved_path.exists():
            return resolved_path

        # Try different file extensions if no extension provided
        if not resolved_path.suffix:
            for ext in [".js", ".jsx", ".ts", ".tsx", ".mjs"]:
                test_path = resolved_path.with_suffix(ext)
                if test_path.exists():
                    return test_path

            # Check for index files
            for ext in [".js", ".jsx", ".ts", ".tsx"]:
                index_path = resolved_path / f"index{ext}"
                if index_path.exists():
                    return index_path

        return None

    def analyze_file(self, filepath: Path, depth: int = 0) -> Dict:
        """Analyze a single file and its imports recursively."""
        relative_path = str(filepath.relative_to(self.root_path))

        # Avoid infinite recursion
        if relative_path in self.processed_files or depth > 20:
            return {"path": relative_path, "imports": {}, "circular": True}

        self.processed_files.add(relative_path)

        imports = self.extract_imports(filepath)
        import_tree = {}

        for import_path in imports:
            resolved_path = self.resolve_import_path(import_path, filepath)

            if resolved_path and self.is_valid_file(resolved_path):
                try:
                    relative_resolved = str(resolved_path.relative_to(self.root_path))
                    import_tree[import_path] = self.analyze_file(
                        resolved_path, depth + 1
                    )
                except ValueError:
                    # File is outside project root - skip it
                    continue
            # Skip external packages entirely - only include local unresolved files
            elif not self._is_external_package(import_path):
                import_tree[import_path] = {"unresolved": True, "path": import_path}

        # Only count local imports (resolved + unresolved non-external)
        local_imports = [k for k, v in import_tree.items()]

        return {
            "path": relative_path,
            "imports": import_tree,
            "import_count": len(local_imports),
        }

    def _is_external_package(self, import_path: str) -> bool:
        """Determine if an import is an external npm package."""
        # External packages typically don't start with . / or any local path indicators
        # and don't contain file path separators in the package name part
        if import_path.startswith(".") or import_path.startswith("/"):
            return False

        # Check if it looks like a scoped package (@scope/package) or regular package
        parts = import_path.split("/")
        first_part = parts[0]

        # Scoped packages start with @
        if first_part.startswith("@"):
            return True

        # Common external packages patterns
        external_indicators = [
            "react",
            "next",
            "lodash",
            "axios",
            "moment",
            "express",
            "fs",
            "path",
            "url",
            "crypto",
            "util",
            "os",
            "http",
            "https",
        ]

        # If it's a known external package
        if first_part in external_indicators:
            return True

        # If import contains no path separators, it's likely an npm package
        # But if it contains paths and we couldn't resolve it locally, it might be unresolved local
        if len(parts) == 1:
            return True

        return False

    def find_entry_points(self) -> List[Path]:
        """Find all page files in Next.js pages directory."""
        entry_points = []

        # Look for pages directories
        pages_dirs = []
        for pages_dir in ["pages", "src/pages"]:
            pages_path = self.root_path / pages_dir
            if pages_path.exists():
                pages_dirs.append(pages_path)

        # Also check for app directory (App Router)
        for app_dir in ["app", "src/app"]:
            app_path = self.root_path / app_dir
            if app_path.exists():
                pages_dirs.append(app_path)

        # Get all page files from these directories
        for pages_dir in pages_dirs:
            for file in pages_dir.rglob("*"):
                if self.is_valid_file(file):
                    # Skip API routes, middleware, and config files
                    relative_path = str(file.relative_to(pages_dir))
                    if not any(
                        skip in relative_path
                        for skip in [
                            "api/",
                            "_middleware",
                            ".config",
                            "_document",
                            "_error",
                        ]
                    ):
                        entry_points.append(file)

        # If no pages found, fall back to scanning common directories
        if not entry_points:
            for scan_dir in self.scan_dirs:
                scan_path = self.root_path / scan_dir
                if scan_path.exists():
                    for file in scan_path.rglob("*"):
                        if self.is_valid_file(file):
                            entry_points.append(file)

        return sorted(list(set(entry_points)))  # Remove duplicates and sort

    def generate_tree(self, entry_points: List[str] = None) -> Dict:
        """Generate the complete import tree."""
        if entry_points:
            files_to_analyze = [Path(self.root_path / ep) for ep in entry_points]
        else:
            files_to_analyze = self.find_entry_points()

        if not files_to_analyze:
            logger.warning(
                "No entry points found. Scanning all JavaScript/TypeScript files..."
            )
            files_to_analyze = []
            for scan_dir in self.scan_dirs:
                scan_path = self.root_path / scan_dir
                if scan_path.exists():
                    for file in scan_path.rglob("*"):
                        if self.is_valid_file(file):
                            files_to_analyze.append(file)

        tree = {}
        # Process each file separately to avoid cross-contamination
        for filepath in files_to_analyze:
            if filepath.exists():
                self.processed_files.clear()  # Reset for each entry point
                relative_path = str(filepath.relative_to(self.root_path))
                tree[relative_path] = self.analyze_file(filepath)

        return tree

    def save_to_json(self, tree: Dict, filename: str = "import_tree.json"):
        """Save the import tree to a JSON file."""
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(tree, f, indent=2, ensure_ascii=False)

        logger.info("Import tree saved to {}", filename)


def generate_and_save_import_tree() -> Dict:
    """Generate the import tree for the project."""
    framework_id = get_project_info()["data"]["frameworks"][0]["id"]
    cache_framework_dir = os.path.join(BUGSTER_DIR, framework_id)
    output_file = os.path.join(cache_framework_dir, "import_tree.json")
    generator = ImportTreeGenerator()
    tree = generator.generate_tree()
    generator.save_to_json(tree=tree, filename=output_file)
    return tree
