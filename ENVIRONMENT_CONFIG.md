# Multi-Environment Configuration Guide

This document explains how the Storefront Agent handles different environments (development, staging, production, testing) with their respective configurations.

## Overview

The application now supports multiple environments with environment-specific configurations for:
- Azure OpenAI endpoints and API keys
- MCP server URLs
- Log levels and debugging settings
- Timeout and retry configurations

## Environment Structure

### Supported Environments

1. **Development** (`development`)
   - Local development setup
   - Debug mode enabled
   - Local MCP server (ws://localhost:8080)
   - Detailed logging

2. **Staging** (`staging`)
   - Pre-production testing
   - Staging Azure resources
   - Staging MCP server (wss://mcp-staging.azurewebsites.net)
   - Standard logging

3. **Production** (`production`)
   - Live production environment
   - Production Azure resources
   - Production MCP server (wss://mcp-prod.azurewebsites.net)
   - Minimal logging, higher reliability

4. **Testing** (`testing`)
   - Automated testing environment
   - Test-specific configurations
   - Isolated test resources

## Configuration Files

### Environment-Specific Files

```
env.development    # Development environment settings
env.staging        # Staging environment settings
env.production     # Production environment settings
```

### Example Configuration Files

#### Development (`env.development`)
```bash
ENVIRONMENT=development
AZURE_OPENAI_ENDPOINT=https://your-dev-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-dev-api-key-here
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-5-nano
MCP_SERVER_URL=ws://localhost:8080
LOG_LEVEL=DEBUG
DEBUG=true
```

#### Staging (`env.staging`)
```bash
ENVIRONMENT=staging
AZURE_OPENAI_ENDPOINT=https://your-staging-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-staging-api-key-here
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-5-nano-staging
MCP_SERVER_URL=wss://mcp-staging.azurewebsites.net
LOG_LEVEL=INFO
DEBUG=false
```

#### Production (`env.production`)
```bash
ENVIRONMENT=production
AZURE_OPENAI_ENDPOINT=https://your-prod-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-prod-api-key-here
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-5-nano-prod
MCP_SERVER_URL=wss://mcp-prod.azurewebsites.net
LOG_LEVEL=WARNING
DEBUG=false
```

## Usage

### 1. Setting Environment

#### Method 1: Environment Variable
```bash
export ENVIRONMENT=production
python your_script.py
```

#### Method 2: Command Line
```bash
python load_config.py production
```

#### Method 3: In Code
```python
import os
os.environ['ENVIRONMENT'] = 'production'
from storefront_agent.config import config
```

### 2. Loading Configuration

```python
from storefront_agent.environments import load_environment_config, Environment

# Auto-detect environment
config = load_environment_config()

# Specify environment
config = load_environment_config(Environment.PRODUCTION)

# Get specific configurations
azure_config = config.get_azure_config()
mcp_config = config.get_mcp_config()
app_config = config.get_app_config()
```

### 3. Using in Application

```python
from storefront_agent.config import config

# Configuration is automatically loaded based on ENVIRONMENT variable
print(f"Azure Endpoint: {config.azure.endpoint}")
print(f"MCP Server: {config.mcp.server_url}")
print(f"Log Level: {config.app.log_level}")
```

## Docker Deployment

### Development
```bash
# Uses docker-compose.override.yml automatically
docker-compose up -d
```

### Staging
```bash
docker-compose -f docker-compose.staging.yml up -d
```

### Production
```bash
docker-compose -f docker-compose.production.yml up -d
```

## Deployment Script

Use the deployment script for automated deployments:

```bash
# Deploy to development
python deploy.py development

# Deploy to staging with tests
python deploy.py staging --test

# Deploy to production
python deploy.py production

# Build only (no deployment)
python deploy.py production --build-only

# Deploy to Azure (when implemented)
python deploy.py production --method azure
```

## Configuration Priority

The configuration system follows this priority order:

1. **Environment-specific config** (from `env.{environment}` file)
2. **Environment variables** (from system environment)
3. **Default values** (hardcoded in code)

## Environment-Specific Features

### Development
- Debug mode enabled
- Detailed logging
- Local MCP server
- Hot reloading (if using Docker volumes)
- Lower timeouts for faster feedback

### Staging
- Production-like configuration
- Staging Azure resources
- Staging MCP server
- Standard logging
- Integration testing

### Production
- Optimized for reliability
- Production Azure resources
- Production MCP server
- Minimal logging
- Higher timeouts and retry counts
- Resource limits

### Testing
- Isolated test resources
- Fast timeouts
- Debug logging
- Test-specific MCP server port

## Security Considerations

### Environment Variables
- Never commit API keys to version control
- Use Azure Key Vault for production secrets
- Rotate keys regularly
- Use different keys for each environment

### File Permissions
```bash
# Secure environment files
chmod 600 env.*
```

### Docker Secrets
For production, consider using Docker secrets:
```yaml
services:
  storefront-agent:
    secrets:
      - azure_api_key
      - mcp_server_key
```

## Troubleshooting

### Common Issues

1. **Environment not detected**
   ```bash
   export ENVIRONMENT=development
   ```

2. **Configuration file not found**
   - Ensure `env.{environment}` file exists
   - Check file permissions

3. **Docker compose file not found**
   - Use correct compose file for environment
   - Check file exists in project root

4. **Azure connection failed**
   - Verify endpoint URL format
   - Check API key validity
   - Ensure deployment exists

### Debug Configuration

```python
from storefront_agent.environments import load_environment_config

config = load_environment_config()
print("Full config:", config.get_config())
print("Azure config:", config.get_azure_config())
print("MCP config:", config.get_mcp_config())
```

## Best Practices

1. **Environment Isolation**
   - Use separate Azure resources for each environment
   - Use different MCP server instances
   - Isolate databases and storage

2. **Configuration Management**
   - Keep sensitive data in environment variables
   - Use configuration validation
   - Document all configuration options

3. **Deployment**
   - Test in staging before production
   - Use blue-green deployments
   - Monitor deployments

4. **Monitoring**
   - Set up environment-specific monitoring
   - Use different log levels per environment
   - Monitor resource usage

## Migration from Single Environment

If you're migrating from the previous single-environment setup:

1. **Create environment files** based on your current `.env`
2. **Update deployment scripts** to use environment-specific configs
3. **Test each environment** thoroughly
4. **Update CI/CD pipelines** to use the new configuration system

## Example Workflow

```bash
# 1. Set up development
cp env_example.txt env.development
# Edit env.development with your dev settings

# 2. Test configuration
python load_config.py development

# 3. Run tests
ENVIRONMENT=development python test_azure_mcp_integration.py

# 4. Deploy to staging
python deploy.py staging --test

# 5. Deploy to production
python deploy.py production
```

This multi-environment configuration system provides flexibility, security, and maintainability for your Storefront Agent deployments across different environments.

