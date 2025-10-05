"""MCP Server Router that uses LLM to determine which MCP server to use."""

import asyncio
import json
from typing import Dict, Any, Optional, List
from loguru import logger
from .azure_llm_client import AzureLLMClient
from .http_mcp_client import HTTPMCPClient


class MCPServerRegistry:
    """Registry of available MCP servers."""
    
    def __init__(self):
        self.servers = {}
    
    def register_server(self, name: str, url: str, description: str, capabilities: List[str]):
        """
        Register an MCP server.
        
        Args:
            name: Server name/identifier
            url: Server URL
            description: Human-readable description
            capabilities: List of capabilities this server provides
        """
        self.servers[name] = {
            "url": url,
            "description": description,
            "capabilities": capabilities,
            "client": None
        }
        logger.info(f"Registered MCP server: {name} at {url}")
    
    def get_server(self, name: str) -> Optional[Dict[str, Any]]:
        """Get server configuration by name."""
        return self.servers.get(name)
    
    def list_servers(self) -> Dict[str, Dict[str, Any]]:
        """List all registered servers."""
        return self.servers.copy()


class MCPRouter:
    """Router that uses LLM to determine which MCP server to use for a request."""
    
    def __init__(self, azure_llm: AzureLLMClient):
        """
        Initialize the MCP router.
        
        Args:
            azure_llm: Azure LLM client for natural language processing
        """
        self.azure_llm = azure_llm
        self.registry = MCPServerRegistry()
        self.connected_servers = {}
        
        # System prompt for MCP server selection
        self.server_selection_prompt = """You are an MCP (Model Context Protocol) server router. Your job is to analyze user requests and determine which MCP server should handle the request.

Available MCP servers:
{servers_info}

IMPORTANT: The MCP server has these specific tools available:
- get_product: Get detailed information about a specific product by ID (requires product_id parameter)
- search_products: Search for products by name, description, or other criteria (requires query parameter, optional limit)
- get_categories: Get all available product categories (no parameters required)
- get_products_by_category: Get products filtered by a specific category (requires category parameter, optional limit)

For each user request, determine:
1. Which MCP server is most appropriate
2. What specific tool/operation should be called from the available tools above
3. What parameters are needed using the correct parameter names

Common request patterns and their mappings:
- "Search for [product type]" → search_products with query parameter
- "Show me [product type] products" → search_products with query parameter
- "Get products in [category]" → get_products_by_category with category parameter
- "Show me all categories" → get_categories (no parameters)
- "Get product [ID]" → get_product with product_id parameter
- "Find [specific product]" → search_products with query parameter

Respond in JSON format:
{{
    "selected_server": "server_name",
    "reasoning": "explanation of why this server was chosen",
    "tool_name": "specific_tool_to_call",
    "parameters": {{"param1": "value1", "param2": "value2"}},
    "confidence": 0.0-1.0
}}

If no server is appropriate, set "selected_server" to null and explain why."""

    def register_mcp_server(self, name: str, url: str, description: str, capabilities: List[str]):
        """Register an MCP server with the router."""
        self.registry.register_server(name, url, description, capabilities)
        logger.info(f"📝 Registered MCP server: {name}")
        logger.info(f"   URL: {url}")
        logger.info(f"   Description: {description}")
        logger.info(f"   Capabilities: {', '.join(capabilities)}")
    
    async def connect_to_server(self, server_name: str) -> bool:
        """
        Connect to a specific MCP server.
        
        Args:
            server_name: Name of the server to connect to
            
        Returns:
            True if connection successful, False otherwise
        """
        try:
            server_config = self.registry.get_server(server_name)
            if not server_config:
                logger.error(f"Server {server_name} not found in registry")
                return False
            
            # Create HTTP client for the server
            client = HTTPMCPClient(server_config["url"])
            connected = await client.connect()
            
            if connected:
                self.connected_servers[server_name] = client
                logger.info(f"Connected to MCP server: {server_name}")
                return True
            else:
                logger.error(f"Failed to connect to MCP server: {server_name}")
                return False
                
        except Exception as e:
            logger.error(f"Error connecting to server {server_name}: {str(e)}")
            return False
    
    async def disconnect_from_server(self, server_name: str):
        """Disconnect from a specific MCP server."""
        try:
            if server_name in self.connected_servers:
                await self.connected_servers[server_name].disconnect()
                del self.connected_servers[server_name]
                logger.info(f"Disconnected from MCP server: {server_name}")
        except Exception as e:
            logger.error(f"Error disconnecting from server {server_name}: {str(e)}")
    
    async def disconnect_all(self):
        """Disconnect from all servers."""
        for server_name in list(self.connected_servers.keys()):
            await self.disconnect_from_server(server_name)
    
    async def select_server_for_request(self, user_input: str) -> Dict[str, Any]:
        """
        Use LLM to select the appropriate MCP server for a user request.
        
        Args:
            user_input: User's natural language request
            
        Returns:
            Dictionary containing server selection and tool information
        """
        try:
            # Build servers info for the prompt
            servers_info = []
            for name, config in self.registry.list_servers().items():
                servers_info.append(f"- {name}: {config['description']} (Capabilities: {', '.join(config['capabilities'])})")
            
            servers_text = "\n".join(servers_info)
            prompt = self.server_selection_prompt.format(servers_info=servers_text)
            
            # Get LLM response
            response = await self.azure_llm.generate_response(
                user_input=f"User Request: {user_input}\n\n{prompt}",
                temperature=0.1  # Low temperature for consistent routing
            )
            
            # Log the raw LLM response
            logger.info(f"🤖 LLM Raw Response: {response.get('content', 'No content')}")
            
            # Parse JSON response
            try:
                result = json.loads(response["content"])
                selected_server = result.get('selected_server')
                reasoning = result.get('reasoning', 'No reasoning provided')
                confidence = result.get('confidence', 0.0)
                
                logger.info(f"🎯 LLM Decision:")
                logger.info(f"   Selected Server: {selected_server}")
                logger.info(f"   Confidence: {confidence}")
                logger.info(f"   Reasoning: {reasoning}")
                
                # Find the actual MCP server URL
                if selected_server and selected_server in self.registry.list_servers():
                    server_config = self.registry.list_servers()[selected_server]
                    server_url = server_config.get('url', 'Unknown URL')
                    logger.info(f"🌐 MCP Server URL: {server_url}")
                else:
                    logger.warning(f"⚠️  Selected server '{selected_server}' not found in registry")
                
                return result
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse LLM response as JSON: {str(e)}")
                return {
                    "selected_server": None,
                    "reasoning": "Failed to parse LLM response",
                    "error": str(e),
                    "confidence": 0.0
                }
                
        except Exception as e:
            logger.error(f"Error selecting server for request: {str(e)}")
            return {
                "selected_server": None,
                "reasoning": f"Error during server selection: {str(e)}",
                "error": str(e),
                "confidence": 0.0
            }
    
    async def execute_request(self, user_input: str) -> Dict[str, Any]:
        """
        Execute a user request by routing it to the appropriate MCP server.
        
        Args:
            user_input: User's natural language request
            
        Returns:
            Dictionary containing the execution result
        """
        try:
            # Select appropriate server
            selection = await self.select_server_for_request(user_input)
            
            if not selection.get("selected_server"):
                return {
                    "success": False,
                    "error": selection.get("reasoning", "No appropriate server found"),
                    "selection": selection
                }
            
            server_name = selection["selected_server"]
            tool_name = selection.get("tool_name")
            parameters = selection.get("parameters", {})

            # If no specific tool was selected, signal fallback to the caller
            if not tool_name:
                return {
                    "success": False,
                    "error": "No appropriate tool selected",
                    "selection": selection
                }
            
            # Ensure we're connected to the selected server
            if server_name not in self.connected_servers:
                connected = await self.connect_to_server(server_name)
                if not connected:
                    return {
                        "success": False,
                        "error": f"Failed to connect to server: {server_name}",
                        "selection": selection
                    }
            
            # Execute the tool call
            client = self.connected_servers[server_name]
            logger.info(f"🔧 Executing tool '{tool_name}' on server '{server_name}'")
            logger.info(f"   Parameters: {parameters}")
            
            result = await client.call_tool(tool_name, parameters)
            
            logger.info(f"✅ Tool execution completed")
            logger.info(f"   Result: {str(result)[:200]}...")
            
            return {
                "success": True,
                "server_name": server_name,
                "tool_name": tool_name,
                "parameters": parameters,
                "result": result,
                "selection": selection
            }
            
        except Exception as e:
            logger.error(f"Error executing request: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "selection": selection if 'selection' in locals() else None
            }
    
    async def get_available_servers(self) -> Dict[str, Any]:
        """Get information about all available servers."""
        servers_info = {}
        
        for name, config in self.registry.list_servers().items():
            is_connected = name in self.connected_servers
            tools = []
            
            if is_connected:
                try:
                    tools = await self.connected_servers[name].list_tools()
                except Exception as e:
                    logger.warning(f"Could not list tools for server {name}: {str(e)}")
            
            servers_info[name] = {
                "url": config["url"],
                "description": config["description"],
                "capabilities": config["capabilities"],
                "connected": is_connected,
                "tools": tools
            }
        
        return servers_info
