"""HTTP-based MCP client for FastAPI MCP servers."""

import json
import asyncio
from typing import Dict, Any, Optional, List
import httpx
from loguru import logger


class HTTPMCPClient:
    """HTTP client for communicating with FastAPI-based MCP servers."""
    
    def __init__(self, base_url: str, timeout: int = 30):
        """
        Initialize the HTTP MCP client.
        
        Args:
            base_url: Base URL of the MCP server (e.g., https://storefront-mcp-server.azurecontainerapps.io)
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.client = None
        
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
    
    async def connect(self) -> bool:
        """
        Connect to the MCP server (HTTP client initialization).
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            logger.info(f"Connecting to HTTP MCP server at {self.base_url}")
            
            self.client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
                headers={"Content-Type": "application/json"}
            )
            
            # Test the connection by getting available tools
            response = await self.client.get("/api/tools")
            if response.status_code == 200:
                logger.info("HTTP MCP server connection successful")
                return True
            else:
                logger.error(f"HTTP MCP server connection failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to connect to HTTP MCP server: {str(e)}")
            return False
    
    async def disconnect(self):
        """Disconnect from the MCP server."""
        try:
            if self.client:
                await self.client.aclose()
                logger.info("Disconnected from HTTP MCP server")
        except Exception as e:
            logger.error(f"Error disconnecting from HTTP MCP server: {str(e)}")
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """
        List available MCP tools.
        
        Returns:
            List of available tools
        """
        try:
            logger.info("Listing available MCP tools")
            response = await self.client.get("/api/tools")
            response.raise_for_status()
            
            tools = response.json()
            logger.info(f"Found {len(tools)} available tools")
            return tools
            
        except Exception as e:
            logger.error(f"Error listing MCP tools: {str(e)}")
            raise HTTPMCPError(f"Failed to list tools: {str(e)}")
    
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
            logger.info(f"Calling MCP tool: {tool_name}")
            
            # Build the request URL and parameters
            url = f"/api/tools/{tool_name}"
            
            # For GET requests with query parameters
            if tool_name in ["search_products", "get_products_by_category"]:
                response = await self.client.get(url, params=parameters)
            else:
                # For POST requests with JSON body
                response = await self.client.post(url, json=parameters)
            
            response.raise_for_status()
            result = response.json()
            
            logger.info(f"Successfully called tool {tool_name}")
            return result
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error calling tool {tool_name}: {e.response.status_code} - {e.response.text}")
            raise HTTPMCPError(f"Tool call failed: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            logger.error(f"Error calling MCP tool {tool_name}: {str(e)}")
            raise HTTPMCPError(f"Failed to call tool {tool_name}: {str(e)}")
    
    async def get_tool_info(self, tool_name: str) -> Dict[str, Any]:
        """
        Get information about a specific tool.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Tool information
        """
        try:
            logger.info(f"Getting info for tool: {tool_name}")
            response = await self.client.get(f"/api/tools/{tool_name}")
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Error getting tool info for {tool_name}: {str(e)}")
            raise HTTPMCPError(f"Failed to get tool info: {str(e)}")
    
    async def health_check(self) -> bool:
        """
        Check if the MCP server is healthy.
        
        Returns:
            True if server is healthy, False otherwise
        """
        try:
            response = await self.client.get("/api/tools")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return False


class HTTPMCPError(Exception):
    """Custom exception for HTTP MCP client errors."""
    pass


# Convenience functions for easy usage
async def create_http_mcp_client(base_url: str, timeout: int = 30) -> HTTPMCPClient:
    """
    Create and connect to an HTTP MCP client.
    
    Args:
        base_url: Base URL of the MCP server
        timeout: Request timeout in seconds
        
    Returns:
        Connected HTTPMCPClient instance
    """
    client = HTTPMCPClient(base_url, timeout)
    await client.connect()
    return client


async def test_mcp_server(base_url: str) -> Dict[str, Any]:
    """
    Test the MCP server and return its capabilities.
    
    Args:
        base_url: Base URL of the MCP server
        
    Returns:
        Dictionary containing server capabilities
    """
    async with HTTPMCPClient(base_url) as client:
        try:
            # Test connection
            health = await client.health_check()
            
            # Get available tools
            tools = await client.list_tools()
            
            # Test a simple tool call
            test_result = None
            if tools:
                first_tool = tools[0]
                tool_name = first_tool.get("name", "")
                if tool_name == "get_categories":
                    test_result = await client.call_tool(tool_name, {})
            
            return {
                "healthy": health,
                "tools_count": len(tools),
                "tools": tools,
                "test_result": test_result,
                "server_url": base_url
            }
            
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
                "server_url": base_url
            }
