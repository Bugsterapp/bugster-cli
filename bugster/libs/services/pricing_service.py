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
        self.api_key = get_api_key()
        if not self.api_key:
            raise ValueError(
                "API key is required. Please run 'bugster login' to set up your API key."
            )

    def check_availability(self, organization_id: str) -> Dict:
        """Check pricing availability for an organization."""
        try:
            with BugsterHTTPClient() as client:
                client.set_headers({"x-api-key": self.api_key})
                response = client.get(
                    f"/api/v1/pricing/info?organization_id={organization_id}"
                )
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
                client.set_headers({"x-api-key": self.api_key})
                response = client.post(
                    "/api/v1/pricing/process",
                    json={
                        "organization_id": organization_id,
                        "action": action
                    }
                )
                return response
        except Exception as e:
            # Check if it's a quota exceeded error
            if hasattr(e, 'response') and e.response.status_code == 400:
                try:
                    error_data = e.response.json()
                    # Check for the specific quota exceeded pattern
                    if (error_data.get('error', '').endswith('quota exceeded') and 
                        error_data.get(f'exceeded_{action}_quota') == True):
                        raise QuotaExceededError(error_data['error'])
                except:
                    # Fallback if parsing fails
                    raise QuotaExceededError(f'{action.capitalize()} quota exceeded')
            
            # Re-raise other errors
            raise


def check_pricing_availability(organization_id: str) -> Dict:
    """Convenience function to check pricing availability."""
    service = PricingService()
    return service.check_availability(organization_id)

def call_pricing_endpoint(organization_id: str, action: str) -> Dict:
    """Convenience function to call the pricing endpoint."""
    service = PricingService()
    return service.track_usage(organization_id, action) 