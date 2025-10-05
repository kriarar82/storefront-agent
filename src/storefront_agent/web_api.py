"""Web API for the Storefront Agent to communicate with Chat MFE."""

import asyncio
import json
import os
import uuid
from typing import Dict, Any, Optional, List
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
from loguru import logger

# Set environment before importing config
os.environ["ENVIRONMENT"] = "production"

from .storefront_agent import StorefrontAgent
from .config import config


# Global agent instance
agent: Optional[StorefrontAgent] = None

# Active SSE connections
active_sse_connections: Dict[str, asyncio.Queue] = {}


class ChatRequest(BaseModel):
    """Request model for chat messages."""
    message: str
    session_id: Optional[str] = None
    user_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Response model for chat messages."""
    response: str
    success: bool
    session_id: Optional[str] = None
    error: Optional[str] = None
    mcp_details: Optional[Dict[str, Any]] = None


class SSEEvent(BaseModel):
    """SSE event model."""
    event: str
    data: Dict[str, Any]
    id: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    agent_connected: bool
    mcp_servers: int
    available_tools: int


# Create FastAPI app
app = FastAPI(
    title="Storefront Agent API",
    description="API for Chat MFE to communicate with Storefront Agent",
    version="1.0.0"
)

# Add CORS middleware for Chat MFE
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def get_agent() -> StorefrontAgent:
    """Get or create the global agent instance."""
    global agent
    if agent is None:
        logger.info("Initializing Storefront Agent...")
        
        # Ensure production environment is set
        os.environ["ENVIRONMENT"] = "production"
        
        # Use the configured MCP server URL
        from .config import config
        mcp_server_url = config.mcp.server_url
        logger.info(f"Using MCP server URL: {mcp_server_url}")
        
        agent = StorefrontAgent(mcp_server_url)
        initialized = await agent.initialize()
        if not initialized:
            raise HTTPException(status_code=500, detail="Failed to initialize Storefront Agent")
        logger.info("Storefront Agent initialized successfully")
    return agent


@app.on_event("startup")
async def startup_event():
    """Initialize the agent on startup."""
    try:
        await get_agent()
        logger.info("Storefront Agent API started successfully")
    except Exception as e:
        logger.error(f"Failed to start Storefront Agent API: {str(e)}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    global agent
    if agent:
        await agent.shutdown()
        agent = None
        logger.info("Storefront Agent API shutdown complete")


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    try:
        agent_instance = await get_agent()
        
        # Get agent status
        is_connected = await agent_instance.test_connection()
        operations = await agent_instance.get_available_operations()
        
        return HealthResponse(
            status="healthy" if is_connected else "unhealthy",
            agent_connected=is_connected,
            mcp_servers=operations.get("total_servers", 0),
            available_tools=operations.get("total_tools", 0)
        )
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return HealthResponse(
            status="unhealthy",
            agent_connected=False,
            mcp_servers=0,
            available_tools=0
        )


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, background_tasks: BackgroundTasks):
    """Main chat endpoint for the Chat MFE."""
    try:
        logger.info(f"Received chat request: {request.message[:100]}...")
        
        # Get agent instance
        agent_instance = await get_agent()
        
        # Process the user request
        result = await agent_instance.process_user_request(request.message)
        
        if result.get("success"):
            response_text = result.get("final_response", "I'm sorry, I couldn't process your request.")
            
            # Extract MCP details for debugging/transparency
            mcp_details = None
            if result.get("mcp_result"):
                mcp_result = result["mcp_result"]
                mcp_details = {
                    "server_used": mcp_result.get("server_name"),
                    "tool_called": mcp_result.get("tool_name"),
                    "confidence": mcp_result.get("selection", {}).get("confidence"),
                    "reasoning": mcp_result.get("selection", {}).get("reasoning"),
                    "success": mcp_result.get("success")
                }
            
            return ChatResponse(
                response=response_text,
                success=True,
                session_id=request.session_id,
                mcp_details=mcp_details
            )
        else:
            error_msg = result.get("error", "Unknown error occurred")
            logger.error(f"Chat request failed: {error_msg}")
            
            return ChatResponse(
                response=f"I'm sorry, I encountered an error: {error_msg}",
                success=False,
                session_id=request.session_id,
                error=error_msg
            )
            
    except Exception as e:
        logger.error(f"Chat endpoint error: {str(e)}")
        return ChatResponse(
            response="I'm sorry, I encountered an unexpected error. Please try again.",
            success=False,
            session_id=request.session_id,
            error=str(e)
        )


@app.get("/tools")
async def get_available_tools():
    """Get available tools from the MCP server."""
    try:
        agent_instance = await get_agent()
        operations = await agent_instance.get_available_operations()
        
        if "error" in operations:
            raise HTTPException(status_code=500, detail=operations["error"])
        
        return {
            "tools": operations.get("tools", []),
            "servers": operations.get("servers", {}),
            "total_tools": operations.get("total_tools", 0),
            "total_servers": operations.get("total_servers", 0)
        }
        
    except Exception as e:
        logger.error(f"Get tools error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/servers")
async def get_mcp_servers():
    """Get information about MCP servers."""
    try:
        agent_instance = await get_agent()
        operations = await agent_instance.get_available_operations()
        
        if "error" in operations:
            raise HTTPException(status_code=500, detail=operations["error"])
        
        return {
            "servers": operations.get("servers", {}),
            "total_servers": operations.get("total_servers", 0),
            "connected_servers": operations.get("connected_servers", 0)
        }
        
    except Exception as e:
        logger.error(f"Get servers error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/reconnect")
async def reconnect_agent():
    """Reconnect to MCP servers."""
    try:
        global agent
        if agent:
            await agent.shutdown()
            agent = None
        
        # Reinitialize agent
        agent = StorefrontAgent()
        initialized = await agent.initialize()
        
        if initialized:
            return {"message": "Agent reconnected successfully", "success": True}
        else:
            raise HTTPException(status_code=500, detail="Failed to reconnect agent")
            
    except Exception as e:
        logger.error(f"Reconnect error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Server-Sent Events endpoint for real-time chat
@app.get("/sse/chat")
async def sse_chat(request: Request, session_id: Optional[str] = None):
    """Server-Sent Events endpoint for real-time chat."""
    if not session_id:
        session_id = str(uuid.uuid4())
    
    # Create a queue for this connection
    queue = asyncio.Queue()
    active_sse_connections[session_id] = queue
    
    async def event_generator():
        """Generate SSE events."""
        try:
            # Send initial connection event
            yield f"event: connected\ndata: {json.dumps({'session_id': session_id, 'message': 'Connected to Storefront Agent'})}\n\n"
            
            # Keep connection alive and process events
            while True:
                try:
                    # Wait for events in the queue
                    event = await asyncio.wait_for(queue.get(), timeout=30.0)
                    
                    # Format as SSE
                    sse_data = f"event: {event['event']}\ndata: {json.dumps(event['data'])}\n"
                    if event.get('id'):
                        sse_data += f"id: {event['id']}\n"
                    sse_data += "\n"
                    
                    yield sse_data
                    
                except asyncio.TimeoutError:
                    # Send keepalive
                    yield f"event: keepalive\ndata: {json.dumps({'timestamp': asyncio.get_event_loop().time()})}\n\n"
                except Exception as e:
                    logger.error(f"SSE event generation error: {str(e)}")
                    break
                    
        except Exception as e:
            logger.error(f"SSE connection error: {str(e)}")
        finally:
            # Clean up connection
            if session_id in active_sse_connections:
                del active_sse_connections[session_id]
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control"
        }
    )


@app.post("/sse/chat/{session_id}/message")
async def send_sse_message(session_id: str, request: ChatRequest):
    """Send a message to an SSE connection."""
    try:
        if session_id not in active_sse_connections:
            raise HTTPException(status_code=404, detail="SSE connection not found")
        
        # Get agent instance
        agent_instance = await get_agent()
        
        # Send processing event
        processing_event = {
            "event": "processing",
            "data": {
                "message": request.message,
                "status": "processing",
                "timestamp": asyncio.get_event_loop().time()
            },
            "id": str(uuid.uuid4())
        }
        await active_sse_connections[session_id].put(processing_event)
        
        # Process the message
        result = await agent_instance.process_user_request(request.message)
        
        # Send response event
        response_event = {
            "event": "response",
            "data": {
                "response": result.get("final_response", "I'm sorry, I couldn't process your request."),
                "success": result.get("success", False),
                "session_id": session_id,
                "error": result.get("error"),
                "mcp_details": result.get("mcp_result"),
                "timestamp": asyncio.get_event_loop().time()
            },
            "id": str(uuid.uuid4())
        }
        await active_sse_connections[session_id].put(response_event)
        
        return {"message": "Message sent successfully", "session_id": session_id}
        
    except Exception as e:
        logger.error(f"SSE message error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/sse/chat/{session_id}")
async def close_sse_connection(session_id: str):
    """Close an SSE connection."""
    try:
        if session_id in active_sse_connections:
            # Send close event
            close_event = {
                "event": "closed",
                "data": {
                    "message": "Connection closed",
                    "timestamp": asyncio.get_event_loop().time()
                },
                "id": str(uuid.uuid4())
            }
            await active_sse_connections[session_id].put(close_event)
            
            # Remove connection
            del active_sse_connections[session_id]
            
        return {"message": "Connection closed", "session_id": session_id}
        
    except Exception as e:
        logger.error(f"SSE close error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# WebSocket endpoint for real-time chat (optional)
@app.websocket("/ws/chat")
async def websocket_chat(websocket):
    """WebSocket endpoint for real-time chat."""
    await websocket.accept()
    
    try:
        agent_instance = await get_agent()
        
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Process the message
            result = await agent_instance.process_user_request(message_data.get("message", ""))
            
            # Send response back
            response = {
                "response": result.get("final_response", "I'm sorry, I couldn't process your request."),
                "success": result.get("success", False),
                "mcp_details": result.get("mcp_result")
            }
            
            await websocket.send_text(json.dumps(response))
            
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        await websocket.close()


if __name__ == "__main__":
    import uvicorn
    
    # Get configuration
    port = int(os.getenv("API_PORT", 8000))
    host = os.getenv("API_HOST", "0.0.0.0")
    
    logger.info(f"Starting Storefront Agent API on {host}:{port}")
    
    uvicorn.run(
        "web_api:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )
