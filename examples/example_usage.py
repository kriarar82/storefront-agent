"""Example usage of the Storefront Agent."""

import asyncio
import json
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from storefront_agent import StorefrontAgent, config


async def example_basic_usage():
    """Example of basic agent usage."""
    print("🤖 Storefront Agent - Basic Usage Example")
    print("=" * 50)
    
    # Initialize the agent
    agent = StorefrontAgent()
    
    try:
        # Initialize the agent
        print("Initializing agent...")
        success = await agent.initialize()
        if not success:
            print("❌ Failed to initialize agent")
            return
        
        print("✅ Agent initialized successfully")
        
        # Example requests
        example_requests = [
            "Show me all products in the electronics category",
            "Check inventory for product ID 12345",
            "Create a new order for customer john@example.com",
            "What are the top-selling products this month?",
            "Update the price of product ABC123 to $29.99"
        ]
        
        for request in example_requests:
            print(f"\n👤 User: {request}")
            print("🤖 Agent: Processing...")
            
            result = await agent.process_user_request(request)
            
            if result["success"]:
                print(f"🤖 Agent: {result['final_response']}")
            else:
                print(f"❌ Error: {result.get('error', 'Unknown error')}")
            
            # Add a small delay between requests
            await asyncio.sleep(1)
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    finally:
        # Cleanup
        await agent.shutdown()
        print("\n👋 Agent shutdown complete")


async def example_custom_parameters():
    """Example using custom LLM parameters."""
    print("\n🤖 Storefront Agent - Custom Parameters Example")
    print("=" * 50)
    
    agent = StorefrontAgent()
    
    try:
        await agent.initialize()
        
        # Custom request with specific parameters
        request = "Find all products with price less than $50"
        
        print(f"👤 User: {request}")
        print("🤖 Agent: Processing with custom parameters...")
        
        # Process with custom LLM parameters
        result = await agent.azure_llm.generate_response(
            user_input=request,
            temperature=0.3,  # Lower temperature for more focused results
            max_tokens=500,
            top_p=0.8
        )
        
        print(f"🤖 Agent: {result['content']}")
        print(f"📊 Tokens used: {result['usage']['total_tokens']}")
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    finally:
        await agent.shutdown()


async def example_mcp_operations():
    """Example of MCP operations."""
    print("\n🤖 Storefront Agent - MCP Operations Example")
    print("=" * 50)
    
    agent = StorefrontAgent()
    
    try:
        await agent.initialize()
        
        # Get available operations
        print("Getting available MCP operations...")
        operations = await agent.get_available_operations()
        
        if "error" in operations:
            print(f"❌ Error getting operations: {operations['error']}")
        else:
            print(f"✅ Found {operations['total_tools']} tools and {operations['total_resources']} resources")
            
            # Show some tools
            if operations.get('tools'):
                print("\n🔧 Available Tools:")
                for tool in operations['tools'][:5]:  # Show first 5 tools
                    name = tool.get('name', 'Unknown')
                    description = tool.get('description', 'No description')
                    print(f"  • {name}: {description}")
        
        # Test connection
        print("\nTesting MCP connection...")
        is_connected = await agent.test_connection()
        print(f"🔗 Connection status: {'✅ Connected' if is_connected else '❌ Disconnected'}")
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    finally:
        await agent.shutdown()


async def example_error_handling():
    """Example of error handling."""
    print("\n🤖 Storefront Agent - Error Handling Example")
    print("=" * 50)
    
    # Test with invalid MCP server URL
    agent = StorefrontAgent("ws://invalid-server:9999")
    
    try:
        print("Testing with invalid MCP server...")
        success = await agent.initialize()
        
        if not success:
            print("✅ Expected failure - invalid server URL")
        else:
            print("❌ Unexpected success")
        
        # Test with valid configuration but invalid request
        agent2 = StorefrontAgent()
        await agent2.initialize()
        
        print("\nTesting with malformed request...")
        result = await agent2.process_user_request("")
        
        if not result["success"]:
            print("✅ Expected failure - empty request")
        else:
            print("❌ Unexpected success")
    
    except Exception as e:
        print(f"✅ Caught expected error: {str(e)}")
    
    finally:
        await agent.shutdown()


async def example_custom_prompts():
    """Example using custom prompts."""
    print("\n🤖 Storefront Agent - Custom Prompts Example")
    print("=" * 50)
    
    agent = StorefrontAgent()
    
    try:
        await agent.initialize()
        
        # Custom prompt for specific use case
        custom_prompt = """User Request: {user_input}

You are a specialized inventory management assistant. Analyze the request and determine:
1. What inventory operation is needed
2. Which products or categories are involved
3. What specific parameters are required

Respond in JSON format:
{{
    "intent": "inventory operation description",
    "confidence": 0.0-1.0,
    "mcp_operations": [
        {{
            "operation": "inventory/check",
            "parameters": {{"product_id": "value"}},
            "description": "Check inventory levels"
        }}
    ],
    "user_message": "I'll help you with that inventory operation"
}}"""
        
        request = "Check if we have enough stock of product XYZ789 for 100 units"
        
        print(f"👤 User: {request}")
        print("🤖 Agent: Processing with custom inventory prompt...")
        
        result = await agent.process_user_request(
            user_input=request,
            custom_prompt=custom_prompt
        )
        
        if result["success"]:
            print(f"🤖 Agent: {result['final_response']}")
            print(f"📋 Intent: {result['intent_analysis'].get('intent', 'Unknown')}")
        else:
            print(f"❌ Error: {result.get('error', 'Unknown error')}")
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    finally:
        await agent.shutdown()


async def main():
    """Run all examples."""
    print("🚀 Storefront Agent Examples")
    print("=" * 60)
    
    examples = [
        example_basic_usage,
        example_custom_parameters,
        example_mcp_operations,
        example_error_handling,
        example_custom_prompts
    ]
    
    for i, example in enumerate(examples, 1):
        try:
            print(f"\n{'='*20} Example {i} {'='*20}")
            await example()
        except Exception as e:
            print(f"❌ Example {i} failed: {str(e)}")
        
        # Add delay between examples
        if i < len(examples):
            print("\n" + "="*60)
            await asyncio.sleep(2)
    
    print("\n🎉 All examples completed!")


if __name__ == "__main__":
    asyncio.run(main())
