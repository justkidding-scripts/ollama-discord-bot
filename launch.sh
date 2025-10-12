#!/bin/bash

# Advanced Discord Bot Launcher Startup Script
# This script handles virtual environment setup and dependency installation

LAUNCHER_DIR="/home/nike/clean-discord-bot"
VENV_DIR="$LAUNCHER_DIR/launcher_env"

cd "$LAUNCHER_DIR"

echo "🚀 Discord Bot Launcher System"
echo "=============================="

# Check if virtual environment exists
if [ ! -d "$VENV_DIR" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

# Activate virtual environment
echo "⚡ Activating virtual environment..."
source "$VENV_DIR/bin/activate"

# Check and install dependencies
echo "🔧 Installing dependencies..."
pip install --quiet rich GitPython pyyaml aiohttp

# Run the launcher
echo "🚀 Starting Bot Launcher..."
echo ""

python3 bot_launcher.py "$@"