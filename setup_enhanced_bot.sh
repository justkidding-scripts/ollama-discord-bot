#!/bin/bash

echo "🤖 Enhanced Ollama Discord Bot Setup"
echo "======================================"

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo "❌ Ollama not found! Installing..."
    curl -fsSL https://ollama.ai/install.sh | sh
    echo "✅ Ollama installed"
fi

# Start Ollama service if not running
if ! pgrep -f "ollama serve" > /dev/null; then
    echo "🚀 Starting Ollama service..."
    ollama serve &
    sleep 5
fi

# Install base models
echo "📥 Installing AI models..."
ollama pull llama3.2:3b
ollama pull llava:7b
echo "✅ Models installed"

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip3 install -r enhanced_requirements.txt

# Check Discord token
if [ ! -f .env ]; then
    echo "⚙️ Creating .env configuration file..."
    cat > .env << 'ENVEOF'
# Discord Bot Configuration
DISCORD_TOKEN=your_discord_bot_token_here
OLLAMA_HOST=http://localhost:11434
DEFAULT_MODEL=llama3.2:3b

# Rate Limiting
RATE_LIMIT_PER_USER=10
RATE_LIMIT_WINDOW=60

# Logging
LOG_LEVEL=INFO
ENVEOF
    echo "❗ Please edit .env file and add your Discord bot token!"
    echo "   You can get one from: https://discord.com/developers/applications"
    exit 1
fi

# Make scripts executable
chmod +x enhanced_discord_bot.py
chmod +x enhanced_launcher.py

echo ""
echo "✅ Setup complete!"
echo "🔧 To start the bot: python3 enhanced_launcher.py"
echo "🌐 Dashboard will be available at: http://localhost:5555"
echo ""
echo "📝 Don't forget to:"
echo "   1. Set your DISCORD_TOKEN in .env file"
echo "   2. Invite the bot to your Discord server"
echo "   3. Grant necessary permissions"
