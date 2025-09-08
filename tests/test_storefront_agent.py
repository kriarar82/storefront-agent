"""Tests for the StorefrontAgent class."""

import pytest
from unittest.mock import AsyncMock, patch


class TestStorefrontAgent:
    """Test cases for StorefrontAgent."""
    
    @pytest.mark.asyncio
    async def test_initialization_success(self, mock_azure_llm, mock_mcp_client):
        """Test successful agent initialization."""
        agent = StorefrontAgent()
        agent.azure_llm = mock_azure_llm
        agent.mcp_client = mock_mcp_client
        
        success = await agent.initialize()
        
        assert success is True
        assert agent.is_connected is True
        mock_mcp_client.connect.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_initialization_failure(self, mock_azure_llm):
        """Test agent initialization failure."""
        agent = StorefrontAgent()
        agent.azure_llm = mock_azure_llm
        
        # Mock MCP client connection failure
        mock_mcp_client = AsyncMock()
        mock_mcp_client.connect.return_value = False
        agent.mcp_client = mock_mcp_client
        
        success = await agent.initialize()
        
        assert success is False
        assert agent.is_connected is False
    
    @pytest.mark.asyncio
    async def test_process_user_request_success(
        self, 
        storefront_agent, 
        sample_user_request, 
        sample_intent_analysis
    ):
        """Test successful user request processing."""
        storefront_agent.azure_llm.analyze_user_intent.return_value = sample_intent_analysis
        
        result = await storefront_agent.process_user_request(sample_user_request)
        
        assert result["success"] is True
        assert "final_response" in result
        assert "intent_analysis" in result
        assert "mcp_results" in result
        storefront_agent.azure_llm.analyze_user_intent.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_user_request_with_mcp_operations(
        self, 
        storefront_agent, 
        sample_user_request
    ):
        """Test user request processing with MCP operations."""
        intent_analysis = {
            "intent": "product search",
            "confidence": 0.9,
            "mcp_operations": [
                {
                    "operation": "products/search",
                    "parameters": {"category": "electronics"},
                    "description": "Search for products"
                }
            ],
            "user_message": "I'll search for products"
        }
        
        storefront_agent.azure_llm.analyze_user_intent.return_value = intent_analysis
        storefront_agent.azure_llm.interpret_mcp_response.return_value = "Found 2 products"
        
        result = await storefront_agent.process_user_request(sample_user_request)
        
        assert result["success"] is True
        assert len(result["mcp_results"]) == 1
        assert result["mcp_results"][0]["operation"] == "products/search"
        storefront_agent.mcp_client.execute_operation.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_user_request_error(self, storefront_agent, sample_user_request):
        """Test user request processing with error."""
        storefront_agent.azure_llm.analyze_user_intent.side_effect = Exception("LLM error")
        
        result = await storefront_agent.process_user_request(sample_user_request)
        
        assert result["success"] is False
        assert "error" in result
        assert "LLM error" in result["error"]
    
    @pytest.mark.asyncio
    async def test_get_available_operations_success(self, storefront_agent):
        """Test getting available operations successfully."""
        operations = await storefront_agent.get_available_operations()
        
        assert "tools" in operations
        assert "resources" in operations
        assert "total_tools" in operations
        assert "total_resources" in operations
        storefront_agent.mcp_client.list_tools.assert_called_once()
        storefront_agent.mcp_client.get_resources.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_available_operations_not_connected(self, mock_azure_llm, mock_mcp_client):
        """Test getting operations when not connected."""
        agent = StorefrontAgent()
        agent.azure_llm = mock_azure_llm
        agent.mcp_client = mock_mcp_client
        agent.is_connected = False
        
        operations = await agent.get_available_operations()
        
        assert "error" in operations
        assert "Not connected" in operations["error"]
    
    @pytest.mark.asyncio
    async def test_test_connection_success(self, storefront_agent):
        """Test successful connection test."""
        is_connected = await storefront_agent.test_connection()
        
        assert is_connected is True
        storefront_agent.mcp_client.list_tools.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_test_connection_failure(self, mock_azure_llm, mock_mcp_client):
        """Test connection test failure."""
        agent = StorefrontAgent()
        agent.azure_llm = mock_azure_llm
        agent.mcp_client = mock_mcp_client
        agent.is_connected = True
        
        mock_mcp_client.list_tools.side_effect = Exception("Connection error")
        
        is_connected = await agent.test_connection()
        
        assert is_connected is False
    
    @pytest.mark.asyncio
    async def test_shutdown(self, storefront_agent):
        """Test agent shutdown."""
        await storefront_agent.shutdown()
        
        assert storefront_agent.is_connected is False
        storefront_agent.mcp_client.disconnect.assert_called_once()
