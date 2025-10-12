#!/usr/bin/env python3
"""
Ollama Discord Bot Runner
Automatically loads environment variables and starts the bot
"""
import os
import sys
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, str(Path(__file__).parent.absolute()))

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️  python-dotenv not found. Using system environment variables only.")

# Import and run the bot
from discord_bot import main

if __name__ == "__main__":
    main()
