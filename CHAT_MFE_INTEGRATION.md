# Chat MFE Integration Guide

This guide explains how the Chat MFE (Micro Frontend) can connect to the Storefront Agent API.

## 🏗️ Architecture Overview

```
┌─────────────────┐    HTTP/WebSocket    ┌──────────────────┐    MCP Protocol    ┌─────────────────┐
│   Chat MFE      │ ──────────────────► │ Storefront Agent │ ─────────────────► │   MCP Server    │
│                 │                      │      API         │                    │                 │
└─────────────────┘                      └──────────────────┘                    └─────────────────┘
```

## 🚀 Quick Start

### 1. Start the Storefront Agent API

```bash
# Using Python directly
source venv/bin/activate
python run_api.py

# Using Docker
docker-compose -f docker-compose.api.yml up -d
```

The API will be available at `http://localhost:8000`

### 2. Test the Connection

```bash
# Test REST API
python test_chat_mfe_client.py

# Test health check
curl http://localhost:8000/health
```

## 📡 API Endpoints

### REST API Endpoints

| Endpoint | Method | Description | Request Body | Response |
|----------|--------|-------------|--------------|----------|
| `/health` | GET | Health check | None | `HealthResponse` |
| `/chat` | POST | Send chat message | `ChatRequest` | `ChatResponse` |
| `/tools` | GET | Get available tools | None | `ToolsResponse` |
| `/servers` | GET | Get MCP server info | None | `ServersResponse` |
| `/reconnect` | POST | Reconnect to MCP | None | `ReconnectResponse` |

### WebSocket Endpoint

| Endpoint | Protocol | Description |
|----------|----------|-------------|
| `/ws/chat` | WebSocket | Real-time chat communication |

## 🔧 Integration Methods

### Method 1: REST API (Recommended for Simple Integration)

```javascript
// Chat MFE JavaScript Example
class StorefrontAgentClient {
    constructor(apiUrl = 'http://localhost:8000') {
        this.apiUrl = apiUrl;
        this.sessionId = null;
    }
    
    async sendMessage(message, userId = null) {
        try {
            const response = await fetch(`${this.apiUrl}/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    session_id: this.sessionId,
                    user_id: userId
                })
            });
            
            const result = await response.json();
            
            // Store session ID for conversation continuity
            if (result.session_id) {
                this.sessionId = result.session_id;
            }
            
            return result;
        } catch (error) {
            return {
                response: `Error: ${error.message}`,
                success: false,
                error: error.message
            };
        }
    }
    
    async checkHealth() {
        try {
            const response = await fetch(`${this.apiUrl}/health`);
            return await response.json();
        } catch (error) {
            return { status: 'unhealthy', error: error.message };
        }
    }
}

// Usage
const agent = new StorefrontAgentClient();

// Send a message
const result = await agent.sendMessage("Show me all product categories");
if (result.success) {
    console.log("Agent:", result.response);
} else {
    console.error("Error:", result.error);
}
```

### Method 2: WebSocket (Recommended for Real-time Chat)

```javascript
// Chat MFE WebSocket Example
class StorefrontAgentWebSocket {
    constructor(apiUrl = 'ws://localhost:8000') {
        this.apiUrl = apiUrl;
        this.ws = null;
        this.sessionId = null;
    }
    
    connect() {
        return new Promise((resolve, reject) => {
            this.ws = new WebSocket(`${this.apiUrl}/ws/chat`);
            
            this.ws.onopen = () => {
                console.log('Connected to Storefront Agent');
                resolve();
            };
            
            this.ws.onmessage = (event) => {
                const result = JSON.parse(event.data);
                
                // Store session ID
                if (result.session_id) {
                    this.sessionId = result.session_id;
                }
                
                // Handle the response
                this.onMessage(result);
            };
            
            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                reject(error);
            };
            
            this.ws.onclose = () => {
                console.log('Disconnected from Storefront Agent');
            };
        });
    }
    
    sendMessage(message, userId = null) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({
                message: message,
                session_id: this.sessionId,
                user_id: userId
            }));
        } else {
            console.error('WebSocket not connected');
        }
    }
    
    onMessage(result) {
        // Override this method to handle responses
        if (result.success) {
            console.log('Agent:', result.response);
        } else {
            console.error('Error:', result.error);
        }
    }
    
    disconnect() {
        if (this.ws) {
            this.ws.close();
        }
    }
}

