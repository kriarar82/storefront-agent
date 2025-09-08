#!/bin/bash
# Activation script for Storefront Agent virtual environment

echo "🚀 Activating Storefront Agent virtual environment..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run 'python -m venv venv' first."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if package is installed
if ! python -c "import storefront_agent" 2>/dev/null; then
    echo "📦 Installing Storefront Agent package..."
    pip install -e .
fi

echo "✅ Virtual environment activated successfully!"
echo ""
echo "Available commands:"
echo "  python main.py                    # Run the agent"
echo "  storefront-agent                  # Run via CLI command"
echo "  python examples/example_usage.py  # Run examples"
echo "  make help                         # Show all available commands"
echo ""
echo "To deactivate, run: deactivate"
