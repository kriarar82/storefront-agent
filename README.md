# Storefront Agent

An AI-powered agent that connects with Azure LLM and MCP (Model Context Protocol) servers to provide intelligent storefront operations through natural language processing.

## Features

- **Natural Language Processing**: Understands user requests in natural language
- **Azure LLM Integration**: Uses Azure OpenAI services for intelligent analysis
- **MCP Server Communication**: Connects to MCP servers for storefront operations
- **Web API**: REST, WebSocket, and Server-Sent Events (SSE) endpoints
- **Multi-Environment Support**: Development, staging, and production configurations
- **Docker Support**: Containerized deployment with Docker and Docker Compose
- **Configurable Prompts**: Customizable system prompts and parameters
- **Interactive Mode**: Command-line interface for real-time interaction
- **Error Handling**: Comprehensive error handling and logging
- **Extensible**: Easy to extend with new MCP operations

## Architecture

```
User Input → Azure LLM → Intent Analysis → MCP Operations → Response Generation
```

1. **User Input**: Natural language request
2. **Azure LLM**: Analyzes intent and determines required operations
3. **MCP Client**: Executes operations on MCP servers
4. **Response**: User-friendly explanation of results

## Installation

### Option 1: Development Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd Storefront-Agent
```

2. Install in development mode:
```bash
make dev-install
# or
pip install -e ".[dev,test,docs]"
```

3. Create environment configuration:
```bash
make env-create
# or
cp env_example.txt .env
```

### Option 2: Production Installation

1. Install from source:
```bash
pip install .
```

2. Or install from PyPI (when published):
```bash
pip install storefront-agent
```

### Environment Configuration

Configure your environment variables in `.env`:
```env
# Azure Configuration
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key-here
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_DEPLOYMENT_NAME=your-deployment-name

# MCP Server Configuration
MCP_SERVER_URL=ws://localhost:8080
MCP_SERVER_TIMEOUT=30

# Application Configuration
LOG_LEVEL=INFO
MAX_RETRIES=3
```

## Usage

### Quick Start

```bash
# Run in interactive mode
make run
# or
python main.py
# or
storefront-agent

# Run a single request
python main.py --request "Show me all products in the electronics category"
# or
storefront-agent --request "Show me all products in the electronics category"
```

### Development Commands

```bash
# Run tests
make test

# Run tests with coverage
make test-cov

# Format code
make format

# Run linting
make lint

# Run all checks
make check

# Install development dependencies
make install-dev

# Build package
make build
```

### Command Line Options

```bash
python main.py --help
# or
storefront-agent --help
```

Available options:
- `--mcp-url`: Override MCP server URL
- `--request`: Process a single request
- `--interactive`: Run in interactive mode (default)
- `--log-level`: Set log level (DEBUG, INFO, WARNING, ERROR)

### Interactive Commands

When running in interactive mode, you can use these commands:

- `help`: Show available commands and examples
- `status`: Show agent status and connection info
- `operations`: List available MCP operations
- `quit`/`exit`/`q`: Exit the application

## Example Usage

### Product Management
```
👤 You: Show me all products in the electronics category
🤖 Agent: I'll search for all products in the electronics category for you...

👤 You: Update the price of product ABC123 to $29.99
🤖 Agent: I'll update the price of product ABC123 to $29.99...
```

### Inventory Management
```
👤 You: Check inventory for product ID 12345
🤖 Agent: Let me check the current inventory levels for product 12345...

👤 You: What products are low in stock?
🤖 Agent: I'll check for products with low inventory levels...
```

### Order Processing
```
👤 You: Create a new order for customer john@example.com
🤖 Agent: I'll help you create a new order for john@example.com...

👤 You: Find all orders with status 'pending'
🤖 Agent: I'll search for all pending orders...
```

## Configuration

### Azure LLM Configuration

The agent uses Azure OpenAI services. Configure the following parameters:

- `endpoint`: Your Azure OpenAI endpoint
- `api_key`: Your API key
- `api_version`: API version to use
- `deployment_name`: Your deployment name

### MCP Server Configuration

Configure your MCP server connection:

- `server_url`: WebSocket or HTTP URL of your MCP server
- `timeout`: Connection timeout in seconds

### Custom Prompts

You can customize the system prompts in `config.py`:

```python
# System prompt for the Storefront Agent
system_prompt = """You are a Storefront Agent..."""

