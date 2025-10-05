# Production Deployment Checklist

## Pre-Deployment Verification

### ✅ Environment Configuration
- [ ] `env.production` file is configured with correct values
- [ ] Azure OpenAI endpoint and API key are valid
- [ ] MCP server URL is accessible
- [ ] All environment variables are properly set

### ✅ Code Quality
- [ ] All test files removed
- [ ] No temporary scripts in root directory
- [ ] Production configuration verified
- [ ] Docker files are ready

### ✅ Testing
- [ ] Local production configuration test passed
- [ ] Web API health check working
- [ ] Tools endpoint returning correct data
- [ ] Chat endpoint processing requests correctly
- [ ] MCP server communication working

## Azure Container Apps Deployment

### 1. Build Docker Image
```bash
# Build the production web API image
docker build -f Dockerfile.api -t storefront-agent-api:production .

# Tag for Azure Container Registry (if using ACR)
docker tag storefront-agent-api:production your-registry.azurecr.io/storefront-agent-api:latest
```

### 2. Deploy to Azure Container Apps
```bash
# Using Azure CLI
az containerapp create \
  --name storefront-agent-api \
  --resource-group your-resource-group \
  --environment your-container-apps-env \
  --image your-registry.azurecr.io/storefront-agent-api:latest \
  --target-port 8000 \
  --ingress external \
  --env-vars ENVIRONMENT=production \
  --secrets azure-openai-key=your-api-key \
  --secret-env-vars AZURE_OPENAI_API_KEY=azure-openai-key
```

### 3. Configure Environment Variables
- `ENVIRONMENT=production`
- `AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/`
- `AZURE_OPENAI_API_KEY=your-api-key`
- `AZURE_OPENAI_DEPLOYMENT_NAME=gpt-5-nano`
- `MCP_SERVER_URL=https://your-mcp-server.azurecontainerapps.io`

### 4. Verify Deployment
```bash
# Check health
curl https://your-app.azurecontainerapps.io/health

# Test chat endpoint
curl -X POST https://your-app.azurecontainerapps.io/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Search for products", "session_id": "test"}'
```

## Post-Deployment Monitoring

### Health Checks
- [ ] `/health` endpoint responding
- [ ] Agent connected to MCP server
- [ ] All tools available
- [ ] Azure LLM connection working

### Performance Monitoring
- [ ] Response times acceptable
- [ ] Memory usage within limits
- [ ] CPU usage stable
- [ ] No memory leaks

### Log Monitoring
- [ ] Application logs accessible
- [ ] Error logs being captured
- [ ] MCP communication logs visible
- [ ] LLM request/response logs available

## Chat MFE Integration

### REST API Integration
```javascript
const response = await fetch('https://your-app.azurecontainerapps.io/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ 
    message: 'Search for products', 
    session_id: 'user123' 
  })
});
```

### Server-Sent Events Integration
```javascript
const eventSource = new EventSource(
  'https://your-app.azurecontainerapps.io/sse/chat?session_id=user123'
);
eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Response:', data);
};
```

## Troubleshooting

### Common Issues
1. **Health Check Failing**: Check environment variables and MCP server connectivity
2. **Azure LLM Errors**: Verify API key and endpoint configuration
3. **MCP Server Timeouts**: Check network connectivity and server status
4. **Memory Issues**: Monitor container resource usage

### Debug Commands
```bash
# Check container logs
az containerapp logs show --name storefront-agent-api --resource-group your-rg

# Check environment variables
az containerapp show --name storefront-agent-api --resource-group your-rg --query properties.configuration.ingress

# Restart container
az containerapp restart --name storefront-agent-api --resource-group your-rg
```

## Security Considerations

- [ ] API keys stored as secrets, not environment variables
- [ ] HTTPS enabled for all endpoints
- [ ] CORS configured appropriately
- [ ] Rate limiting implemented (if needed)
- [ ] Input validation on all endpoints

## Backup and Recovery

- [ ] Configuration backed up
- [ ] Docker images tagged and stored
- [ ] Environment variables documented
- [ ] Recovery procedures documented
