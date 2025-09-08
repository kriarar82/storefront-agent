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
            
            response = await self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": system_content},
                    {"role": "user", "content": user_input}
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                frequency_penalty=frequency_penalty,
                presence_penalty=presence_penalty,
                stop=stop
            )
            
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

Please provide:
1. A clear explanation of what happened
2. Whether the operation was successful
3. Any relevant data or results
4. Next steps if applicable

Keep the explanation conversational and helpful for a non-technical user.
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


class AzureLLMError(Exception):
    """Custom exception for Azure LLM client errors."""
    pass
