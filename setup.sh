#!/bin/bash
# Quick setup script for TwinShip Ontology development
# This script helps you get started quickly with uv

set -e

echo "════════════════════════════════════════════════════════════"
echo "  TwinShip Ontology - Quick Setup"
echo "════════════════════════════════════════════════════════════"
echo ""

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ uv is not installed"
    echo ""
    echo "Install uv using one of these methods:"
    echo ""
    echo "  # Recommended (macOS/Linux):"
    echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"
    echo ""
    echo "  # Or with Homebrew:"
    echo "  brew install uv"
    echo ""
    echo "  # Or with pip:"
    echo "  pip install uv"
    echo ""
    exit 1
fi

echo "✓ uv is installed: $(uv --version)"
echo ""

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python version: $PYTHON_VERSION"
echo ""

# Install dependencies
echo "Installing dependencies with uv..."
uv sync

if [ $? -eq 0 ]; then
    echo ""
    echo "════════════════════════════════════════════════════════════"
    echo "✓ Setup Complete!"
    echo "════════════════════════════════════════════════════════════"
    echo ""
    echo "Next steps:"
    echo ""
    echo "  1. Activate the virtual environment:"
    echo "     source .venv/bin/activate"
    echo ""
    echo "  2. Generate complete website:"
    echo "     ./scripts/generate_website.sh"
    echo ""
    echo "  3. Or run individual scripts:"
    echo "     python scripts/merge_modules.py --help"
    echo "     python scripts/generate_widoco_docs.py --help"
    echo ""
    echo "  4. View documentation:"
    echo "     open docs/WEBSITE_GENERATION.md"
    echo "     open docs/PYTHON_SETUP.md"
    echo ""
    echo "Enjoy working with TwinShip Ontology! 🚢"
    echo ""
else
    echo ""
    echo "❌ Setup failed. Please check the error messages above."
    exit 1
fi
