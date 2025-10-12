#!/bin/bash

echo "🤖 Starting Ollama Discord Bot"
echo "=============================="

# Check if Ollama is running
if ! pgrep -f "ollama serve" > /dev/null; then
    echo "🚀 Starting Ollama service..."
    ollama serve &
    sleep 3
    echo "✅ Ollama started"
fi

# Check if models exist
if ! ollama list | grep -q "llama3.2:3b"; then
    echo "📥 Installing base AI model..."
    ollama pull llama3.2:3b
fi

# Activate virtual environment and run bot
echo "🤖 Starting Discord bot..."
source venv/bin/activate && python3 streamlined_bot.py
