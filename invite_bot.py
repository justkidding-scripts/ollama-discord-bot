#!/usr/bin/env python3
"""
Discord Bot Invitation Helper
Generates the correct invite URL for your bot
"""

import os
import sys
from dotenv import load_dotenv
import requests
import json

load_dotenv()

def get_client_id_from_token(token):
    """Extract client ID from bot token"""
    try:
        # Bot tokens are encoded with the client ID
        import base64
        # First part of token before first dot contains client ID
        client_id_part = token.split('.')[0]
        # Decode base64
        decoded = base64.b64decode(client_id_part + '==')
        return decoded.decode('utf-8')
    except:
        return None

def generate_invite_url():
    """Generate Discord bot invite URL"""
    
    print("🤖 Discord Bot Invitation Helper")
    print("=" * 40)
    
    # Check if token exists
    token = os.getenv('DISCORD_TOKEN')
    if not token or token == 'your_discord_bot_token_here':
        print("❌ Discord token not configured!")
        print("\n📝 Steps to configure:")
        print("1. Go to https://discord.com/developers/applications")
        print("2. Create a new application or select existing one")
        print("3. Go to 'Bot' tab and copy the token")
        print("4. Edit .env file: nano .env")
        print("5. Replace: DISCORD_TOKEN=your_actual_bot_token_here")
        print("6. Run this script again")
        return
    
    print("✅ Discord token found!")
    
    # Try to get client ID from token
    client_id = get_client_id_from_token(token)
    
    if not client_id:
        print("\n🔍 Need your bot's Client ID:")
        print("1. Go to https://discord.com/developers/applications")
        print("2. Select your application")
        print("3. In 'General Information', copy the 'Application ID'")
        client_id = input("\nEnter your bot's Application ID: ").strip()
    
    if not client_id:
        print("❌ Client ID is required to generate invite URL")
        return
    
    print(f"✅ Using Client ID: {client_id}")
    
    # Required permissions for the bot
    permissions = {
        'Send Messages': 2048,
        'Read Message History': 65536, 
        'Use Slash Commands': 2147483648,
        'Add Reactions': 64,
        'Embed Links': 16384,
        'Attach Files': 32768,
        'Send Messages in Threads': 274877906944,
        'Use External Emojis': 262144
    }
    
    # Calculate total permissions
    total_permissions = sum(permissions.values())
    
    # Generate invite URL
    invite_url = f"https://discord.com/api/oauth2/authorize?client_id={client_id}&permissions={total_permissions}&scope=bot%20applications.commands"
    
    print(f"\n🔗 Your bot invite URL:")
    print("=" * 60)
    print(invite_url)
    print("=" * 60)
    
    print(f"\n📋 Included permissions:")
    for perm_name in permissions.keys():
        print(f"   ✅ {perm_name}")
    
    print(f"\n🚀 Next steps:")
    print("1. Copy the URL above")
    print("2. Paste it in your browser")
    print("3. Select your Discord server")
    print("4. Click 'Authorize'")
    print("5. Run: ./deploy_enhanced_bot.sh")
    
    # Save URL to file for easy access
    with open('bot_invite_url.txt', 'w') as f:
        f.write(invite_url)
    
    print(f"\n💾 URL also saved to: bot_invite_url.txt")
    
    return invite_url

def check_bot_status():
    """Check if bot can connect to Discord"""
    token = os.getenv('DISCORD_TOKEN')
    if not token or token == 'your_discord_bot_token_here':
        return False
    
    try:
        headers = {
            'Authorization': f'Bot {token}',
            'Content-Type': 'application/json'
        }
        response = requests.get('https://discord.com/api/v10/users/@me', headers=headers, timeout=5)
        if response.status_code == 200:
            bot_info = response.json()
            print(f"✅ Bot authentication successful!")
            print(f"   Bot Name: {bot_info.get('username', 'Unknown')}")
            print(f"   Bot ID: {bot_info.get('id', 'Unknown')}")
            return True
        else:
            print(f"❌ Bot authentication failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error checking bot status: {e}")
        return False

def main():
    if len(sys.argv) > 1 and sys.argv[1] == '--check':
        print("🔍 Checking bot authentication...")
        check_bot_status()
    else:
        generate_invite_url()
        print(f"\n🔍 Testing bot authentication...")
        check_bot_status()

if __name__ == "__main__":
    main()