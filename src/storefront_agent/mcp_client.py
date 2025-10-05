"""MCP (Model Context Protocol) client for server communication."""

import json
import asyncio
import uuid
from typing import Dict, Any, Optional, List, Callable
import websockets
import httpx
from loguru import logger
from .config import config


class MCPClient:
    """Client for communicating with MCP servers."""
    
    def __init__(self, server_url: Optional[str] = None):
        """
        Initialize the MCP client.
        
        Args:
            server_url: Optional MCP server URL override
        """
        self.server_url = server_url or config.mcp.server_url
        self.timeout = config.mcp.timeout
        self.websocket = None
        self.request_id = 0
        self.pending_requests: Dict[str, asyncio.Future] = {}
        
    async def connect(self) -> bool:
        """
        Connect to the MCP server.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            logger.info(f"Connecting to MCP server at {self.server_url}")
            
            if self.server_url.startswith("ws://") or self.server_url.startswith("wss://"):
                self.websocket = await websockets.connect(
                    self.server_url,
                    timeout=self.timeout
                )
                logger.info("WebSocket connection established")
                
                # Start listening for responses
                asyncio.create_task(self._listen_for_responses())
                
            elif self.server_url.startswith("http://") or self.server_url.startswith("https://"):
                # HTTP-based MCP server
                logger.info("Using HTTP-based MCP server")
                from .http_mcp_client import HTTPMCPClient
                self.http_client = HTTPMCPClient(self.server_url, self.timeout)
                await self.http_client.connect()
                
            else:
                raise ValueError(f"Unsupported server URL protocol: {self.server_url}")
                
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to MCP server: {str(e)}")
            return False
    
    async def disconnect(self):
        """Disconnect from the MCP server."""
        try:
            if self.websocket:
                await self.websocket.close()
                logger.info("Disconnected from MCP server")
        except Exception as e:
            logger.error(f"Error disconnecting from MCP server: {str(e)}")
    
    async def _listen_for_responses(self):
        """Listen for responses from the MCP server (WebSocket only)."""
        try:
            async for message in self.websocket:
                try:
                    response = json.loads(message)
                    await self._handle_response(response)
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse response JSON: {str(e)}")
                except Exception as e:
                    logger.error(f"Error handling response: {str(e)}")
        except websockets.exceptions.ConnectionClosed:
            logger.info("WebSocket connection closed")
        except Exception as e:
            logger.error(f"Error in response listener: {str(e)}")
    
    async def _handle_response(self, response: Dict[str, Any]):
        """Handle incoming response from MCP server."""
        try:
            request_id = response.get("id")
            if request_id and request_id in self.pending_requests:
                future = self.pending_requests.pop(request_id)
                if not future.done():
                    future.set_result(response)
            else:
                logger.warning(f"Received response for unknown request ID: {request_id}")
        except Exception as e:
            logger.error(f"Error handling response: {str(e)}")
    
    async def _send_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send a request to the MCP server and wait for response.
        
        Args:
            request: The MCP request to send
            
        Returns:
            The response from the MCP server
        """
        try:
            # Generate unique request ID
            request_id = str(uuid.uuid4())
            request["id"] = request_id
            
            # Create future for response
            future = asyncio.Future()
            self.pending_requests[request_id] = future
            
            # Send request
            if self.websocket:
                await self.websocket.send(json.dumps(request))
                logger.info(f"Sent MCP request with ID: {request_id}")
            else:
                # HTTP-based request
                return await self._send_http_request(request)
            
            # Wait for response with timeout
            try:
                response = await asyncio.wait_for(future, timeout=self.timeout)
                return response
            except asyncio.TimeoutError:
                self.pending_requests.pop(request_id, None)
                raise MCPError(f"Request timeout after {self.timeout} seconds")
                
        except Exception as e:
            logger.error(f"Error sending MCP request: {str(e)}")
            raise MCPError(f"Failed to send request: {str(e)}")
    
    async def _send_http_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Send HTTP-based MCP request."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.server_url,
                    json=request,
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error sending HTTP MCP request: {str(e)}")
            raise MCPError(f"HTTP request failed: {str(e)}")
    
    async def call_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Call a specific MCP tool.
        
        Args:
            tool_name: Name of the tool to call
            parameters: Parameters for the tool
            timeout: Optional timeout override
            
        Returns:
            Response from the MCP server
        """
        try:
            # Use HTTP client if available
            if hasattr(self, 'http_client') and self.http_client:
                return await self.http_client.call_tool(tool_name, parameters, timeout)
            
            # Fallback to WebSocket/JSON-RPC
            request = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": parameters
                }
            }
            
            logger.info(f"Calling MCP tool: {tool_name}")
            response = await self._send_request(request)
            
            if "error" in response:
                raise MCPError(f"Tool call failed: {response['error']}")
            
            return response.get("result", {})
            
        except Exception as e:
            logger.error(f"Error calling MCP tool {tool_name}: {str(e)}")
            raise MCPError(f"Failed to call tool {tool_name}: {str(e)}")
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """
        List available MCP tools.
        
        Returns:
            List of available tools
        """
        try:
            # Use HTTP client if available
            if hasattr(self, 'http_client') and self.http_client:
                return await self.http_client.list_tools()
            
            # Fallback to WebSocket/JSON-RPC
            request = {
                "jsonrpc": "2.0",
                "method": "tools/list"
            }
            
            logger.info("Listing available MCP tools")
            response = await self._send_request(request)
            
            if "error" in response:
                raise MCPError(f"Failed to list tools: {response['error']}")
            
            return response.get("result", {}).get("tools", [])
            
        except Exception as e:
            logger.error(f"Error listing MCP tools: {str(e)}")
            raise MCPError(f"Failed to list tools: {str(e)}")
    
    async def get_resources(self) -> List[Dict[str, Any]]:
        """
        Get available MCP resources.
        
        Returns:
            List of available resources
        """
        try:
            request = {
                "jsonrpc": "2.0",
                "method": "resources/list"
            }
            
            logger.info("Getting available MCP resources")
            response = await self._send_request(request)
            
            if "error" in response:
                raise MCPError(f"Failed to get resources: {response['error']}")
            
            return response.get("result", {}).get("resources", [])
            
        except Exception as e:
            logger.error(f"Error getting MCP resources: {str(e)}")
            raise MCPError(f"Failed to get resources: {str(e)}")
    
    async def read_resource(
        self,
        resource_uri: str,
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Read a specific MCP resource.
        
        Args:
            resource_uri: URI of the resource to read
            timeout: Optional timeout override
            
        Returns:
            Resource content
        """
        try:
            request = {
                "jsonrpc": "2.0",
                "method": "resources/read",
                "params": {
                    "uri": resource_uri
                }
            }
            
            logger.info(f"Reading MCP resource: {resource_uri}")
            response = await self._send_request(request)
            
            if "error" in response:
                raise MCPError(f"Failed to read resource: {response['error']}")
            
            return response.get("result", {})
            
        except Exception as e:
            logger.error(f"Error reading MCP resource {resource_uri}: {str(e)}")
            raise MCPError(f"Failed to read resource {resource_uri}: {str(e)}")
    
    async def execute_operation(
        self,
        operation: str,
        parameters: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a generic MCP operation.
        
        Args:
            operation: The operation to execute
            parameters: Parameters for the operation
            context: Optional context information
            
        Returns:
            Operation result
        """
        try:
            request = {
                "jsonrpc": "2.0",
                "method": operation,
                "params": {
                    "parameters": parameters,
                    "context": context or {}
                }
            }
            
            logger.info(f"Executing MCP operation: {operation}")
            response = await self._send_request(request)
            
            if "error" in response:
                raise MCPError(f"Operation failed: {response['error']}")
            
            return response.get("result", {})
            
        except Exception as e:
            logger.error(f"Error executing MCP operation {operation}: {str(e)}")
            raise MCPError(f"Failed to execute operation {operation}: {str(e)}")


class MCPError(Exception):
    """Custom exception for MCP client errors."""
    pass
