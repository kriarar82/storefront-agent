"""Command-line interface for the Storefront Agent."""

import asyncio
import sys
import argparse
from typing import Optional
from loguru import logger
from .storefront_agent import StorefrontAgent
from .config import config


class StorefrontAgentCLI:
    """Command-line interface for the Storefront Agent."""
    
    def __init__(self):
        """Initialize the CLI."""
        self.agent = None
        self.setup_logging()
    
    def setup_logging(self):
        """Setup logging configuration."""
        logger.remove()  # Remove default handler
        logger.add(
            sys.stdout,
            level=config.app.log_level,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
        )
        logger.add(
            "storefront_agent.log",
            level="DEBUG",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            rotation="10 MB",
            retention="7 days"
        )
    
    async def initialize(self, mcp_server_url: Optional[str] = None) -> bool:
        """
        Initialize the agent.
        
        Args:
            mcp_server_url: Optional MCP server URL override
            
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            logger.info("Starting Storefront Agent...")
            
            # Create and initialize the agent
            self.agent = StorefrontAgent(mcp_server_url)
            success = await self.agent.initialize()
            
            if success:
                logger.info("Agent initialized successfully")
            else:
                logger.error("Failed to initialize agent")
            
            return success
            
        except Exception as e:
            logger.error(f"Error initializing agent: {str(e)}")
            return False
    
    async def run_interactive(self):
        """Run the agent in interactive mode."""
        try:
            logger.info("Starting interactive mode...")
            print("\n🤖 Storefront Agent - Interactive Mode")
            print("=" * 50)
            print("Type your requests in natural language.")
            print("Type 'help' for available commands, 'quit' to exit.")
            print("=" * 50)
            
            while True:
                try:
                    # Get user input
                    user_input = input("\n👤 You: ").strip()
                    
                    if not user_input:
                        continue
                    
                    # Handle special commands
                    if user_input.lower() in ['quit', 'exit', 'q']:
                        print("👋 Goodbye!")
                        break
                    elif user_input.lower() == 'help':
                        await self._show_help()
                        continue
                    elif user_input.lower() == 'status':
                        await self._show_status()
                        continue
                    elif user_input.lower() == 'operations':
                        await self._show_operations()
                        continue
                    
                    # Process the request
                    print("🤖 Agent: Processing your request...")
                    result = await self.agent.process_user_request(user_input)
                    
                    if result["success"]:
                        print(f"🤖 Agent: {result['final_response']}")
                    else:
                        print(f"❌ Error: {result.get('error', 'Unknown error occurred')}")
                
                except KeyboardInterrupt:
                    print("\n👋 Goodbye!")
                    break
                except Exception as e:
                    logger.error(f"Error in interactive mode: {str(e)}")
                    print(f"❌ Error: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error running interactive mode: {str(e)}")
            print(f"❌ Fatal error: {str(e)}")
    
    async def run_single_request(self, user_input: str):
        """
        Run a single request and return the result.
        
        Args:
            user_input: The user's request
        """
        try:
            logger.info(f"Processing single request: {user_input}")
            result = await self.agent.process_user_request(user_input)
            
            if result["success"]:
                print(f"🤖 Response: {result['final_response']}")
                return result
            else:
                print(f"❌ Error: {result.get('error', 'Unknown error occurred')}")
                return result
                
        except Exception as e:
            logger.error(f"Error processing single request: {str(e)}")
            print(f"❌ Error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def _show_help(self):
        """Show help information."""
        help_text = """
Available Commands:
- help: Show this help message
- status: Show agent status and connection info
- operations: List available MCP operations
- quit/exit/q: Exit the application

Natural Language Examples:
- "Show me all products in the electronics category"
- "Check inventory for product ID 12345"
- "Create a new order for customer john@example.com"
- "What are the top-selling products this month?"
- "Update the price of product ABC123 to $29.99"
- "Find all orders with status 'pending'"
        """
        print(help_text)
    
    async def _show_status(self):
        """Show agent status."""
        try:
            is_connected = await self.agent.test_connection()
            print(f"🔗 MCP Server Connection: {'✅ Connected' if is_connected else '❌ Disconnected'}")
            print(f"🤖 Agent Status: {'✅ Ready' if self.agent else '❌ Not Initialized'}")
            
            if is_connected:
                operations = await self.agent.get_available_operations()
                if "error" not in operations:
                    print(f"📋 Available Tools: {operations.get('total_tools', 0)}")
                    print(f"📁 Available Resources: {operations.get('total_resources', 0)}")
                else:
                    print(f"⚠️  Could not retrieve operations: {operations['error']}")
        except Exception as e:
            print(f"❌ Error getting status: {str(e)}")
    
    async def _show_operations(self):
        """Show available MCP operations."""
        try:
            operations = await self.agent.get_available_operations()
            
            if "error" in operations:
                print(f"❌ Error: {operations['error']}")
                return
            
            print(f"\n📋 Available MCP Operations:")
            print(f"Tools: {operations.get('total_tools', 0)}")
            print(f"Resources: {operations.get('total_resources', 0)}")
            
            if operations.get('tools'):
                print("\n🔧 Tools:")
                for tool in operations['tools'][:10]:  # Show first 10 tools
                    name = tool.get('name', 'Unknown')
                    description = tool.get('description', 'No description')
                    print(f"  • {name}: {description}")
                if len(operations['tools']) > 10:
                    print(f"  ... and {len(operations['tools']) - 10} more tools")
            
            if operations.get('resources'):
                print("\n📁 Resources:")
                for resource in operations['resources'][:10]:  # Show first 10 resources
                    uri = resource.get('uri', 'Unknown')
                    name = resource.get('name', uri)
                    print(f"  • {name}: {uri}")
                if len(operations['resources']) > 10:
                    print(f"  ... and {len(operations['resources']) - 10} more resources")
                    
        except Exception as e:
            print(f"❌ Error getting operations: {str(e)}")
    
    async def shutdown(self):
        """Shutdown the agent."""
        try:
            if self.agent:
                await self.agent.shutdown()
            logger.info("Agent shutdown complete")
        except Exception as e:
            logger.error(f"Error during shutdown: {str(e)}")


async def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Storefront Agent - AI-powered storefront operations")
    parser.add_argument(
        "--mcp-url",
        type=str,
        help="MCP server URL (overrides config)"
    )
    parser.add_argument(
        "--request",
        type=str,
        help="Process a single request and exit"
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Run in interactive mode (default)"
    )
    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Set log level"
    )
    
    args = parser.parse_args()
    
    # Create and configure the CLI
    cli = StorefrontAgentCLI()
    
    # Override log level if specified
    if args.log_level:
        config.app.log_level = args.log_level
        cli.setup_logging()
    
    try:
        # Initialize the agent
        success = await cli.initialize(args.mcp_url)
        if not success:
            print("❌ Failed to initialize agent")
            sys.exit(1)
        
        # Run based on arguments
        if args.request:
            # Single request mode
            await cli.run_single_request(args.request)
        else:
            # Interactive mode (default)
            await cli.run_interactive()
    
    except KeyboardInterrupt:
        print("\n👋 Application interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        print(f"❌ Fatal error: {str(e)}")
        sys.exit(1)
    finally:
        await cli.shutdown()


def cli_main():
    """Synchronous entry point for the CLI command."""
    asyncio.run(main())


if __name__ == "__main__":
    asyncio.run(main())
