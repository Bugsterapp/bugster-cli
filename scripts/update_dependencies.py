#!/usr/bin/env python3
"""
Update setup.py install_requires with dependencies from requirements.txt
Usage: python scripts/update_dependencies.py

This script allows you to:
1. Update setup.py with all dependencies from requirements.txt
2. Update setup.py with only core dependencies (excluding dev dependencies)
3. Specify which dependencies to include or exclude
"""

import argparse
import os
import re
import subprocess
import sys


def read_requirements(file_path="requirements.txt"):
    """Read and parse requirements file"""
    requirements = []
    with open(file_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("-e "):
                continue
            # Handle requirements with version specs
            requirements.append(line)
    return requirements


def update_setup_py(requirements, debug=False):
    """Update setup.py with requirements"""
    try:
        # Read the setup.py file as a single string
        with open("setup.py", encoding="utf-8") as f:
            content = f.read()

        # Define a pattern to match the entire install_requires section
        pattern = r"(install_requires\s*=\s*\[)([^\]]*?)(\s*\])"
        match = re.search(pattern, content, re.DOTALL)

        if not match:
            print("Could not find install_requires section in setup.py")
            if debug:
                print("Content of setup.py:")
                print(content[:500] + "..." if len(content) > 500 else content)
            return False

        # Format the new requirements
        formatted_reqs = []
        for req in requirements:
            formatted_reqs.append(f'        "{req}",')

        new_requires = "\n" + "\n".join(formatted_reqs) + "\n    "

        # Replace the content between the brackets
        new_content = content[: match.start(2)] + new_requires + content[match.end(2) :]

        # Write the updated content back to setup.py
        with open("setup.py", "w", encoding="utf-8") as f:
            f.write(new_content)

        print(f"Updated setup.py with {len(requirements)} dependencies")
        return True

    except Exception as e:
        print(f"Error updating setup.py: {str(e)}")
        return False


def filter_requirements(requirements, exclude=None, include=None):
    """Filter requirements based on include/exclude lists"""
    if exclude is None:
        exclude = []
    if include is None:
        include = []

    if include:
        # If include is specified, only keep those packages
        filtered = []
        for req in requirements:
            package_name = (
                req.split("==")[0].split(">=")[0].split(">")[0].split("<")[0].strip()
            )
            if package_name in include:
                filtered.append(req)
        return filtered
    elif exclude:
        # If exclude is specified, remove those packages
        filtered = []
        for req in requirements:
            package_name = (
                req.split("==")[0].split(">=")[0].split(">")[0].split("<")[0].strip()
            )
            if package_name not in exclude:
                filtered.append(req)
        return filtered

    # If neither include nor exclude is specified, return all requirements
    return requirements


def get_package_names(requirements):
    """Extract package names from requirements"""
    package_names = set()
    for req in requirements:
        package_name = (
            req.split("==")[0].split(">=")[0].split(">")[0].split("<")[0].strip()
        )
        package_names.add(package_name)
    return package_names


def install_missing_packages(include_packages, available_packages, debug=False):
    """Install packages that are needed but not present in requirements.txt"""
    missing_packages = [
        pkg
        for pkg in include_packages
        if pkg not in get_package_names(available_packages)
    ]

    if not missing_packages:
        return available_packages

    print(
        f"Installing {len(missing_packages)} missing packages: {', '.join(missing_packages)}"
    )

    for package in missing_packages:
        try:
            print(f"Installing {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        except subprocess.CalledProcessError as e:
            print(f"Failed to install {package}: {str(e)}")

    # Update requirements.txt with newly installed packages
    subprocess.check_call(
        [sys.executable, "-m", "pip", "freeze"],
        stdout=open("requirements.txt", "w", encoding="utf-8"),
    )

    # Read updated requirements
    return read_requirements()


def parse_args():
    parser = argparse.ArgumentParser(
        description="Update setup.py with dependencies from requirements.txt"
    )
    parser.add_argument(
        "--req-file", default="requirements.txt", help="Path to requirements file"
    )
    parser.add_argument("--exclude", nargs="+", help="List of packages to exclude")
    parser.add_argument(
        "--include",
        nargs="+",
        help="List of packages to include (only these will be added)",
    )
    parser.add_argument(
        "--dev",
        action="store_true",
        help="Include dev dependencies (defaults to False)",
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug output")
    parser.add_argument(
        "--no-install", action="store_true", help="Don't install missing packages"
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    if not os.path.exists(args.req_file):
        print(f"Error: {args.req_file} not found")
        exit(1)

    if not os.path.exists("setup.py"):
        print("Error: setup.py not found")
        exit(1)

    # Default development dependencies to exclude if --dev is not specified
    dev_dependencies = [
        "pytest",
        "black",
        "flake8",
        "mypy",
        "isort",
        "coverage",
        "pylint",
        "autopep8",
        "pycodestyle",
        "pyflakes",
        "rope",
        "setuptools",
        "wheel",
        "pip",
        "build",
        "twine",
        "pyinstaller",
    ]

    # Read requirements from file
    all_requirements = read_requirements(args.req_file)
    if not all_requirements:
        print(f"No requirements found in {args.req_file}")
        exit(1)

    print(f"Found {len(all_requirements)} total dependencies in {args.req_file}")

    # Install missing packages if needed
    if args.include and not args.no_install:
        all_requirements = install_missing_packages(
            args.include, all_requirements, args.debug
        )

    # Filter requirements
    if args.include:
        requirements = filter_requirements(all_requirements, include=args.include)
        print(f"Including only {len(requirements)} specified dependencies")
    elif args.exclude:
        requirements = filter_requirements(all_requirements, exclude=args.exclude)
        print(f"Excluding {len(args.exclude)} specified dependencies")
    elif not args.dev:
        # By default, exclude dev dependencies
        requirements = filter_requirements(all_requirements, exclude=dev_dependencies)
        print(f"Excluding {len(dev_dependencies)} development dependencies")
    else:
        # Include all dependencies
        requirements = all_requirements
        print("Including all dependencies")

    # Debug
    if args.debug:
        print("Requirements to be added:")
        for req in requirements:
            print(f"  - {req}")

    # Update setup.py
    success = update_setup_py(requirements, args.debug)

    if success:
        print("Successfully updated setup.py")
    else:
        print("Failed to update setup.py")
        exit(1)
