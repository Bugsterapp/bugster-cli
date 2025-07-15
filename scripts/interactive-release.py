#!/usr/bin/env python3

import json
import re
import ssl
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

# Disable SSL certificate verification
ssl._create_default_https_context = ssl._create_unverified_context


def get_github_releases():
    """Get the latest releases from GitHub"""
    try:
        # Try to get repo info from git remote
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            check=True,
        )
        remote_url = result.stdout.strip()

        # Extract owner/repo from different URL formats
        if "github.com/" in remote_url:
            if remote_url.startswith("git@"):
                # SSH format: git@github.com:owner/repo.git
                repo_part = remote_url.split("github.com:")[1]
            else:
                # HTTPS format: https://github.com/owner/repo.git
                repo_part = remote_url.split("github.com/")[1]

            repo_path = repo_part.replace(".git", "")
        else:
            return None, None

        # Get releases from GitHub API
        api_url = f"https://api.github.com/repos/{repo_path}/releases"

        with urllib.request.urlopen(api_url) as response:
            releases = json.loads(response.read().decode())

        # Filter production and development releases
        production_releases = [r for r in releases if not r["prerelease"]]
        development_releases = [r for r in releases if r["prerelease"]]

        latest_production = production_releases[0] if production_releases else None
        latest_development = development_releases[0] if development_releases else None

        return latest_production, latest_development

    except (
        subprocess.CalledProcessError,
        urllib.error.URLError,
        json.JSONDecodeError,
        IndexError,
    ) as e:
        print(f"⚠️  Could not fetch GitHub releases: {e}")
        return None, None


def get_current_version_fallback():
    """Fallback: Get the current version from bugster/__init__.py"""
    init_file = Path("bugster/__init__.py")
    if not init_file.exists():
        return None

    content = init_file.read_text()
    match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)
    return match.group(1) if match else None


def parse_version(version_string):
    """Parse version string, removing 'v' prefix if present"""
    if version_string.startswith("v"):
        return version_string[1:]
    return version_string


def suggest_next_version(current_version):
    """Suggest the next version based on the current one"""
    if not current_version:
        return ["1.0.0", "0.1.0"]

    # Handle version with prerelease suffix (e.g., "1.0.0-beta.1")
    base_version = current_version.split("-")[0]

    try:
        major, minor, patch = map(int, base_version.split("."))
        return [
            f"{major + 1}.0.0",  # Major bump
            f"{major}.{minor + 1}.0",  # Minor bump
            f"{major}.{minor}.{patch + 1}",  # Patch bump
        ]
    except ValueError:
        return ["1.0.0", "0.1.0"]


def validate_version(version):
    """Validate version format"""
    if not re.match(r"^\d+\.\d+\.\d+$", version):
        return False
    return True


def get_environment_url(env_type):
    """Get the API URL for the given environment"""
    urls = {"development": "dev.bugster.app", "production": "api.bugster.app"}
    return urls.get(env_type)


