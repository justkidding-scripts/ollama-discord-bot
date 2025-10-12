#!/bin/bash

echo "🤖 Simple Ollama Discord Bot Setup"
echo "=================================="

# Check Ollama
if ! command -v ollama &> /dev/null; then
    echo "Installing Ollama..."
    curl -fsSL https://ollama.ai/install.sh | sh
fi

# Start Ollama if not running
if ! pgrep -f "ollama serve" > /dev/null; then
    echo "Starting Ollama..."
    ollama serve &
    sleep 3
fi

# Install basic model
echo "Installing AI model..."
ollama pull llama3.2:3b

# Install Python deps
echo "Installing dependencies..."
pip3 install -r simple_requirements.txt

# Create .env if missing
if [ ! -f .env ]; then
    cat > .env << 'ENVEOF'
DISCORD_TOKEN=your_discord_bot_token_here
OLLAMA_HOST=http://localhost:11434
ENVEOF
    echo "⚠️  Edit .env and add your Discord bot token!"
    echo "   Get one from: https://discord.com/developers/applications"
fi

chmod +x streamlined_bot.py

echo ""
echo "✅ Setup complete!"
echo "🚀 Start bot: python3 streamlined_bot.py"
