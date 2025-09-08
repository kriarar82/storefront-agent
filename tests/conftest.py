"""Pytest configuration and fixtures for Storefront Agent tests."""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from pathlib import Path
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from storefront_agent import StorefrontAgent, AzureLLMClient, MCPClient


@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_azure_llm():
    """Mock Azure LLM client."""
    mock = AsyncMock(spec=AzureLLMClient)
    mock.generate_response.return_value = {
        "content": "Mock response",
        "finish_reason": "stop",
        "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
        "model": "mock-model",
        "temperature": 0.7,
        "max_tokens": 1000
    }
    mock.analyze_user_intent.return_value = {
        "intent": "test intent",
        "confidence": 0.9,
        "mcp_operations": [],
        "user_message": "Mock user message"
    }
    return mock


@pytest.fixture
def mock_mcp_client():
    """Mock MCP client."""
    mock = AsyncMock(spec=MCPClient)
    mock.connect.return_value = True
    mock.disconnect.return_value = None
    mock.list_tools.return_value = [
        {"name": "test_tool", "description": "A test tool"}
    ]
    mock.get_resources.return_value = [
        {"uri": "test://resource", "name": "Test Resource"}
    ]
    mock.call_tool.return_value = {"result": "success"}
    mock.execute_operation.return_value = {"result": "success"}
    return mock


@pytest.fixture
async def storefront_agent(mock_azure_llm, mock_mcp_client):
    """Create a StorefrontAgent instance with mocked dependencies."""
    agent = StorefrontAgent()
    agent.azure_llm = mock_azure_llm
    agent.mcp_client = mock_mcp_client
    agent.is_connected = True
    return agent


@pytest.fixture
def sample_user_request():
    """Sample user request for testing."""
    return "Show me all products in the electronics category"


@pytest.fixture
def sample_intent_analysis():
    """Sample intent analysis response."""
    return {
        "intent": "product search",
        "confidence": 0.9,
        "mcp_operations": [
            {
                "operation": "products/search",
                "parameters": {"category": "electronics"},
                "description": "Search for products in electronics category"
            }
        ],
        "user_message": "I'll search for products in the electronics category"
    }


@pytest.fixture
def sample_mcp_response():
    """Sample MCP response."""
    return {
        "result": {
            "products": [
                {"id": "1", "name": "Laptop", "category": "electronics", "price": 999.99},
                {"id": "2", "name": "Phone", "category": "electronics", "price": 699.99}
            ]
        }
    }