# User prompt template for intent analysis
user_prompt_template = """User Request: {user_input}..."""
```

## MCP Server Integration

The agent communicates with MCP servers using the Model Context Protocol. It supports:

- **Tool Operations**: Call specific tools on the MCP server
- **Resource Operations**: Read and manage resources
- **Generic Operations**: Execute custom operations

### Supported MCP Operations

- Product catalog management
- Inventory management
- Order processing
- Customer management
- Analytics and reporting
- Store configuration

## Error Handling

The agent includes comprehensive error handling:

- **Connection Errors**: Handles MCP server connection issues
- **LLM Errors**: Manages Azure LLM API errors
- **Validation Errors**: Validates input and configuration
- **Retry Logic**: Automatic retry with exponential backoff

## Logging

The agent uses structured logging with multiple levels:

- **DEBUG**: Detailed debugging information
- **INFO**: General information about operations
- **WARNING**: Warning messages for non-critical issues
- **ERROR**: Error messages for failures

Logs are written to both console and `storefront_agent.log` file.

## Development

### Project Structure

```
Storefront-Agent/
├── src/
│   └── storefront_agent/
│       ├── __init__.py           # Package initialization
│       ├── cli.py                # Command-line interface
│       ├── storefront_agent.py   # Core Storefront Agent class
│       ├── azure_llm_client.py   # Azure LLM client
│       ├── mcp_client.py         # MCP client
│       ├── config.py             # Configuration management
│       └── utils.py              # Utility functions
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # Pytest configuration
│   ├── test_storefront_agent.py # Unit tests
│   └── test_installation.py     # Installation tests
├── examples/
│   └── example_usage.py         # Usage examples
├── docs/                        # Documentation
├── main.py                      # Simple entry point
├── setup.py                     # Package setup
├── pyproject.toml              # Modern Python packaging
├── requirements.txt            # Python dependencies
├── Makefile                    # Development commands
├── .pre-commit-config.yaml     # Pre-commit hooks
├── .gitignore                  # Git ignore rules
└── README.md                   # This file
```

### Adding New MCP Operations

1. Define the operation in your MCP server
2. Update the system prompt to include the new operation
3. The agent will automatically discover and use the new operation

### Customizing Responses

Modify the prompt templates in `config.py` to customize how the agent responds to users.

## Production Deployment

### Azure Container Apps Deployment

The Storefront Agent is designed for deployment on Azure Container Apps with production configuration.

#### Prerequisites

1. **Azure Container Apps Environment**: Set up Azure Container Apps
2. **Azure OpenAI Service**: Deploy GPT-5 Nano model
3. **MCP Server**: Deploy the storefront MCP server
4. **Environment Configuration**: Configure production environment variables

#### Environment Configuration

1. **Update Production Config** (`env.production`):
```bash
# Azure Configuration
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-5-nano

# MCP Server Configuration
MCP_SERVER_URL=https://your-mcp-server.azurecontainerapps.io
```

2. **Verify Configuration**:
```bash
# Test production configuration
ENVIRONMENT=production python -c "from src.storefront_agent.config import config; print(f'MCP URL: {config.mcp.server_url}')"
```

#### Docker Deployment

1. **Build Production Image**:
```bash
# Build the web API image
docker build -f Dockerfile.api -t storefront-agent-api:production .

# Or use Docker Compose
docker-compose -f docker-compose.production.api.yml build
```

2. **Run Production Container**:
```bash
# Using Docker Compose
docker-compose -f docker-compose.production.api.yml up -d

# Or run directly
docker run -d \
  --name storefront-agent-api \
  --env-file env.production \
  -p 8000:8000 \
  storefront-agent-api:production
```

#### Web API Endpoints

The production deployment exposes these endpoints:

- **Health Check**: `GET /health`
- **Chat (REST)**: `POST /chat`
- **Tools**: `GET /tools`
- **Servers**: `GET /servers`
- **WebSocket**: `ws://host:8000/ws/chat`
- **Server-Sent Events**: `GET /sse/chat`

#### Chat MFE Integration

The Chat MFE can connect using:

1. **REST API**:
```javascript
const response = await fetch('https://your-agent.azurecontainerapps.io/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ message: 'Search for products', session_id: 'user123' })
});
```

2. **Server-Sent Events**:
```javascript
const eventSource = new EventSource('https://your-agent.azurecontainerapps.io/sse/chat?session_id=user123');
eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Response:', data);
};
```

#### Monitoring and Logs

- **Health Check**: Monitor `/health` endpoint
- **Logs**: Check container logs for debugging
- **Metrics**: Monitor Azure Container Apps metrics

## Troubleshooting

### Common Issues

1. **Connection Failed**: Check your MCP server URL and ensure the server is running
2. **Azure LLM Error**: Verify your Azure credentials and endpoint configuration
3. **Invalid Response**: Check the MCP server response format

### Debug Mode

Run with debug logging to see detailed information:

```bash
python main.py --log-level DEBUG
```

### Testing Connection

Use the `status` command in interactive mode to test your connections:

```
👤 You: status
🤖 Agent: 🔗 MCP Server Connection: ✅ Connected
🤖 Agent: 🤖 Agent Status: ✅ Ready
```

## License

This project is licensed under the MIT License.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Support

For support and questions, please open an issue in the repository.