def main():
    # Get current versions from GitHub
    latest_production, latest_development = get_github_releases()

    print("\n🔍 Bugster CLI Release Manager\n")

    # Show current release information
    current_version = None
    if latest_production:
        current_version = parse_version(latest_production["tag_name"])
        print(
            f"📦 Latest Production: {latest_production['tag_name']} ({latest_production['created_at'][:10]})"
        )

    if latest_development:
        dev_version = parse_version(latest_development["tag_name"])
        print(
            f"🧪 Latest Development: {latest_development['tag_name']} ({latest_development['created_at'][:10]})"
        )

    # Fallback to local version if GitHub not available
    if not current_version:
        current_version = get_current_version_fallback()
        if current_version:
            print(f"📄 Local version (from __init__.py): {current_version}")
        else:
            print("⚠️  No version information found")

    if current_version:
        suggestions = suggest_next_version(current_version)
        print(f"\n🔄 Based on current version: {current_version}")
        print("\nChoose version bump:")
        print(f"  1. {suggestions[0]} (Major - breaking changes)")
        print(f"  2. {suggestions[1]} (Minor - new features)")
        print(f"  3. {suggestions[2]} (Patch - bug fixes)")
        print("  4. Custom version")

        while True:
            version_choice = input("\n📝 Choose version bump (1/2/3/4): ").strip()
            if version_choice in ["1", "2", "3", "4"]:
                break
            print("❌ Invalid choice. Please enter 1, 2, 3, or 4")

        if version_choice == "4":
            while True:
                version = input("\n📝 Enter custom version (x.y.z): ").strip()
                if validate_version(version):
                    break
                print("❌ Invalid version format. Please use x.y.z (e.g., 1.2.3)")
        else:
            version = suggestions[int(version_choice) - 1]
            print(f"\n✅ Selected version: {version}")
    else:
        suggestions = ["1.0.0", "0.1.0"]
        print("\nNo current version found. Choose initial version:")
        print(f"  1. {suggestions[0]} (Stable initial release)")
        print(f"  2. {suggestions[1]} (Beta initial release)")
        print("  3. Custom version")

        while True:
            version_choice = input("\n📝 Choose initial version (1/2/3): ").strip()
            if version_choice in ["1", "2", "3"]:
                break
            print("❌ Invalid choice. Please enter 1, 2, or 3")

        if version_choice == "3":
            while True:
                version = input("\n📝 Enter custom version (x.y.z): ").strip()
                if validate_version(version):
                    break
                print("❌ Invalid version format. Please use x.y.z (e.g., 1.2.3)")
        else:
            version = suggestions[int(version_choice) - 1]
            print(f"\n✅ Selected version: {version}")

    print("\nRelease types:")
    print("  1. Development (pre-release)")
    print("  2. Production (stable release)")

    while True:
        type_choice = input("\n📝 Choose release type (1/2): ").strip()
        if type_choice in ["1", "2"]:
            break
        print("❌ Invalid choice. Please enter 1 or 2")

    release_type = "development" if type_choice == "1" else "production"

    variant = None
    if release_type == "development":
        print("\nPre-release variant:")
        print("  1. Beta (default)")
        print("  2. Alpha")

        variant_choice = input("\n📝 Choose variant (1/2) [1]: ").strip() or "1"
        variant = "beta" if variant_choice == "1" else "alpha"

    # Show summary
    print("\n📋 Release Summary:")
    print(f"  Version: {version}")
    print(f"  Type: {release_type}")
    if variant:
        print(f"  Variant: {variant}")
    print(f"  API URL: {get_environment_url(release_type)}")

    # Show what will happen
    tag_name = f"v{version}"
    if release_type == "development" and variant:
        tag_name = f"v{version}-{variant}.1"

    print(f"  Git tag: {tag_name}")
    print("  GitHub Release: Will be created automatically")
    print(f"  Version in code: Will be updated to '{version}' automatically")

    if input("\n⚠️  Proceed with release? (y/N): ").lower() != "y":
        print("\n❌ Release cancelled")
        sys.exit(0)

    # Execute release script
    cmd = ["./scripts/release.sh", version, release_type]
    if variant:
        cmd.append(variant)

    try:
        print(f"\n🚀 Executing: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)
        print("\n✅ Release initiated! Check GitHub Actions for build progress.")
        print(f"   https://github.com/{get_repo_path()}/actions")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Release failed: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n❌ Release cancelled")
        sys.exit(1)


def get_repo_path():
    """Get the GitHub repository path (owner/repo)"""
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            check=True,
        )
        remote_url = result.stdout.strip()

        if "github.com/" in remote_url:
            if remote_url.startswith("git@"):
                repo_part = remote_url.split("github.com:")[1]
            else:
                repo_part = remote_url.split("github.com/")[1]

            return repo_part.replace(".git", "")
    except subprocess.CalledProcessError:
        pass

    return "your-org/your-repo"


if __name__ == "__main__":
    main()
