#!/bin/bash
set -e

cd "$(dirname "$0")"

echo "=== GhostHacker Image Gen Setup ==="
echo "Device: Apple Silicon (MPS)"
echo "Model: AnimagineXL 4.0"
echo ""

# Create virtual environment
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
else
    echo "Virtual environment already exists."
fi

# Activate
source .venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "=== Setup complete ==="
echo ""
echo "To start the server:"
echo "  cd apps/image-gen"
echo "  source .venv/bin/activate"
echo "  python app.py"
echo ""
echo "The model (~6GB) will be downloaded on first run."
echo "Server will be available at http://localhost:8100"
