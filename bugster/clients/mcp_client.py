"""
MCP Stdio Client
"""

import asyncio
import logging
from contextlib import AsyncExitStack
from typing import Dict, List, Optional

from mcp import ClientSession, ListToolsResult, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import CallToolResult

from bugster.types import ToolRequest

logger = logging.getLogger(__name__)


class MCPStdioClient:
    def __init__(self):
        """Initialize MCP client"""
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.stdio = None
        self.write = None
        self._closed = False  # Flag to prevent double closing

    async def _cleanup(self):
        """Internal cleanup method to avoid double closing"""
        if not self._closed:
            try:
                await asyncio.wait_for(self.exit_stack.aclose(), timeout=10.0)
            except Exception as cleanup_error:
                logger.warning(f"Error during cleanup: {cleanup_error}")
            finally:
                self._closed = True
                self.session = None
                self.stdio = None
                self.write = None

    async def init_client(
        self, command: str, args: List[str], env: Optional[Dict[str, str]] = None
    ):
        """Initialize MCP client and session"""
        if not self.session:
            server_params = StdioServerParameters(command=command, args=args, env=env)

            try:
                # Add timeout for stdio_client initialization
                stdio_transport = await asyncio.wait_for(
                    self.exit_stack.enter_async_context(stdio_client(server_params)),
                    timeout=30.0,  # 30 seconds
                )
                self.stdio, self.write = stdio_transport

                # Add timeout for ClientSession initialization
                self.session = await asyncio.wait_for(
                    self.exit_stack.enter_async_context(
                        ClientSession(self.stdio, self.write)
                    ),
                    timeout=10.0,  # 10 seconds
                )

                # Add timeout for session initialization
                # fyi: if npx @playwright/mcp@latest fails, it will hang here
                await asyncio.wait_for(self.session.initialize(), timeout=30.0)

            except asyncio.TimeoutError:
                # Clean up resources and re-raise
                await self._cleanup()
                raise RuntimeError("MCP client initialization timed out")

    async def list_tools(self) -> ListToolsResult:
        """List available tools"""
        response = await self.session.list_tools()
        return response.tools

    async def execute(self, tool: ToolRequest) -> CallToolResult:
        """Execute a tool using MCP"""
        result = await self.session.call_tool(tool.name, tool.args)
        return result

    async def close(self):
        """Close MCP client"""
        if self.session and not self._closed:
            await self._cleanup()
