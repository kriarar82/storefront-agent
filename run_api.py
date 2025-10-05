#!/usr/bin/env python3
"""Run the Storefront Agent Web API."""

import os
import sys
import uvicorn
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from storefront_agent.web_api import app


def main():
    """Main function to run the API server."""
    print("🚀 Starting Storefront Agent Web API")
    print("=" * 50)
    
    # Configuration
    port = int(os.getenv("API_PORT", 8000))
    host = os.getenv("API_HOST", "0.0.0.0")
    reload = os.getenv("API_RELOAD", "true").lower() == "true"
    
    print(f"🌐 Host: {host}")
    print(f"🔌 Port: {port}")
    print(f"🔄 Reload: {reload}")
    print()
    print("📋 Available endpoints:")
    print(f"   • Health Check: http://{host}:{port}/health")
    print(f"   • Chat (REST): http://{host}:{port}/chat")
    print(f"   • Tools: http://{host}:{port}/tools")
    print(f"   • Servers: http://{host}:{port}/servers")
    print(f"   • WebSocket: ws://{host}:{port}/ws/chat")
    print(f"   • SSE Stream: http://{host}:{port}/sse/chat")
    print(f"   • SSE Message: http://{host}:{port}/sse/chat/{{session_id}}/message")
    print()
    print("🎯 Chat MFE can connect to:")
    print(f"   • REST API: http://{host}:{port}/chat")
    print(f"   • WebSocket: ws://{host}:{port}/ws/chat")
    print(f"   • Server-Sent Events: http://{host}:{port}/sse/chat")
    print()
    
    # Start the server
    uvicorn.run(
        "src.storefront_agent.web_api:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )


if __name__ == "__main__":
    main()
