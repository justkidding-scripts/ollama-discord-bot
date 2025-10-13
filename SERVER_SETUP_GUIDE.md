# Discord Bot Server Setup Guide

## Current Bot Details
- **Bot Name:** JA
- **Bot ID:** 1426760267651350580
- **Status:** Public bot, no code grant required

## Invite URLs (Try in order)

### Option 1: Basic Bot Permissions
```
https/discord.com/oauth2/authorize?client_id=1426760267651350580&scope=bot&permissions=2148002880
```

### Option 2: Minimal Permissions
```
https/discord.com/oauth2/authorize?client_id=1426760267651350580&scope=bot&permissions=68608
```

### Option 3: Simple Bot Scope Only
```
https/discord.com/oauth2/authorize?client_id=1426760267651350580&scope=bot
```

## Step-by-Step Server Addition

### Method 1: Direct URL
1. Copy one of the invite URLs above
2. Paste it into your browser
3. Select your Discord server from the dropdown
4. Review permissions and click "Authorize"

### Method 2: Discord Developer Portal
1. Go to https/discord.com/developers/applications/1426760267651350580/oauth2/url-generator
2. Select scopes: `bot`
3. Select permissions you want (or leave default)
4. Copy generated URL and use it

### Method 3: Server Settings
1. Go to your Discord server
2. Click "Server Settings" → "Integrations"
3. Click "Bots and Apps" → "View all"
4. Search for "JA" or use bot ID: 1426760267651350580
5. Click "Add to Server"

## Required Permissions Explained

| Permission | Code | Purpose |
|------------|------|---------|
| Send Messages | 2048 | Send bot responses |
| Read Messages | 1024 | Read user commands |
| Use Slash Commands | 2147483648 | Future slash commands |
| Embed Links | 16384 | Rich embedded responses |
| Read Message History | 65536 | Context for commands |

## Troubleshooting

### "Installation type not for this application"
- This usually means the bot scope is incorrect
- Try the "Simple Bot Scope Only" URL above
- Make sure you have "Manage Server" permissions

### "Invalid Permissions"
- The bot might be requesting permissions your server doesn't allow
- Use the minimal permissions URL
- Contact server admin if needed

### "Bot already in server"
- Check if bot is already added but offline
- Look in member list or server settings → integrations

## Testing the Bot

Once added, test with these commands:
- `!ping` - Basic connectivity test
- `!test` - Functionality test
- `!info` - Bot information

## Current Bot Status

The bot should show as online with status "Testing Connection" once properly added to a server.