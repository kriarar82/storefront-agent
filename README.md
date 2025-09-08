# Storefront Agent

An AI-powered agent that connects with Azure LLM and MCP (Model Context Protocol) servers to provide intelligent storefront operations through natural language processing.

## Features

- **Natural Language Processing**: Understands user requests in natural language
- **Azure LLM Integration**: Uses Azure OpenAI services for intelligent analysis
- **MCP Server Communication**: Connects to MCP servers for storefront operations
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
