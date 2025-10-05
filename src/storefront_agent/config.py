"""Configuration management for the Storefront Agent."""

import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
from .environments import load_environment_config, Environment

# Load environment variables
load_dotenv()

# Load environment-specific configuration
env_config = load_environment_config()


class AzureConfig(BaseSettings):
    """Azure OpenAI configuration."""
    
    endpoint: str = Field(default="", env="AZURE_OPENAI_ENDPOINT")
    api_key: str = Field(default="", env="AZURE_OPENAI_API_KEY")
    api_version: str = Field(default="2024-02-15-preview", env="AZURE_OPENAI_API_VERSION")
    deployment_name: str = Field(default="", env="AZURE_OPENAI_DEPLOYMENT_NAME")
    
    class Config:
        env_file = ".env"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Override with environment-specific config if available
        azure_config = env_config.get_azure_config()
        if azure_config.get("endpoint"):
            self.endpoint = azure_config["endpoint"]
        if azure_config.get("api_key"):
            self.api_key = azure_config["api_key"]
        if azure_config.get("api_version"):
            self.api_version = azure_config["api_version"]
        if azure_config.get("deployment_name"):
            self.deployment_name = azure_config["deployment_name"]


class MCPConfig(BaseSettings):
    """MCP Server configuration."""
    
    server_url: str = Field(default="ws://localhost:8080", env="MCP_SERVER_URL")
    timeout: int = Field(default=30, env="MCP_SERVER_TIMEOUT")
    
    class Config:
        env_file = ".env"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Override with environment-specific config if available
        mcp_config = env_config.get_mcp_config()
        if mcp_config.get("server_url"):
            self.server_url = mcp_config["server_url"]
        if mcp_config.get("timeout"):
            self.timeout = mcp_config["timeout"]


class AppConfig(BaseSettings):
    """Application configuration."""
    
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    max_retries: int = Field(default=3, env="MAX_RETRIES")
    debug: bool = Field(default=False, env="DEBUG")
    
    class Config:
        env_file = ".env"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Override with environment-specific config if available
        app_config = env_config.get_app_config()
        if app_config.get("log_level"):
            self.log_level = app_config["log_level"]
        if app_config.get("max_retries"):
            self.max_retries = app_config["max_retries"]
        if app_config.get("debug") is not None:
            self.debug = app_config["debug"]


class StorefrontAgentConfig:
    """Main configuration class."""
    
    def __init__(self):
        self.azure = AzureConfig()
        self.mcp = MCPConfig()
        self.app = AppConfig()
        
        # Storefront Agent specific prompts
        self.system_prompt = """You are a Storefront Agent, an AI assistant specialized in understanding natural language requests related to storefront operations and determining appropriate actions to take with MCP (Model Context Protocol) servers.

Your primary responsibilities:
1. Analyze natural language input from users
2. Identify the intent and required actions
3. Determine which MCP server tools/resources to use
4. Format appropriate MCP requests
5. Interpret MCP responses and provide user-friendly feedback

Available MCP operations you can perform:
- Product catalog management (search, add, update, delete products)
- Inventory management (check stock, update quantities)
- Order processing (create, update, track orders)
- Customer management (lookup, update customer information)
- Analytics and reporting (sales data, performance metrics)
- Store configuration (settings, preferences)

When responding:
- Always be helpful and professional
- Ask clarifying questions when needed
- Provide clear explanations of what actions you're taking
- Handle errors gracefully and suggest alternatives
- Use natural language to explain technical operations

Remember: You are the interface between users and the MCP server ecosystem. Make complex operations feel simple and intuitive."""

        self.user_prompt_template = """User Request: {user_input}

Please analyze this request and determine:
1. What the user wants to accomplish
2. Which MCP server operations are needed
3. The specific parameters required for those operations

Respond in JSON format with the following structure:
{{
    "intent": "description of what the user wants",
    "confidence": 0.0-1.0,
    "mcp_operations": [
        {{
            "operation": "operation_name",
            "parameters": {{"param1": "value1", "param2": "value2"}},
            "description": "what this operation does"
        }}
    ],
    "user_message": "friendly explanation of what you're going to do"
}}"""


# Global configuration instance
config = StorefrontAgentConfig()
