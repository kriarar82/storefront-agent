"""Environment-specific configuration management."""

import os
from enum import Enum
from typing import Dict, Any, Optional
from pathlib import Path


class Environment(Enum):
    """Supported environments."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


class EnvironmentConfig:
    """Environment-specific configuration loader."""
    
    def __init__(self, environment: Optional[Environment] = None):
        """
        Initialize environment configuration.
        
        Args:
            environment: Environment to load. If None, auto-detect from ENV variable.
        """
        self.environment = environment or self._detect_environment()
        self.config = self._load_environment_config()
    
    def _detect_environment(self) -> Environment:
        """Auto-detect environment from ENV variable."""
        env_name = os.getenv("ENVIRONMENT", "development").lower()
        try:
            return Environment(env_name)
        except ValueError:
            print(f"Warning: Unknown environment '{env_name}', defaulting to development")
            return Environment.DEVELOPMENT
    
    def _load_environment_config(self) -> Dict[str, Any]:
        """Load configuration for the current environment."""
        base_config = {
            "environment": self.environment.value,
            "log_level": "INFO",
            "max_retries": 3,
            "timeout": 30,
        }
        
        if self.environment == Environment.DEVELOPMENT:
            return self._get_development_config(base_config)
        elif self.environment == Environment.STAGING:
            return self._get_staging_config(base_config)
        elif self.environment == Environment.PRODUCTION:
            return self._get_production_config(base_config)
        elif self.environment == Environment.TESTING:
            return self._get_testing_config(base_config)
        else:
            return base_config
    
    def _get_development_config(self, base: Dict[str, Any]) -> Dict[str, Any]:
        """Development environment configuration."""
        return {
            **base,
            "azure": {
                "endpoint": os.getenv("AZURE_OPENAI_ENDPOINT", ""),
                "api_key": os.getenv("AZURE_OPENAI_API_KEY", ""),
                "api_version": "2024-02-15-preview",
                "deployment_name": os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-5-nano"),
            },
            "mcp": {
                "server_url": os.getenv("MCP_SERVER_URL", "ws://localhost:8080"),
                "timeout": 30,
            },
            "log_level": "DEBUG",
            "debug": True,
        }
    
    def _get_staging_config(self, base: Dict[str, Any]) -> Dict[str, Any]:
        """Staging environment configuration."""
        return {
            **base,
            "azure": {
                "endpoint": os.getenv("AZURE_OPENAI_ENDPOINT", ""),
                "api_key": os.getenv("AZURE_OPENAI_API_KEY", ""),
                "api_version": "2024-02-15-preview",
                "deployment_name": os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-5-nano-staging"),
            },
            "mcp": {
                "server_url": os.getenv("MCP_SERVER_URL", "wss://mcp-staging.azurewebsites.net"),
                "timeout": 30,
            },
            "log_level": "INFO",
            "debug": False,
        }
    
    def _get_production_config(self, base: Dict[str, Any]) -> Dict[str, Any]:
        """Production environment configuration."""
        # Load from env.production file
        env_file = Path("env.production")
        if env_file.exists():
            from dotenv import load_dotenv
            load_dotenv(env_file)
        
        return {
            **base,
            "azure": {
                "endpoint": os.getenv("AZURE_OPENAI_ENDPOINT", ""),
                "api_key": os.getenv("AZURE_OPENAI_API_KEY", ""),
                "api_version": "2024-02-15-preview",
                "deployment_name": os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-5-nano"),
            },
            "mcp": {
                "server_url": os.getenv("MCP_SERVER_URL", "https://storefront-mcp-server.kindflower-89fe6492.eastus.azurecontainerapps.io"),
                "timeout": 60,  # Longer timeout for production
            },
            "log_level": "WARNING",
            "debug": False,
            "max_retries": 5,  # More retries for production
        }
    
    def _get_testing_config(self, base: Dict[str, Any]) -> Dict[str, Any]:
        """Testing environment configuration."""
        return {
            **base,
            "azure": {
                "endpoint": os.getenv("AZURE_OPENAI_ENDPOINT", "https://test-resource.openai.azure.com/"),
                "api_key": os.getenv("AZURE_OPENAI_API_KEY", "test-key"),
                "api_version": "2024-02-15-preview",
                "deployment_name": os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-5-nano-test"),
            },
            "mcp": {
                "server_url": os.getenv("MCP_SERVER_URL", "ws://localhost:8081"),  # Different port for testing
                "timeout": 10,
            },
            "log_level": "DEBUG",
            "debug": True,
        }
    
    def get_config(self) -> Dict[str, Any]:
        """Get the current environment configuration."""
        return self.config
    
    def get_azure_config(self) -> Dict[str, Any]:
        """Get Azure-specific configuration."""
        return self.config.get("azure", {})
    
    def get_mcp_config(self) -> Dict[str, Any]:
        """Get MCP-specific configuration."""
        return self.config.get("mcp", {})
    
    def get_app_config(self) -> Dict[str, Any]:
        """Get application-specific configuration."""
        return {
            "log_level": self.config.get("log_level", "INFO"),
            "max_retries": self.config.get("max_retries", 3),
            "timeout": self.config.get("timeout", 30),
            "debug": self.config.get("debug", False),
        }


def load_environment_config(environment: Optional[Environment] = None) -> EnvironmentConfig:
    """
    Load configuration for the specified environment.
    
    Args:
        environment: Environment to load. If None, auto-detect.
        
    Returns:
        EnvironmentConfig instance
    """
    return EnvironmentConfig(environment)
