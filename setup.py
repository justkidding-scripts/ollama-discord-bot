#!/usr/bin/env python3
import os
import subprocess
import sys

def install_requirements():
    """Install Python requirements"""
    print("📦 Installing Python requirements...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

def setup_environment():
    """Setup environment file"""
    env_file = ".env"
    
    if not os.path.exists(env_file):
        print("⚙️  Creating environment file...")
        with open(env_file, "w") as f:
            f.write("# Discord Bot Configuration\n")
            f.write("DISCORD_TOKEN=your_discord_bot_token_here\n")
            f.write("OLLAMA_HOST=http://localhost:11434\n")
            f.write("DEFAULT_MODEL=llama3.2:3b\n")
            f.write("\n# Rate Limiting\n")
            f.write("RATE_LIMIT_PER_USER=5\n")
            f.write("RATE_LIMIT_WINDOW=60\n")
            f.write("\n# Logging\n")
            f.write("LOG_LEVEL=INFO\n")
        print(f"✅ Created {env_file}. Please update DISCORD_TOKEN with your bot token.")
    else:
        print(f"✅ Environment file {env_file} already exists.")

def check_ollama():
    """Check if Ollama is running"""
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            print(f"✅ Ollama is running with {len(models)} models available.")
            return True
        else:
            print("⚠️  Ollama is running but API returned an error.")
            return False
    except Exception as e:
        print(f"❌ Ollama is not running or not accessible: {e}")
        return False

def main():
    print("🤖 Setting up Ollama Discord Bot...")
    
    try:
        # Install requirements
        install_requirements()
        
        # Setup environment
        setup_environment()
        
        # Check Ollama
        if not check_ollama():
            print("\n⚠️  Warning: Ollama is not running!")
            print("   Make sure Ollama is installed and running:")
            print("   sudo systemctl start ollama")
        
        print("\n✅ Setup complete!")
        print("\nNext steps:")
        print("1. Edit .env file and add your Discord bot token")
        print("2. Make sure Ollama is running: sudo systemctl status ollama")
        print("3. Run the bot: python3 discord_bot.py")
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
