"""
Analytics for Bugster CLI using PostHog.

This module provides usage analytics to help improve the CLI experience.

Users can opt-out in several ways:
1. During 'bugster init' setup (recommended)
2. Set environment variable: BUGSTER_ANALYTICS_DISABLED=true
3. Create opt-out file: touch ~/.bugster_no_analytics
"""

import os
import logging
import time
import functools
from typing import Optional
from datetime import datetime
from pathlib import Path
import typer

from bugster.utils.user_config import get_api_key
from bugster.utils.file import load_config
from bugster.libs.settings import libs_settings

logger = logging.getLogger(__name__)

# Privacy and opt-out configuration
OPT_OUT_ENV_VAR = "BUGSTER_ANALYTICS_DISABLED"
OPT_OUT_FILE = Path.home() / ".bugster_no_analytics"


class PostHogClient:
    """Minimal PostHog client for tracking specific business events."""
    
    def __init__(self):
        # Fast path for opted-out users - check first before any heavy initialization
        if self._should_disable_analytics():
            self.enabled = False
            self.api_key = None
            self.host = None
            self.environment = None
            return
            
        self.api_key = libs_settings.posthog_api_key
        self.host = libs_settings.posthog_host
        self.environment = libs_settings.environment.value
        
        if not self.api_key or "disabled" in self.api_key:
            logger.warning("PostHog API key not found. Event tracking will be disabled.")
            self.enabled = False
        else:
            self.enabled = True
            try:
                import posthog
                posthog.api_key = self.api_key
                posthog.host = self.host
                posthog.sync_mode = True  # Ensure events are sent before CLI exits
                posthog.debug = libs_settings.debug
                self._client = posthog
                logger.debug(f"PostHog configured for {self.environment} environment")
            except ImportError:
                logger.debug("PostHog not available, analytics disabled")
                self.enabled = False
            except Exception as e:
                logger.debug(f"Failed to setup PostHog: {e}")
                self.enabled = False
    
    @staticmethod
    def extract_organization_id(api_key: str) -> str:
        """Extracts the organization ID from an API key.
        
        Args:
            api_key: The API key in format bugster_random1orgid_random2
            
        Returns:
            The organization ID embedded in the API key
            
        Raises:
            ValueError: If the API key format is invalid
        """
        if not api_key.startswith("bugster_"):
            raise ValueError("Invalid API key format: must start with 'bugster_'")
        
        # Remove the "bugster_" prefix
        without_prefix = api_key[8:]  # "bugster_" is 8 characters
        
        if len(without_prefix) <= 32:  # Must have at least 32 chars for the two random parts
            raise ValueError("Invalid API key format: insufficient length")
        
        # Extract organization ID by removing first 16 and last 16 characters
        organization_id = without_prefix[16:-16]
        if not organization_id:
            raise ValueError("Invalid API key format: no organization ID found")
        organization_id = "org_" + organization_id
        return organization_id

    def _should_disable_analytics(self) -> bool:
        """Check if analytics should be disabled based on user preferences."""
        # Check environment variable
        if os.getenv(OPT_OUT_ENV_VAR, "").lower() in ("true", "1", "yes"):
            logger.debug("Analytics disabled via environment variable")
            return True
            
        # Check opt-out file
        if OPT_OUT_FILE.exists():
            logger.debug("Analytics disabled via opt-out file")
            return True
            
        # Check if PostHog is disabled
        if not libs_settings.posthog_enabled:
            logger.debug(f"Analytics disabled for environment: {self.environment}")
            return True
            
        return False
    
    def _track_event(self, event_name: str, user_id: str, properties: dict) -> None:
        """Internal method to track events with consistent properties."""
        if not self.enabled or self._should_disable_analytics():
            return
            
        try:
            # Add base properties to all events
            base_properties = {
                "environment": self.environment,
                "timestamp": datetime.utcnow().isoformat(),
                "source": "cli"
            }
            
            # Merge with event-specific properties
            final_properties = {**base_properties, **properties}
            
            # Track the event
            self._client.capture(
                distinct_id=user_id,
                event=event_name,
                properties=final_properties
            )
            
            logger.info(f"PostHog event tracked: {event_name} for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error tracking PostHog event '{event_name}': {e}")
    
    def track_cli_generate(self, organization_id: str, project_id: Optional[str]) -> None:
        """Track CLI generate event."""
        properties = {
            "organization_id": organization_id,
        }
        
        if project_id:
            properties["project_id"] = project_id
        
        self._track_event(
            event_name="cli_generate",
            user_id=organization_id,
            properties=properties
        )
    
    def track_cli_run(self, organization_id: str, project_id: Optional[str]) -> None:
        """Track CLI run event."""
        properties = {
            "organization_id": organization_id,
        }
        
        if project_id:
            properties["project_id"] = project_id
        
        self._track_event(
            event_name="cli_run",
            user_id=organization_id,
            properties=properties
        )
    
    def track_cli_update(self, organization_id: str, project_id: Optional[str]) -> None:
        """Track CLI update event."""
        properties = {
            "organization_id": organization_id,
        }
        
        if project_id:
            properties["project_id"] = project_id
        
        self._track_event(
            event_name="cli_update",
            user_id=organization_id,
            properties=properties
        )
    
    def track_cli_destructive(self, organization_id: str, project_id: Optional[str]) -> None:
        """Track CLI destructive event."""
        properties = {
            "organization_id": organization_id,
        }
        
        if project_id:
            properties["project_id"] = project_id
        
        self._track_event(
            event_name="cli_destructive",
            user_id=organization_id,
            properties=properties
        )

    def flush(self):
        """Ensure all events are sent before CLI exits."""
        if self.enabled and hasattr(self, '_client'):
            try:
                if hasattr(self._client, 'flush'):
                    self._client.flush()
                logger.debug("Analytics events flushed")
            except Exception as e:
                logger.debug(f"Failed to flush analytics: {e}")

    @classmethod
    def create_opt_out_file(cls):
        """Create opt-out file to disable analytics."""
        try:
            OPT_OUT_FILE.touch(exist_ok=True)
            return True
        except Exception:
            return False

    @classmethod
    def remove_opt_out_file(cls):
        """Remove opt-out file to re-enable analytics."""
        try:
            if OPT_OUT_FILE.exists():
                OPT_OUT_FILE.unlink()
            return True
        except Exception:
            return False

    @classmethod
    def is_opted_out(cls) -> bool:
        """Check if user has opted out of analytics."""
        return (
            os.getenv(OPT_OUT_ENV_VAR, "").lower() in ("true", "1", "yes")
            or OPT_OUT_FILE.exists()
        )