// Usage
const agent = new StorefrontAgentWebSocket();

agent.connect().then(() => {
    agent.sendMessage("Hello! Can you help me with storefront operations?");
});

// Handle responses
agent.onMessage = (result) => {
    if (result.success) {
        // Display the response in your chat UI
        displayMessage(result.response, 'agent');
    } else {
        // Display error message
        displayMessage(`Error: ${result.error}`, 'error');
    }
};
```

## 📋 Request/Response Models

### ChatRequest
```json
{
    "message": "Show me all product categories",
    "session_id": "optional-session-id",
    "user_id": "optional-user-id"
}
```

### ChatResponse
```json
{
    "response": "Here are all the product categories...",
    "success": true,
    "session_id": "generated-session-id",
    "error": null,
    "mcp_details": {
        "server_used": "storefront",
        "tool_called": "get_categories",
        "confidence": 0.95,
        "reasoning": "User is asking for product categories...",
        "success": true
    }
}
```

### HealthResponse
```json
{
    "status": "healthy",
    "agent_connected": true,
    "mcp_servers": 1,
    "available_tools": 4
}
```

## 🔒 Security Considerations

### CORS Configuration
The API includes CORS middleware, but for production:

```python
# In web_api.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-chat-mfe-domain.com"],  # Specific domains
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

### Authentication (Optional)
Add authentication middleware if needed:

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer

security = HTTPBearer()

async def verify_token(token: str = Depends(security)):
    # Implement your token verification logic
    if not verify_user_token(token.credentials):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    return token

# Apply to endpoints
@app.post("/chat")
async def chat(request: ChatRequest, token = Depends(verify_token)):
    # ... existing code
```

## 🚀 Deployment

### Docker Deployment
```bash
# Build and run with Docker Compose
docker-compose -f docker-compose.api.yml up -d

# Check logs
docker-compose -f docker-compose.api.yml logs -f
```

### Environment Variables
```bash
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=false

# Storefront Agent Configuration
ENVIRONMENT=production
AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-5-nano
MCP_SERVER_URL=https://your-mcp-server.azurecontainerapps.io
```

## 🧪 Testing

### Manual Testing
```bash
# Test health check
curl http://localhost:8000/health

# Test chat
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Show me all product categories"}'

# Test tools
curl http://localhost:8000/tools
```

### Automated Testing
```bash
# Run the test client
python test_chat_mfe_client.py
```

## 📊 Monitoring

### Health Check
Monitor the `/health` endpoint to ensure the service is running:

```javascript
// Health check in Chat MFE
async function checkAgentHealth() {
    try {
        const response = await fetch('/health');
        const health = await response.json();
        
        if (health.status === 'healthy') {
            console.log('Storefront Agent is healthy');
            return true;
        } else {
            console.error('Storefront Agent is unhealthy');
            return false;
        }
    } catch (error) {
        console.error('Health check failed:', error);
        return false;
    }
}

// Check every 30 seconds
setInterval(checkAgentHealth, 30000);
```

### Logging
The API includes comprehensive logging. Check logs for:
- Request/response details
- MCP server communication
- Error tracking
- Performance metrics

## 🔧 Troubleshooting

### Common Issues

1. **Connection Refused**
   - Ensure the API server is running
   - Check the port (default: 8000)
   - Verify firewall settings

2. **CORS Errors**
   - Update CORS configuration in `web_api.py`
   - Ensure correct origin URLs

3. **MCP Server Errors**
   - Check MCP server connectivity
   - Verify environment variables
   - Check logs for detailed error messages

4. **Authentication Errors**
   - Verify API keys and endpoints
   - Check Azure OpenAI configuration

### Debug Mode
Enable debug logging:

```python
# In run_api.py
uvicorn.run(
    app,
    host=host,
    port=port,
    reload=reload,
    log_level="debug"  # Change to debug
)
```

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [WebSocket Guide](https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API)
- [CORS Configuration](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS)
- [Storefront Agent Documentation](./README.md)

## 🎯 Next Steps

1. **Implement in Chat MFE**: Choose REST API or WebSocket based on your needs
2. **Add Authentication**: Implement proper authentication if required
3. **Configure CORS**: Update CORS settings for your domain
4. **Monitor Performance**: Set up monitoring and alerting
5. **Scale as Needed**: Consider load balancing for high traffic

The Storefront Agent API provides a robust foundation for Chat MFE integration with full MCP server support and intelligent request routing.
