# Storefront Agent Documentation

This directory contains the documentation for the Storefront Agent project.

## Structure

- `README.md` - This file
- `api/` - API documentation (auto-generated)
- `examples/` - Detailed usage examples
- `deployment/` - Deployment guides
- `development/` - Development guides

## Building Documentation

To build the documentation locally:

```bash
# Install documentation dependencies
pip install -e ".[docs]"

# Build HTML documentation
cd docs
make html

# Serve documentation locally
python -m http.server 8000
```

## Documentation Contents

### API Reference
- `storefront_agent.StorefrontAgent` - Main agent class
- `storefront_agent.AzureLLMClient` - Azure LLM client
- `storefront_agent.MCPClient` - MCP client
- `storefront_agent.config` - Configuration management

### Examples
- Basic usage examples
- Advanced configuration examples
- Integration examples
- Error handling examples

### Deployment
- Docker deployment
- Kubernetes deployment
- Environment configuration
- Production considerations

### Development
- Setting up development environment
- Running tests
- Contributing guidelines
- Code style guide
