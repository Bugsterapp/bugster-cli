#!/usr/bin/env python3
"""Script to inject real configuration values into the settings file before building.

This replaces placeholder values (API keys, URLs) with real values from environment variables.
"""

import argparse
import os
import sys
from pathlib import Path


def inject_configuration(settings_file_path: str, environment: str) -> None:
    """Replace placeholder values with real configuration from environment variables.

    Args:
        settings_file_path: Path to the settings.py file
        environment: Target environment (development/production)
    """
    # Validate environment
    if environment not in ["development", "production"]:
        print(
            f"Error: Invalid environment '{environment}'. Must be 'development' or 'production'"
        )
        sys.exit(1)

    # Define environment-specific URLs
    url_mappings = {
        "development": {
            "api_url": "https://dev.bugster.app",
            "websocket_url": "wss://websocket.bugster.app/development/",
        },
        "production": {
            "api_url": "https://api.bugster.app",
            "websocket_url": "wss://websocket.bugster.app/production/",
        },
    }

    # Get environment variables
    posthog_api_key = os.getenv("POSTHOG_API_KEY")
    if not posthog_api_key:
        print("Error: POSTHOG_API_KEY environment variable not set")
        sys.exit(1)

    # Read the settings file
    settings_path = Path(settings_file_path)
    if not settings_path.exists():
        print(f"Error: Settings file not found at {settings_file_path}")
        sys.exit(1)

    try:
        with open(settings_path, encoding="utf-8") as f:
            content = f.read()

        # Define all replacements
        replacements = [
            ('"phc_api_key_placeholder"', f'"{posthog_api_key}"'),
            ('"api_url_placeholder"', f'"{url_mappings[environment]["api_url"]}"'),
            (
                '"websocket_url_placeholder"',
                f'"{url_mappings[environment]["websocket_url"]}"',
            ),
        ]

        replacements_made = []

        # Perform all replacements
        for placeholder, real_value in replacements:
            if placeholder in content:
                content = content.replace(placeholder, real_value)
                replacements_made.append(placeholder.strip('"'))
            else:
                print(
                    f"Warning: Placeholder {placeholder} not found in {settings_file_path}"
                )

        # Write back the updated content
        with open(settings_path, "w", encoding="utf-8") as f:
            f.write(content)

        print(f"Successfully injected configuration for {environment} environment")
        print(f"   Replaced placeholders: {', '.join(replacements_made)}")
        print(f"   File: {settings_file_path}")

    except Exception as e:
        print(f"Error processing settings file: {e}")
        sys.exit(1)


def main():
    """Main function to handle command line arguments and execute configuration injection."""
    parser = argparse.ArgumentParser(
        description="Inject real configuration values into Bugster CLI settings before build"
    )
    parser.add_argument(
        "-env",
        "--environment",
        required=True,
        choices=["development", "production"],
        help="Target environment for the build",
    )
    parser.add_argument(
        "--settings-file",
        default="bugster/libs/settings.py",
        help="Path to the settings file (default: bugster/libs/settings.py)",
    )

    args = parser.parse_args()

    print(f"Injecting configuration for {args.environment} environment...")
    inject_configuration(args.settings_file, args.environment)
    print("Configuration injection completed successfully")


if __name__ == "__main__":
    main()
