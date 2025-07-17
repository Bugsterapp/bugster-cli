"""Pricing service for Bugster CLI to track test and destructive usage."""

import logging
from typing import Dict

from bugster.clients.http_client import BugsterHTTPClient
from bugster.utils.user_config import get_api_key

logger = logging.getLogger(__name__)


class QuotaExceededError(Exception):
    """Raised when pricing quota is exceeded."""
    pass


class PricingService:
    """Service for tracking test and destructive usage via pricing endpoint."""

    def __init__(self):
        from bugster.libs.settings import libs_settings
        # Hardcode dev.bugster.app for testing
        self.base_url = "https://dev.bugster.app"
        self.api_key = get_api_key()
        if not self.api_key:
            raise ValueError(
                "API key is required. Please run 'bugster login' to set up your API key."
            )

    def check_availability(self, organization_id: str) -> Dict:
        """Check pricing availability for an organization."""
        try:
            with BugsterHTTPClient() as client:
                client.set_headers({"X-API-Key": self.api_key})
                endpoint = f"/pricing/info?organization_id={organization_id}"
                response = client.get(endpoint)
                return response
        except Exception as e:
            # If organization doesn't exist, it's OK (will be created on first use)
            if hasattr(e, 'response') and e.response.status_code == 404:
                return {"available": True, "message": "Organization will be created on first use"}
            raise

    def track_usage(self, organization_id: str, action: str) -> Dict:
        """Track usage for a specific action (test or destructive)."""
        try:
            with BugsterHTTPClient() as client:
                client.set_headers({"X-API-Key": self.api_key})
                endpoint = "/pricing/process"
                payload = {
                    "organization_id": organization_id,
                    "action": action
                }
                logger.info(f"Calling pricing endpoint: {self.base_url}{endpoint}")
                response = client.post(endpoint, json=payload)
                return response
        except Exception as e:
            # Check if it's a quota exceeded error
            # The error message from BugsterHTTPError contains the response text
            error_message = str(e)
            logger.info(f"Pricing endpoint error: {error_message}")
            
            if "400" in error_message and "quota exceeded" in error_message.lower():
                # Extract the specific quota exceeded message if possible
                if f"exceeded_{action}_quota" in error_message:
                    quota_error = f"{action.capitalize()} quota exceeded"
                else:
                    quota_error = f"{action.capitalize()} quota exceeded"
                logger.warning(f"Quota exceeded detected: {quota_error}")
                raise QuotaExceededError(quota_error)
            
            # Re-raise other errors
            logger.error(f"Non-quota pricing error: {error_message}")
            raise


def check_pricing_availability(organization_id: str) -> Dict:
    """Convenience function to check pricing availability."""
    service = PricingService()
    return service.check_availability(organization_id)

def call_pricing_endpoint(organization_id: str, action: str) -> Dict:
    """Convenience function to call the pricing endpoint."""
    service = PricingService()
    return service.track_usage(organization_id, action) 