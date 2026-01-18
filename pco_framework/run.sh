#!/bin/bash
# PCO Framework - Quick Start

cd "$(dirname "$0")"

echo "========================================"
echo "PCO Framework"
echo "Provably Compliant Outcomes"
echo "========================================"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: python3 not found"
    exit 1
fi

# Check Coq (optional)
if ! command -v coqc &> /dev/null; then
    echo "⚠️  Warning: coqc not found"
    echo "   Install: brew install coq"
    echo ""
fi

# Check dependencies
echo "Checking dependencies..."
python3 -c "import tkinter" 2>/dev/null || {
    echo "❌ Error: tkinter not installed"
    exit 1
}

python3 -c "import openai" 2>/dev/null || {
    echo "⚠️  Warning: openai package not installed"
    echo "   Install: pip install openai"
    echo ""
}

# Check API key
if [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️  Warning: OPENAI_API_KEY not set"
    echo "   You can enter it in the dashboard GUI"
    echo ""
fi

echo "✓ Starting dashboard..."
python3 dashboard.py
