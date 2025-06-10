#!/usr/bin/env python3

import os
import re
import sys
import subprocess
from pathlib import Path

def get_current_version():
    """Get the current version from bugster/__init__.py"""
    init_file = Path("bugster/__init__.py")
    if not init_file.exists():
        return None
    
    content = init_file.read_text()
    match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)
    return match.group(1) if match else None

def suggest_next_version(current_version):
    """Suggest the next version based on the current one"""
    if not current_version:
        return ["1.0.0", "0.1.0"]
    
    major, minor, patch = map(int, current_version.split('.'))
    return [
        f"{major+1}.0.0",  # Major bump
        f"{major}.{minor+1}.0",  # Minor bump
        f"{major}.{minor}.{patch+1}",  # Patch bump
    ]

def validate_version(version):
    """Validate version format"""
    if not re.match(r'^\d+\.\d+\.\d+$', version):
        return False
    return True

def get_environment_url(env_type):
    """Get the API URL for the given environment"""
    urls = {
        'development': 'dev.bugster.api',
        'production': 'api.bugster.app'
    }
    return urls.get(env_type)

def main():
    # Get current version
    current_version = get_current_version()
    print("\n🔍 Bugster CLI Release Manager\n")
    
    if current_version:
        print(f"Current version: {current_version}")
        suggestions = suggest_next_version(current_version)
        print("\nSuggested next versions:")
        print(f"  1. {suggestions[0]} (Major)")
        print(f"  2. {suggestions[1]} (Minor)")
        print(f"  3. {suggestions[2]} (Patch)")
        print("\nOr enter a custom version (x.y.z)")
    else:
        print("⚠️  No current version found in bugster/__init__.py")
        suggestions = ["1.0.0", "0.1.0"]
        print("\nSuggested versions:")
        print(f"  1. {suggestions[0]} (Initial release)")
        print(f"  2. {suggestions[1]} (Initial beta)")

    while True:
        version = input("\n📝 Enter version number: ").strip()
        if validate_version(version):
            break
        print("❌ Invalid version format. Please use x.y.z (e.g., 1.2.3)")

    print("\nRelease types:")
    print("  1. Development (pre-release)")
    print("  2. Production (stable release)")
    
    while True:
        type_choice = input("\n📝 Choose release type (1/2): ").strip()
        if type_choice in ['1', '2']:
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
    
    if input("\n⚠️  Proceed with release? (y/N): ").lower() != 'y':
        print("\n❌ Release cancelled")
        sys.exit(0)

    # Execute release script
    cmd = ["./scripts/release.sh", version, release_type]
    if variant:
        cmd.append(variant)
    
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Release failed: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n❌ Release cancelled")
        sys.exit(1)

if __name__ == "__main__":
    main() 