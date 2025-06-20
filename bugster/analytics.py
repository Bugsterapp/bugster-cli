"""
Privacy-first analytics for Bugster CLI using PostHog.

This module provides anonymous usage analytics to help improve the CLI experience.

Users can opt-out in several ways:
1. During 'bugster init' setup (recommended)
2. Set environment variable: BUGSTER_ANALYTICS_DISABLED=true
3. Create opt-out file: touch ~/.bugster_no_analytics
"""

import hashlib
import os
import platform
import sys
import time
import uuid
from pathlib import Path
from typing import Any, Dict, Optional
import typer
from loguru import logger

from bugster import __version__
from bugster.libs.settings import libs_settings

# Privacy and opt-out configuration
OPT_OUT_ENV_VAR = "BUGSTER_ANALYTICS_DISABLED"
OPT_OUT_FILE = Path.home() / ".bugster_no_analytics"

# PostHog configuration based on environment
def get_posthog_config():
    """Get PostHog configuration based on current environment."""
    return {
        "api_key": libs_settings.posthog_api_key,
        "host": libs_settings.posthog_host,
        "disabled": not libs_settings.posthog_enabled,
    }


class BugsterAnalytics:
    """Privacy-first analytics for Bugster CLI."""

    def __init__(self):
        """Initialize analytics client with privacy checks."""
        self._client = None
        self._user_id = None
        self._enabled = False
        
        # Check if analytics should be enabled
        if self._should_disable_analytics():
            return
            
        try:
            self._setup_posthog()
            self._user_id = self._generate_anonymous_user_id()
            self._enabled = True
            logger.debug("Analytics initialized successfully")
        except Exception as e:
            logger.debug(f"Failed to initialize analytics: {e}")
            self._enabled = False

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
            
        # Check if PostHog config is disabled for this environment
        config = get_posthog_config()
        if config.get("disabled", False):
            logger.debug(f"Analytics disabled for environment: {libs_settings.environment}")
            return True
            
        # Check if API key is disabled
        api_key = config.get("api_key", "")
        if not api_key or "disabled" in api_key:
            logger.debug("Analytics disabled due to missing/disabled API key")
            return True
            
        return False

    def _setup_posthog(self):
        """Setup PostHog client with environment-specific configuration."""
        try:
            import posthog
            
            config = get_posthog_config()
            api_key = config["api_key"]
            host = config["host"]
            
            posthog.api_key = api_key
            posthog.host = host
            posthog.sync_mode = True  # Ensure events are sent before CLI exits
            posthog.debug = libs_settings.debug  # Use general debug setting
            
            self._client = posthog
            logger.debug(f"PostHog configured for {libs_settings.environment} environment")
            
        except ImportError:
            logger.debug("PostHog not available, analytics disabled")
            raise
        except Exception as e:
            logger.debug(f"Failed to setup PostHog: {e}")
            raise

    def _generate_anonymous_user_id(self) -> str:
        """Generate a stable anonymous user ID based on system info."""
        try:
            # Use system-specific info for stable ID generation
            system_info = [
                platform.machine(),
                platform.system(),
                platform.node(),
                str(Path.home()),
            ]
            
            # Create hash of system info
            system_string = "|".join(system_info)
            user_hash = hashlib.sha256(system_string.encode()).hexdigest()
            
            return f"anon_{user_hash[:16]}"
            
        except Exception as e:
            logger.debug(f"Failed to generate user ID: {e}")
            return f"anon_{str(uuid.uuid4())[:16]}"

    def _get_base_properties(self) -> Dict[str, Any]:
        """Get base properties included with all events."""
        return {
            "$lib": "bugster-cli",
            "$lib_version": __version__, 
            "environment": libs_settings.environment.value,
            "platform": platform.system(),
            "platform_version": platform.version(),
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        }

    def _track_event(self, event_name: str, properties: Optional[Dict[str, Any]] = None):
        """Internal method to track events with error handling."""
        if not self._enabled or not self._client or not self._user_id:
            return
            
        try:
            event_properties = self._get_base_properties()
            if properties:
                event_properties.update(properties)
                
            self._client.capture(
                distinct_id=self._user_id,
                event=event_name,
                properties=event_properties
            )
            logger.debug(f"Tracked event: {event_name}")
            
        except Exception as e:
            logger.debug(f"Failed to track event {event_name}: {e}")

    def track_command_executed(
        self,
        command_name: str,
        start_time: float,
        success: bool,
        flags: Optional[Dict[str, Any]] = None,
        error_type: Optional[str] = None,
        message: Optional[str] = None,
    ):
        """Track CLI command execution."""
        duration = time.time() - start_time
        properties = {
            "command_name": command_name,
            "duration": duration,
            "success": success,
            "flags_count": len(flags) if flags else 0,
        }
        
        if flags:
            properties["flags_used"] = list(flags.keys())
            
        if error_type and not success:
            properties["error_type"] = error_type
        if message:
            properties["message"] = message
            
        self._track_event("command_executed", properties)
    def flush(self):
        """Ensure all events are sent before CLI exits."""
        if self._enabled and self._client:
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
_analytics_instance: Optional[BugsterAnalytics] = None


def get_analytics() -> BugsterAnalytics:
    """Get or create the global analytics instance."""
    global _analytics_instance
    if _analytics_instance is None:
        _analytics_instance = BugsterAnalytics()
    return _analytics_instance


def track_command(command_name: str):
    """Decorator to track command execution time and success/failure."""
    def decorator(func):
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
                # Extract relevant flags from kwargs
                flags = {k: v for k, v in kwargs.items() if v is not None}
                analytics = get_analytics()
                analytics.track_command_executed(
                    command_name=command_name,
                    start_time=start_time,
                    success=success,
                    flags=flags,
                    error_type=error_type,
                )
                
        return wrapper
    return decorator 