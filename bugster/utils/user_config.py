"""User configuration utilities for Bugster CLI."""

import json
import os
from pathlib import Path
from typing import Optional

from loguru import logger

CONFIG_FILE = Path.home() / ".bugsterrc"
ENV_API_KEY = "BUGSTER_CLI_API_KEY"


def get_user_config_file() -> Path:
    """Get the path to the config file."""
    return Path(CONFIG_FILE)


def load_user_config() -> dict:
    """Load configuration from file."""
    config_file = get_user_config_file()

    if not config_file.exists():
        return {}

    try:
        with open(config_file) as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}


def save_user_config(config: dict) -> None:
    """Save configuration to file."""
    config_file = get_user_config_file()

    # Create parent directories if they don't exist
    config_file.parent.mkdir(parents=True, exist_ok=True)

    with open(config_file, "w") as f:
        json.dump(config, f, indent=2)


def get_api_key() -> Optional[str]:
    """Get API key from environment or config file."""
    # First check environment variable
    api_key = os.getenv(ENV_API_KEY)

    if api_key:
        logger.info("API key found in environment variable")
        return api_key

    # Then check config file
    config = load_user_config()
    logger.info("API key found in config file")
    return config.get("apiKey")


def save_api_key(api_key: str) -> None:
    """Save API key to config file."""
    config = load_user_config()
    config["apiKey"] = api_key
    save_user_config(config)
