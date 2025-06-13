# bugster/libs/settings.py
from enum import Enum

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(str, Enum):
    LOCAL = "local"
    DEVELOPMENT = "development"
    PRODUCTION = "production"


class LibsSettings(BaseSettings):
    """Pydantic settings for the `libs` module."""

    environment: Environment = Field(default=Environment.PRODUCTION)

    # URLs por ambiente
    _api_urls = {
        Environment.LOCAL: "http://localhost:8000",
        Environment.DEVELOPMENT: "https://dev.bugster.app",
        Environment.PRODUCTION: "https://api.bugster.app",
    }

    # WebSocket URLs por ambiente
    _ws_urls = {
        Environment.LOCAL: "ws://localhost:8765",
        Environment.DEVELOPMENT: "wss://websocket.bugster.app/prod/",
        Environment.PRODUCTION: "wss://websocket.bugster.app/prod/",
    }

    @property
    def bugster_api_url(self) -> str:
        """Return the API URL based on the environment."""
        return self._api_urls[self.environment]

    @property
    def websocket_url(self) -> str:
        """Return the WebSocket URL based on the environment."""
        return self._ws_urls[self.environment]

    # Configuraciones específicas por ambiente
    debug: bool = Field(default=False)
    log_level: str = Field(default="INFO")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Auto-configurar según el ambiente
        if self.environment == Environment.LOCAL:
            self.debug = True
            self.log_level = "DEBUG"
        elif self.environment == Environment.DEVELOPMENT:
            self.debug = True
            self.log_level = "INFO"
        else:  # PRODUCTION
            self.debug = False
            self.log_level = "WARNING"

    model_config = SettingsConfigDict(
        env_file=".env", extra="ignore", env_prefix="BUGSTER_"
    )


libs_settings = LibsSettings()
