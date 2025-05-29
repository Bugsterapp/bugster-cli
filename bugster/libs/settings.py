from pydantic import Field
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)


class LibsSettings(BaseSettings):
    """Pydantic settings for the `libs` module."""

    @property
    def bugster_api_url(self) -> str:
        """Return the API URL based on the environment."""
        # TODO: See if we can use the environment variable to set the API URL
        return "https://api.bugster.app"

    environment: str = Field(default="localhost")
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


libs_settings = LibsSettings()
