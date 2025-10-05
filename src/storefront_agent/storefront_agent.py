"""Main Storefront Agent that orchestrates Azure LLM and MCP interactions."""

import asyncio
import json
from typing import Dict, Any, Optional, List
from loguru import logger
from .azure_llm_client import AzureLLMClient, AzureLLMError
from .mcp_client import MCPClient, MCPError
from .mcp_router import MCPRouter
from .config import config


class StorefrontAgent:
    """Main Storefront Agent class that coordinates Azure LLM and MCP operations."""
    
    def __init__(self, mcp_server_url: Optional[str] = None):
        """
        Initialize the Storefront Agent.
        
        Args:
            mcp_server_url: Optional MCP server URL override (for backward compatibility)
        """
        self.azure_llm = AzureLLMClient()
        self.mcp_router = MCPRouter(self.azure_llm)
        self.is_connected = False
        
        # Always use MCP server - no direct tool connections
        if mcp_server_url:
            # Register the provided MCP server as the primary server
            self.primary_mcp_server_url = mcp_server_url
        else:
            # Use default MCP server from configuration
            self.primary_mcp_server_url = config.mcp.server_url
        
    async def initialize(self) -> bool:
        """
        Initialize the agent by connecting to the MCP server.
        
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            logger.info("Initializing Storefront Agent...")
            
            # Register MCP servers
            await self._register_mcp_servers()
            
            # Connect to the primary MCP server
            self.is_connected = await self.mcp_router.connect_to_server("storefront")
            if not self.is_connected:
                logger.error("Failed to connect to MCP server")
                return False
            
            # Test MCP router
            try:
                servers_info = await self.mcp_router.get_available_servers()
                logger.info(f"MCP Router initialized with {len(servers_info)} registered servers")
            except Exception as e:
                logger.warning(f"Could not get MCP server info: {str(e)}")
            
            logger.info("Storefront Agent initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Storefront Agent: {str(e)}")
            return False
    
    async def _register_mcp_servers(self):
        """Register available MCP servers with the router."""
        try:
            # Register the storefront MCP server using the configured URL
            self.mcp_router.register_mcp_server(
                name="storefront",
                url=self.primary_mcp_server_url,
                description="Storefront operations server for product management, search, and catalog operations",
                capabilities=[
                    "product_search",
                    "product_management", 
                    "category_management",
                    "inventory_operations",
                    "catalog_operations"
                ]
            )
            
            # You can register additional MCP servers here
            # Example:
            # self.mcp_router.register_mcp_server(
            #     name="inventory",
            #     url="https://inventory-mcp-server.azurecontainerapps.io",
            #     description="Inventory management server",
            #     capabilities=["stock_management", "inventory_tracking"]
            # )
            
            logger.info(f"MCP server registered: storefront at {self.primary_mcp_server_url}")
            
        except Exception as e:
            logger.error(f"Failed to register MCP servers: {str(e)}")
            raise
    
    async def process_user_request(
        self,
        user_input: str,
        custom_prompt: Optional[str] = None,
        llm_parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a user's natural language request through the MCP server.
        
        Args:
            user_input: The user's natural language input
            custom_prompt: Optional custom prompt template
            llm_parameters: Optional LLM parameters override
            
        Returns:
            Dictionary containing the complete response
        """
        try:
            logger.info(f"Processing user request through MCP server: {user_input[:100]}...")
            
            # Ensure we're connected to the MCP server
            if not self.is_connected:
                logger.error("Not connected to MCP server")
                return {
                    "user_input": user_input,
                    "error": "Not connected to MCP server",
                    "success": False
                }
            
            # Use MCP router to execute the request through the MCP server
            mcp_result = await self.mcp_router.execute_request(user_input)
            
            if not mcp_result.get("success"):
                # If MCP execution failed, provide a helpful error message
                logger.warning("MCP execution failed")
                return {
                    "user_input": user_input,
                    "mcp_result": mcp_result,
                    "final_response": f"I understand your request, but encountered an error while processing it through the MCP server: {mcp_result.get('error', 'Unknown error')}",
                    "success": False,
                    "error": mcp_result.get("error", "MCP execution failed")
                }
            
            # Generate final response based on MCP result
            final_response = await self._generate_response_from_mcp_result(
                user_input=user_input,
                mcp_result=mcp_result
            )
            
            logger.info("User request processed successfully through MCP server")
            
            return {
                "user_input": user_input,
                "mcp_result": mcp_result,
                "final_response": final_response,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error processing user request: {str(e)}")
            return {
                "user_input": user_input,
                "error": str(e),
                "success": False
            }
    
    async def _execute_mcp_operations(
        self,
        operations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Execute a list of MCP operations.
        
        Args:
            operations: List of MCP operations to execute
            
        Returns:
            List of operation results
        """
        results = []
        
        for operation in operations:
            try:
                op_name = operation.get("operation", "unknown")
                parameters = operation.get("parameters", {})
                description = operation.get("description", "No description")
                
                logger.info(f"Executing MCP operation: {op_name}")
                
                # Execute the operation
                if op_name.startswith("tools/"):
                    # Tool-based operation
                    tool_name = op_name.replace("tools/", "")
                    result = await self.mcp_client.call_tool(tool_name, parameters)
                elif op_name.startswith("resources/"):
                    # Resource-based operation
                    resource_uri = parameters.get("uri", "")
                    result = await self.mcp_client.read_resource(resource_uri)
                else:
                    # Generic operation
                    result = await self.mcp_client.execute_operation(
                        op_name, parameters
                    )
                
                results.append({
                    "operation": op_name,
                    "description": description,
                    "parameters": parameters,
                    "result": result,
                    "success": True
                })
                
                logger.info(f"Successfully executed operation: {op_name}")
                
            except MCPError as e:
                logger.error(f"MCP operation failed: {str(e)}")
                results.append({
                    "operation": operation.get("operation", "unknown"),
                    "description": operation.get("description", ""),
                    "parameters": operation.get("parameters", {}),
                    "error": str(e),
                    "success": False
                })
            except Exception as e:
                logger.error(f"Unexpected error in MCP operation: {str(e)}")
                results.append({
                    "operation": operation.get("operation", "unknown"),
                    "description": operation.get("description", ""),
                    "parameters": operation.get("parameters", {}),
                    "error": f"Unexpected error: {str(e)}",
                    "success": False
                })
        
        return results
    
    async def _generate_final_response(
        self,
        user_input: str,
        intent_analysis: Dict[str, Any],
        mcp_results: List[Dict[str, Any]]
    ) -> str:
        """
        Generate the final response to the user.
        
        Args:
            user_input: Original user input
            intent_analysis: Intent analysis results
            mcp_results: Results from MCP operations
            
        Returns:
            Final response text
        """
        try:
            # If we have MCP results, use the LLM to interpret them
            if mcp_results:
                # Create a summary of MCP results for the LLM
                mcp_summary = []
                for result in mcp_results:
                    if result.get("success"):
                        mcp_summary.append({
                            "operation": result["operation"],
                            "description": result["description"],
                            "result": result["result"]
                        })
                    else:
                        mcp_summary.append({
                            "operation": result["operation"],
                            "description": result["description"],
                            "error": result.get("error", "Unknown error")
                        })
                
                # Use LLM to interpret the results
                interpretation = await self.azure_llm.interpret_mcp_response(
                    mcp_response={"operations": mcp_summary},
                    original_request=user_input
                )
                
                return interpretation
            else:
                # No MCP operations, return the user message from intent analysis
                return intent_analysis.get("user_message", "I understand your request, but I couldn't determine any specific actions to take.")
                
        except Exception as e:
            logger.error(f"Error generating final response: {str(e)}")
            return f"I processed your request but encountered an error while generating the response: {str(e)}"
    
    async def _generate_response_from_mcp_result(
        self,
        user_input: str,
        mcp_result: Dict[str, Any]
    ) -> str:
        """
        Generate a user-friendly response from MCP execution result.
        
        Args:
            user_input: Original user input
            mcp_result: Result from MCP execution
            
        Returns:
            User-friendly response text
        """
        try:
            server_name = mcp_result.get("server_name", "Unknown")
            tool_name = mcp_result.get("tool_name", "Unknown")
            result = mcp_result.get("result", {})
            selection = mcp_result.get("selection", {})
            
            # Create a summary for the LLM to interpret
            mcp_summary = {
                "server_used": server_name,
                "tool_called": tool_name,
                "reasoning": selection.get("reasoning", "No reasoning provided"),
                "confidence": selection.get("confidence", 0.0),
                "result": result
            }
            
            # Use LLM to interpret the MCP result
            interpretation = await self.azure_llm.interpret_mcp_response(
                mcp_response={"operations": [mcp_summary]},
                original_request=user_input
            )
            
            return interpretation
            
        except Exception as e:
            logger.error(f"Error generating response from MCP result: {str(e)}")
            return f"I executed your request using the {mcp_result.get('server_name', 'MCP')} server, but encountered an error while generating the response: {str(e)}"
    
    async def get_available_operations(self) -> Dict[str, Any]:
        """
        Get information about available MCP operations across all servers.
        
        Returns:
            Dictionary containing available tools and servers
        """
        try:
            servers_info = await self.mcp_router.get_available_servers()
            
            total_tools = 0
            all_tools = []
            
            for server_name, server_info in servers_info.items():
                if server_info.get("connected") and server_info.get("tools"):
                    tools = server_info["tools"]
                    total_tools += len(tools)
                    for tool in tools:
                        tool["server"] = server_name
                        all_tools.append(tool)
            
            return {
                "servers": servers_info,
                "tools": all_tools,
                "total_servers": len(servers_info),
                "total_tools": total_tools,
                "connected_servers": sum(1 for s in servers_info.values() if s.get("connected"))
            }
            
        except Exception as e:
            logger.error(f"Error getting available operations: {str(e)}")
            return {"error": str(e)}
    
    async def test_connection(self) -> bool:
        """
        Test the connection to the MCP server.
        
        Returns:
            True if connection is working, False otherwise
        """
        try:
            if not self.is_connected:
                return False
            
            # Test MCP server connection by getting available servers
            servers_info = await self.mcp_router.get_available_servers()
            storefront_server = servers_info.get("storefront")
            
            if storefront_server and storefront_server.get("connected"):
                return True
            else:
                logger.error("MCP server not connected")
                return False
            
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return False
    
    async def shutdown(self):
        """Shutdown the agent and disconnect from MCP server."""
        try:
            logger.info("Shutting down Storefront Agent...")
            
            # Disconnect from MCP router servers
            await self.mcp_router.disconnect_all()
            
            self.is_connected = False
            logger.info("Storefront Agent shutdown complete")
        except Exception as e:
            logger.error(f"Error during shutdown: {str(e)}")


class StorefrontAgentError(Exception):
    """Custom exception for Storefront Agent errors."""
    pass
