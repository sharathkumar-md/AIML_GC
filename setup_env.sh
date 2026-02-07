#!/bin/bash
# Setup script for Kelp Automated Deal Flow project
# AI-ML GC 2025-26

echo "=========================================="
echo " Kelp Automated Deal Flow - Environment Setup"
echo "=========================================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python3 is not installed"
    echo "Please install Python 3.10+ first"
    exit 1
fi

# Create virtual environment
echo "[1/4] Creating virtual environment..."
if [ -d "venv" ]; then
    echo "Virtual environment already exists. Removing old one..."
    rm -rf venv
fi
python3 -m venv venv

# Activate virtual environment
echo "[2/4] Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "[3/4] Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "[4/4] Installing dependencies..."
pip install -r requirements.txt

echo ""
echo "=========================================="
echo " Setup Complete!"
echo "=========================================="
echo ""
echo "To activate the environment, run:"
echo "    source venv/bin/activate"
echo ""
echo "To run the pipeline:"
echo "    python src/main.py"
