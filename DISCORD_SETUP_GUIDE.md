# Discord Bot Setup & Invitation Guide

## Step 1: Create Discord Application & Bot

### 1.1 Go to Discord Developer Portal
1. Open your browser and go to: **https/discord.com/developers/applications**
2. Click **"New Application"**
3. Give your application a name (e.g., "Multi-Agent AI Bot")
4. Click **"Create"**

### 1.2 Create Bot User
1. In the left sidebar, click **"Bot"**
2. Click **"Add Bot"** (if not already created)
3. Under **"Token"** section, click **"Reset Token"** then **"Copy"**
4. **SAVE THIS TOKEN SECURELY** - you'll need it next!

### 1.3 Configure Bot Settings
1. **Privileged Gateway Intents** (IMPORTANT):
 - Enable **"Message Content Intent"**
 - Enable **"Server Members Intent"** (optional)
 - Enable **"Presence Intent"** (optional)

2. **Bot Permissions** (we'll set these in OAuth2):
 - Send Messages
 - Read Message History
 - Use Slash Commands
 - Add Reactions
 - Embed Links

## Step 2: Configure Your Bot Project

### 2.1 Add Discord Token
```bash
# Edit the .env file
nano .env

# Replace the token line with your actual token:
DISCORD_TOKEN=your_actual_discord_bot_token_here
```

**️ NEVER share your bot token publicly!**

### 2.2 Verify System Status
```bash
# Check Ollama is running
systemctl --user status ollama

# Test agent bridge
source discord-bot-env/bin/activate
python3 ollama-agent-bridge.py --status
```

## Step 3: Generate Bot Invite URL

### 3.1 OAuth2 URL Generator
1. In Discord Developer Portal, go to **"OAuth2"** → **"URL Generator"**
2. **Scopes**: Select these checkboxes:
 - `bot`
 - `applications.commands`

3. **Bot Permissions**: Select these checkboxes:
 - Send Messages
 - Send Messages in Threads
 - Read Message History
 - Use Slash Commands
 - Add Reactions
 - Embed Links
 - Attach Files
 - Use External Emojis

### 3.2 Generated URL
Copy the **Generated URL** at the bottom of the page. It should look like:
```
https/discord.com/api/oauth2/authorize?client_id=YOUR_CLIENT_ID&permissions=277025902592&scope=bot%20applications.commands
```

## Step 4: Invite Bot to Your Server

### 4.1 Use Invite URL
1. **Paste the generated URL** in your browser
2. **Select your Discord server** from the dropdown
3. **Review permissions** and click **"Authorize"**
4. **Complete captcha** if prompted

### 4.2 Verify Bot Joined
1. Check your Discord server
2. Your bot should appear in the member list (offline initially)
3. The bot will show as online once you start it

## Step 5: Deploy and Test Your Bot

### 5.1 Deploy Bot
```bash
# Run the deployment script
./deploy_enhanced_bot.sh
```

Follow the prompts:
- It will verify your configuration
- Ask if you want to install as a systemd service
- Start the bot automatically

### 5.2 Test Bot Commands
Once deployed, test in Discord:

```
!help
!agents
!agent python-developer hello world
!system
```

## Quick Reference

### Essential Discord Developer Settings
- **Application Name**: Your bot's name
- **Bot Token**: Keep secret, add to .env file
- **Message Content Intent**: MUST be enabled
- **Permissions**: Send Messages, Read History, Slash Commands

### Bot Invite URL Template
```
https/discord.com/api/oauth2/authorize?client_id=YOUR_CLIENT_ID&permissions=277025902592&scope=bot%20applications.commands
```

### Required Files Check
```bash
# Verify these files exist and are configured:
ls -la .env # Contains DISCORD_TOKEN
ls -la enhanced_discord_bot_v2.py # Main bot file
ls -la ollama-agent-bridge.py # Agent system
ls -la deploy_enhanced_bot.sh # Deployment script
```

### Testing Commands
```bash
# Test agent bridge system
python3 ollama-agent-bridge.py --status

# Test bot configuration (dry run)
source discord-bot-env/bin/activate
timeout 10 python3 enhanced_discord_bot_v2.py
```

## ️ Troubleshooting

### Bot Token Issues
- **Invalid token**: Regenerate token in Developer Portal
- **Token in wrong format**: Should be a long string starting with letters/numbers
- **Permissions denied**: Check bot permissions in server settings

### Bot Won't Join Server
- **Missing permissions**: Regenerate invite URL with correct permissions
- **Server owner only**: Only server owners/admins can invite bots
- **Bot already in server**: Check member list, may be offline

### Bot Offline After Invitation
- **Not started yet**: Bot appears offline until you run the deployment script
- **Configuration error**: Check .env file and logs
- **Ollama not running**: Ensure `systemctl --user status ollama` shows active

### Commands Not Working
- **Message Content Intent**: Must be enabled in Developer Portal
- **Missing permissions**: Check bot role permissions in server
- **Incorrect prefix**: Commands start with `!` (exclamation mark)

## Success Checklist

- Discord application created
- Bot user created and token copied
- Message Content Intent enabled
- Token added to .env file
- Bot invited to Discord server
- Deployment script completed successfully
- Bot shows as online in Discord
- `!help` command works
- Agent commands respond correctly

**Your multi-agent Discord bot is ready to use!**

---

*Need help? Check the logs with `journalctl -u enhanced-discord-bot -f` or review the main README.md file.*