import logging
from typing import Any, Dict, Optional

import requests

from bugster.libs.settings import libs_settings

logger = logging.getLogger(__name__)


class HTTPClient:
    """HTTP client for making API requests."""

    def __init__(self, base_url: str, timeout: int = 60):
        """Initialize the HTTP client."""
        self.base_url = base_url
        self.timeout = timeout
        self.session = requests.Session()

    def put(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> requests.Response:
        """Make a PUT request."""
        return self._make_request("PUT", endpoint, data=data, json=json, **kwargs)

    def get(
        self, endpoint: str, params: Optional[Dict[str, Any]] = None, **kwargs
    ) -> requests.Response:
        """Make a GET request."""
        return self._make_request("GET", endpoint, params=params, **kwargs)

    def post(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> requests.Response:
        """Make a POST request."""
        return self._make_request("POST", endpoint, data=data, json=json, **kwargs)

    def delete(self, endpoint: str, **kwargs) -> requests.Response:
        """Make a DELETE request."""
        return self._make_request("DELETE", endpoint, **kwargs)

    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make an HTTP request."""
        url = f"{self.base_url}{endpoint}"
        response = None
        data = None

        if "timeout" not in kwargs:
            kwargs["timeout"] = self.timeout

        try:
            logger.info("Making {} request to {}", method, url)
            response = self.session.request(method, url, **kwargs)
            logger.info("Response status code: {}", response.status_code)
            response.raise_for_status()
            data = response.json()
            logger.info("Received data: {}", data)
            return data
        except requests.exceptions.HTTPError as err:
            if response and hasattr(response, "text"):
                logger.error(
                    "HTTP error for {} {}: {} - {}", method, url, err, response.text
                )
            else:
                logger.error("HTTP error for {} {}: {}", method, url, err)
            raise
        except Exception as err:
            logger.error("Error making {} request to {}: {}", method, url, err)
            raise

    def set_auth_header(self, token: str, auth_type: str = "Bearer"):
        """Set authentication header for all requests."""
        self.session.headers.update({"Authorization": f"{auth_type} {token}"})

    def set_headers(self, headers: Dict[str, str]):
        """Set custom headers for all requests."""
        self.session.headers.update(headers)

    def remove_header(self, header_name: str):
        """Remove a header from all requests."""
        self.session.headers.pop(header_name, None)

    def close(self):
        """Close the session."""
        self.session.close()

    def __enter__(self):
        """Enter the context manager."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context manager."""
        self.close()


class BugsterHTTPClient(HTTPClient):
    """HTTP client for the Bugster API."""

    def __init__(self):
        """Initialize the HTTP client."""
        super().__init__(base_url=libs_settings.bugster_api_url)
