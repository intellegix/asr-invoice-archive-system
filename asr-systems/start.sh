#!/bin/bash

echo ""
echo "============================================================"
echo "  ASR Invoice Archive System - Production Server"
echo "============================================================"
echo ""

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python3 is not installed"
    echo "Please install Python 3.11 or later"
    exit 1
fi

# Check Python version
PYVER=$(python3 --version 2>&1 | cut -d' ' -f2)
echo "Found Python $PYVER"

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
    pip install -r production-server/requirements.txt
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
    python -m uvicorn production-server.api.main:app --host 0.0.0.0 --port 8000
fi

if [ $? -ne 0 ]; then
    echo ""
    echo "Server exited with error. Check logs for details."
    read -p "Press Enter to continue..."
fi
