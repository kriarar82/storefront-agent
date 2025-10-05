"""Azure LLM client for the Storefront Agent."""

import json
import asyncio
from typing import Dict, Any, Optional, List
from openai import AsyncAzureOpenAI
from loguru import logger
from .config import config


class AzureLLMClient:
    """Client for interacting with Azure OpenAI services."""
    
    def __init__(self):
        """Initialize the Azure LLM client."""
        self.client = AsyncAzureOpenAI(
            azure_endpoint=config.azure.endpoint,
            api_key=config.azure.api_key,
            api_version=config.azure.api_version
        )
        self.deployment_name = config.azure.deployment_name
        
    async def generate_response(
        self,
        user_input: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        top_p: float = 0.9,
        frequency_penalty: float = 0.0,
        presence_penalty: float = 0.0,
        stop: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Generate a response from Azure LLM.
        
        Args:
            user_input: The user's input text
            system_prompt: Optional system prompt override
            temperature: Controls randomness (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            top_p: Nucleus sampling parameter
            frequency_penalty: Penalty for frequent tokens
            presence_penalty: Penalty for presence of tokens
            stop: List of stop sequences
            
        Returns:
            Dictionary containing the response and metadata
        """
        try:
            # Use provided system prompt or default from config
            system_content = system_prompt or config.system_prompt
            
            logger.info(f"Generating response for user input: {user_input[:100]}...")
            
            # Prepare parameters based on model type
            params = {
                "model": self.deployment_name,
                "messages": [
                    {"role": "system", "content": system_content},
                    {"role": "user", "content": user_input}
                ]
            }
            
            # Add parameters only if they're supported by the model
            # GPT-5 Nano has specific parameter restrictions
            if self.deployment_name == "gpt-5-nano":
                # GPT-5 Nano only supports default temperature (1.0) and no max_tokens
                if temperature != 1.0:
                    logger.warning("GPT-5 Nano only supports default temperature (1.0), ignoring provided temperature")
            else:
                # Standard models support all parameters
                params.update({
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "top_p": top_p,
                    "frequency_penalty": frequency_penalty,
                    "presence_penalty": presence_penalty,
                    "stop": stop
                })
            
            response = await self.client.chat.completions.create(**params)
            
            # Extract response content
            content = response.choices[0].message.content
            finish_reason = response.choices[0].finish_reason
            
            logger.info(f"Generated response with finish reason: {finish_reason}")
            
            return {
                "content": content,
                "finish_reason": finish_reason,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                "model": response.model,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            raise AzureLLMError(f"Failed to generate response: {str(e)}")
    
    async def analyze_user_intent(
        self,
        user_input: str,
        custom_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze user input to determine intent and required MCP operations.
        
        Args:
            user_input: The user's natural language input
            custom_prompt: Optional custom prompt template
            
        Returns:
            Dictionary containing intent analysis and MCP operations
        """
        try:
            # Use custom prompt or default template
            prompt_template = custom_prompt or config.user_prompt_template
            formatted_prompt = prompt_template.format(user_input=user_input)
            
            logger.info(f"Analyzing user intent for: {user_input}")
            
            response = await self.generate_response(
                user_input=formatted_prompt,
                temperature=0.3,  # Lower temperature for more consistent analysis
                max_tokens=500
            )
            
            # Try to parse JSON response
            try:
                intent_data = json.loads(response["content"])
                logger.info(f"Successfully parsed intent analysis: {intent_data.get('intent', 'Unknown')}")
                return intent_data
            except json.JSONDecodeError:
                logger.warning("Failed to parse JSON response, returning raw content")
                return {
                    "intent": "unknown",
                    "confidence": 0.0,
                    "mcp_operations": [],
                    "user_message": response["content"],
                    "raw_response": response["content"]
                }
                
        except Exception as e:
            logger.error(f"Error analyzing user intent: {str(e)}")
            raise AzureLLMError(f"Failed to analyze user intent: {str(e)}")
    
    async def generate_mcp_request(
        self,
        operation: str,
        parameters: Dict[str, Any],
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a properly formatted MCP request.
        
        Args:
            operation: The MCP operation to perform
            parameters: Parameters for the operation
            context: Optional context for the request
            
        Returns:
            Dictionary containing the MCP request
        """
        try:
            prompt = f"""
Generate a properly formatted MCP request for the following operation:

Operation: {operation}
Parameters: {json.dumps(parameters, indent=2)}
Context: {context or "No additional context"}

Please format this as a valid MCP request JSON object with the following structure:
{{
    "jsonrpc": "2.0",
    "id": "unique_request_id",
    "method": "operation_name",
    "params": {{
        "parameters": {{...}}
    }}
}}

Ensure the request follows MCP protocol standards.
"""
            
            response = await self.generate_response(
                user_input=prompt,
                temperature=0.1,  # Very low temperature for consistent formatting
                max_tokens=300
            )
            
            # Try to parse the JSON response
            try:
                mcp_request = json.loads(response["content"])
                logger.info(f"Generated MCP request for operation: {operation}")
                return mcp_request
            except json.JSONDecodeError:
                logger.warning("Failed to parse MCP request JSON, returning raw content")
                return {
                    "error": "Failed to parse MCP request",
                    "raw_response": response["content"]
                }
                
        except Exception as e:
            logger.error(f"Error generating MCP request: {str(e)}")
            raise AzureLLMError(f"Failed to generate MCP request: {str(e)}")
    
    async def interpret_mcp_response(
        self,
        mcp_response: Dict[str, Any],
        original_request: str
    ) -> str:
        """
        Interpret MCP server response and provide user-friendly explanation.
        
        Args:
            mcp_response: The response from the MCP server
            original_request: The original user request
            
        Returns:
            User-friendly explanation of the MCP response
        """
        try:
            prompt = f"""
Interpret the following MCP server response and provide a user-friendly explanation:

Original User Request: {original_request}

MCP Server Response: {json.dumps(mcp_response, indent=2)}

The MCP server has these tools available:
- get_product: Get detailed product information by ID
- search_products: Search for products by query
- get_categories: Get all product categories
- get_products_by_category: Get products by category

Please provide:
1. Restate succinctly what the user asked.
2. Clearly say whether the requested product or products are available based on results.
3. Summarize the most relevant details (e.g., product name, price, availability) in 1-3 short sentences.
4. If there was an error, explain briefly what went wrong and suggest a tool-driven next step.
5. Keep it conversational and concise.
"""
            
            response = await self.generate_response(
                user_input=prompt,
                temperature=0.5,
                max_tokens=400
            )
            
            logger.info("Successfully interpreted MCP response")
            return response["content"]
            
        except Exception as e:
            logger.error(f"Error interpreting MCP response: {str(e)}")
            raise AzureLLMError(f"Failed to interpret MCP response: {str(e)}")

    async def generate_no_matching_tool_response(
        self,
        original_request: str,
        available_tools: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """
        Generate a friendly response when no matching tool was found for the user request.
        """
        try:
            tool_lines = []
            if available_tools:
                for tool in available_tools[:8]:  # limit to avoid long prompts
                    name = tool.get("name") or tool.get("tool_name") or "unknown_tool"
                    description = tool.get("description") or ""
                    tool_lines.append(f"- {name}: {description}")
            tools_text = "\n".join(tool_lines) if tool_lines else (
                "- get_product: Get product by ID\n"
                "- search_products: Search products by query\n"
                "- get_categories: List categories\n"
                "- get_products_by_category: Products by category"
            )

            prompt = f"""
You are a friendly customer service agent for an online storefront.

The user asked: "{original_request}"

No matching tool was confidently identified for this request.

Please respond as a helpful customer service agent:
- Greet briefly and acknowledge the request.
- Explain that you couldn't find an exact tool match for that request.
- Offer guidance on how to proceed using available capabilities (below), with one concise example.
- Ask 1 clarifying question if it helps move forward.

Available tools:
{tools_text}

Keep the response to 2-5 sentences, clear and conversational.
"""

            response = await self.generate_response(
                user_input=prompt,
                temperature=0.6,
                max_tokens=150
            )
            return response["content"]
        except Exception as e:
            logger.error(f"Error generating no-matching-tool response: {str(e)}")
            return (
                "Hi! I couldn't find a matching tool for that. Try asking about products, "
                "categories, or searching for items by name or category."
            )


class AzureLLMError(Exception):
    """Custom exception for Azure LLM client errors."""
    pass
