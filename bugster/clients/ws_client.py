"""
WebSocket client implementation using websockets library
"""

import json
import ssl
import asyncio
from typing import Dict, Any, Optional
import websockets
from websockets.asyncio.client import ClientConnection
from bugster.utils.user_config import get_api_key


class WebSocketClient:
    def __init__(self):
        """Initialize WebSocket client"""
        self.ws: Optional[ClientConnection] = None
        self.url = "wss://websocket.bugster.app/prod/"
        # self.url = "ws://localhost:8765"
        self.connected = False

        # Create SSL context that ignores certificate verification
        self.ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE

    async def connect(self):
        """Connect to WebSocket server"""
        # Get API key from config
        api_key = get_api_key()
        if not api_key:
            raise RuntimeError(
                "API key not found. Please run 'bugster login' to set up your API key."
            )

        # Add API key to headers
        additional_headers = {"X-API-Key": api_key}

        if self.url.startswith("wss"):
            self.ws = await websockets.connect(
                self.url,
                ssl=self.ssl_context,
                open_timeout=30,
                additional_headers=additional_headers,
            )
        else:
            self.ws = await websockets.connect(
                self.url,
                open_timeout=30,
                additional_headers=additional_headers,
            )
        self.connected = True

    async def close(self):
        """Close WebSocket connection"""
        if self.ws:
            await self.ws.close()
            self.connected = False
            self.ws = None

    async def send(self, data: Dict[str, Any]):
        """Send data to WebSocket server"""
        if not self.ws:
            raise RuntimeError("WebSocket not connected")
        await self.ws.send(json.dumps(data))

    async def receive(self, timeout: Optional[float] = None) -> Dict[str, Any]:
        """Receive data from WebSocket server with optional timeout"""
        if not self.ws:
            raise RuntimeError("WebSocket not connected")

        if timeout:
            try:
                message = await asyncio.wait_for(self.ws.recv(), timeout=timeout)
            except asyncio.TimeoutError:
                raise asyncio.TimeoutError(
                    f"No message received within {timeout} seconds"
                )
        else:
            message = await self.ws.recv()

        return json.loads(message)
