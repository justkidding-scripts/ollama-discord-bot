#!/bin/bash

# Ultimate Research Bot Launcher
# Automatically sets up and activates virtual environment with all dependencies

set -e

echo "🚀 Starting Ultimate Research Bot..."

# Set working directory
cd "$(dirname "$0")"

# Create virtual environment if it doesn't exist
if [ ! -d "ultra-enhanced-env" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv ultra-enhanced-env
fi

# Activate virtual environment
echo "⚡ Activating virtual environment..."
source ultra-enhanced-env/bin/activate

# Install/upgrade dependencies
echo "⬇️ Installing dependencies..."
pip install -r requirements.txt

# Check which bot to run based on argument
case "${1:-ultimate}" in
    "launcher")
        echo "🎛️ Launching Bot Management System..."
        python3 bot_launcher.py
        ;;
    "clean")
        echo "🧽 Launching Clean Enhanced Bot..."
        python3 clean_enhanced_bot.py
        ;;
    "research")
        echo "🔬 Launching Enhanced Research Bot..."
        python3 enhanced_research_bot.py
        ;;
    "ultimate"|*)
        echo "🎯 Launching Ultimate Research Bot..."
        python3 ultimate_research_bot.py
        ;;
esac

# Deactivate environment when done
deactivate