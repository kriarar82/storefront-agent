"""Main application entry point for the Storefront Agent.

This is a simple wrapper that imports and runs the CLI.
For the full CLI implementation, see src/storefront_agent/cli.py
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from storefront_agent.cli import main

if __name__ == "__main__":
    asyncio.run(main())
