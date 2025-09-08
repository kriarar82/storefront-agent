"""Main Storefront Agent that orchestrates Azure LLM and MCP interactions."""

import asyncio
import json
from typing import Dict, Any, Optional, List
from loguru import logger
from .azure_llm_client import AzureLLMClient, AzureLLMError
from .mcp_client import MCPClient, MCPError
from .config import config


class StorefrontAgent:
    """Main Storefront Agent class that coordinates Azure LLM and MCP operations."""
    
    def __init__(self, mcp_server_url: Optional[str] = None):
        """
        Initialize the Storefront Agent.
        
        Args:
            mcp_server_url: Optional MCP server URL override
        """
        self.azure_llm = AzureLLMClient()
        self.mcp_client = MCPClient(mcp_server_url)
        self.is_connected = False
        
    async def initialize(self) -> bool:
        """
        Initialize the agent by connecting to the MCP server.
        
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            logger.info("Initializing Storefront Agent...")
            
            # Connect to MCP server
            self.is_connected = await self.mcp_client.connect()
            if not self.is_connected:
                logger.error("Failed to connect to MCP server")
                return False
            
            # Test the connection by listing available tools
            try:
                tools = await self.mcp_client.list_tools()
                logger.info(f"Connected to MCP server with {len(tools)} available tools")
            except Exception as e:
                logger.warning(f"Could not list MCP tools: {str(e)}")
            
            logger.info("Storefront Agent initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Storefront Agent: {str(e)}")
            return False
    
    async def process_user_request(
        self,
        user_input: str,
        custom_prompt: Optional[str] = None,
        llm_parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a user's natural language request.
        
        Args:
            user_input: The user's natural language input
            custom_prompt: Optional custom prompt template
            llm_parameters: Optional LLM parameters override
            
        Returns:
            Dictionary containing the complete response
        """
        try:
            logger.info(f"Processing user request: {user_input[:100]}...")
            
            # Step 1: Analyze user intent using Azure LLM
            intent_analysis = await self.azure_llm.analyze_user_intent(
                user_input=user_input,
                custom_prompt=custom_prompt
            )
            
            logger.info(f"Intent analysis completed: {intent_analysis.get('intent', 'Unknown')}")
            
            # Step 2: Execute MCP operations if any are identified
            mcp_results = []
            if intent_analysis.get("mcp_operations"):
                mcp_results = await self._execute_mcp_operations(
                    intent_analysis["mcp_operations"]
                )
            
            # Step 3: Generate final response
            final_response = await self._generate_final_response(
                user_input=user_input,
                intent_analysis=intent_analysis,
                mcp_results=mcp_results
            )
            
            logger.info("User request processed successfully")
            
            return {
                "user_input": user_input,
                "intent_analysis": intent_analysis,
                "mcp_results": mcp_results,
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
    
    async def get_available_operations(self) -> Dict[str, Any]:
        """
        Get information about available MCP operations.
        
        Returns:
            Dictionary containing available tools and resources
        """
        try:
            if not self.is_connected:
                return {"error": "Not connected to MCP server"}
            
            tools = await self.mcp_client.list_tools()
            resources = await self.mcp_client.get_resources()
            
            return {
                "tools": tools,
                "resources": resources,
                "total_tools": len(tools),
                "total_resources": len(resources)
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
            
            # Try to list tools as a connection test
            await self.mcp_client.list_tools()
            return True
            
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return False
    
    async def shutdown(self):
        """Shutdown the agent and disconnect from MCP server."""
        try:
            logger.info("Shutting down Storefront Agent...")
            await self.mcp_client.disconnect()
            self.is_connected = False
            logger.info("Storefront Agent shutdown complete")
        except Exception as e:
            logger.error(f"Error during shutdown: {str(e)}")


class StorefrontAgentError(Exception):
    """Custom exception for Storefront Agent errors."""
    pass