# Global analytics instance
_analytics_instance: Optional[PostHogClient] = None


def get_analytics() -> PostHogClient:
    """Get or create the global analytics instance."""
    global _analytics_instance
    if _analytics_instance is None:
        _analytics_instance = PostHogClient()
    return _analytics_instance


def track_command(command_name: str):
    """Decorator to track command execution time and success/failure."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            success = True
            error_type = None
            
            try:
                result = func(*args, **kwargs)
                return result
            except typer.Exit as e:
                if e.exit_code == 1:
                    success = True
                raise
            except Exception as e:
                success = False
                error_type = type(e).__name__
                raise
            finally:
                # Track specific events for generate, run, update, and destructive commands
                if command_name in ["generate", "run", "update", "destructive"]:
                    try:
                        analytics = get_analytics()
                        
                        # Get API key and extract organization ID
                        api_key = get_api_key()
                        if api_key:
                            organization_id = analytics.extract_organization_id(api_key)
                            
                            # Get project ID from config
                            project_id = None
                            try:
                                config = load_config()
                                project_id = config.project_id
                            except Exception as e:
                                logger.debug(f"Could not load project_id from config: {e}")
                            
                            # Track the specific command
                            if command_name == "generate":
                                analytics.track_cli_generate(organization_id, project_id)
                            elif command_name == "run":
                                analytics.track_cli_run(organization_id, project_id)
                            elif command_name == "update":
                                analytics.track_cli_update(organization_id, project_id)
                            elif command_name == "destructive":
                                analytics.track_cli_destructive(organization_id, project_id)
                        
                    except Exception as e:
                        logger.debug(f"Failed to track {command_name} command: {e}")
                
                # Ensure events are sent
                analytics = get_analytics()
                analytics.flush()
                
        return wrapper
    return decorator


# For backward compatibility
BugsterAnalytics = PostHogClient
posthog_client = get_analytics() 