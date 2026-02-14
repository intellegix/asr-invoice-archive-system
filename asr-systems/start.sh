#!/usr/bin/env bash
set -e

echo ""
echo "============================================================"
echo "  ASR Invoice Archive System - Production Server"
echo "============================================================"
echo ""

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed or not in PATH"
    echo "Please install Python 3.11 or later"
    exit 1
fi

# Check Python version (require 3.11+)
PYVER=$(python3 --version 2>&1 | cut -d' ' -f2)
PYMAJOR=$(echo "$PYVER" | cut -d. -f1)
PYMINOR=$(echo "$PYVER" | cut -d. -f2)

echo "Found Python $PYVER"

if [ "$PYMAJOR" -lt 3 ] || { [ "$PYMAJOR" -eq 3 ] && [ "$PYMINOR" -lt 11 ]; }; then
    echo "ERROR: Python 3.11+ is required (found $PYVER)"
    exit 1
fi

# Check for virtual environment
if [ -f "venv/bin/activate" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
else
    echo "WARNING: Virtual environment not found"
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate

    echo "Installing dependencies..."
    pip install -r production_server/requirements.txt
fi

# Check for .env file
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo "WARNING: .env file not found, copying from .env.example"
        cp .env.example .env
        echo "Please edit .env and set your ANTHROPIC_API_KEY"
        read -p "Press Enter to continue..."
    else
        echo "WARNING: No .env or .env.example found"
    fi
fi

# Check if start_server.py exists
if [ -f "start_server.py" ]; then
    echo ""
    echo "Starting ASR Production Server..."
    echo ""
    python start_server.py
else
    echo ""
    echo "Starting ASR Production Server via uvicorn..."
    echo ""
    python -m uvicorn production_server.api.main:app --host 0.0.0.0 --port 8000
fi
