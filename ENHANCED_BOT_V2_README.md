# Enhanced Discord Bot V2 - PhD Research Assistant

## 🚀 Features Overview

This enhanced Discord bot integrates **84 AI Agents** via Ollama with **secure terminal access**, **webhook integrations**, and **scheduled research data collection** for advanced PhD-level cybersecurity and criminology research.

### ✨ New Features in V2

1. **🖥️ Secure Discord Terminal**
   - Command filtering and whitelist security
   - Session management with timeouts
   - Working directory tracking
   - Real-time command execution

2. **🔗 Webhook Integration System**
   - Research data collection endpoints
   - Real-time alert notifications  
   - External tool integration
   - HTTP API with authentication

3. **⏰ Scheduled Tasks**
   - Automated research data collection
   - Terminal session cleanup
   - System metrics reporting
   - Periodic maintenance tasks

4. **🛡️ Enhanced Security**
   - Command whitelist/blacklist system
   - Rate limiting per user
   - Secure execution environment
   - Session timeout protection

## 📋 Command Reference

### Terminal Commands
- `!terminal` - Create a new secure terminal session
- `!term <command>` - Execute command in terminal
- `!terminals` - List your active terminal sessions
- `!close_terminal [session_id]` - Close terminal session(s)

### Agent Commands  
- `!agent <agent_name> <query>` - Chat with specific AI agent
- `!agents` - List all available agents

### System Commands
- `!status` - Show bot status and system metrics
- `!webhook_info` - Display webhook configuration
- `!help` - Show command help (standard Discord.py)

## 🖥️ Terminal Usage

### Creating a Terminal
```
!terminal
```
This creates a secure terminal session with:
- **5-minute timeout** (configurable)
- **Command filtering** for security
- **Working directory tracking**
- **Command history**

### Executing Commands
```
!term ls -la
!term cd /home/nike/projects
!term python3 --version
!term git status
```

### Security Features
**Allowed Commands:**
- File operations: `ls`, `cat`, `head`, `tail`, `grep`, `find`, `which`
- System info: `pwd`, `whoami`, `uname`, `uptime`, `free`, `df`, `ps`
- Development: `git`, `python3`, `node`, `npm`, `pip3`, `ollama`
- Network: `ping`, `nslookup`, `dig`, `traceroute`

**Blocked Commands:**
- Destructive: `rm`, `mv`, `chmod`, `chown`
- System: `sudo`, `systemctl`, `kill`, `shutdown`
- Process: `nohup`, `bg`, `fg`, `disown`

## 🔗 Webhook API

### Base Configuration
- **URL:** `http://localhost:8085`
- **Authentication:** Bearer token (`WEBHOOK_SECRET`)
- **Content-Type:** `application/json`

### Research Data Endpoint
**POST** `/webhook/research`

```json
{
  "channel_id": "123456789012345678",
  "message": "Research data collected",
  "details": "Additional context information"
}
```

**Headers:**
```
Authorization: Bearer ultra_enhanced_webhook_secret_2024
Content-Type: application/json
```

### Alert Endpoint
**POST** `/webhook/alert`

```json
{
  "channel_id": "123456789012345678",
  "type": "warning",
  "message": "System alert triggered"
}
```

Alert types: `info`, `warning`, `error`, `success`

### Status Endpoint
**GET** `/webhook/status`

Returns system health information:
```json
{
  "status": "online",
  "bot_guilds": 1,
  "active_terminals": 2,
  "timestamp": "2025-10-12T09:00:00.000Z"
}
```

## ⏰ Scheduled Tasks

### Terminal Cleanup (Every Hour)
- Removes expired terminal sessions
- Notifies users of cleanup
- Prevents resource leaks

### Research Data Collection (Every 6 Hours)
- Collects system metrics
- Sends to research channels
- Tracks usage patterns
- Performance monitoring

## 📊 System Monitoring

The bot automatically tracks:
- **Active terminal sessions**
- **Memory usage**  
- **Disk usage**
- **System load average**
- **Connected Discord servers**
- **Command execution rates**

## 🔧 Configuration

### Environment Variables
```bash
# Discord Configuration
DISCORD_TOKEN=your_bot_token
WEBHOOK_PORT=8085
WEBHOOK_SECRET=research_webhook_secret

# Terminal Settings
TERMINAL_TIMEOUT=300          # 5 minutes
MAX_TERMINALS_PER_USER=3      # Per user limit

# Rate Limiting
RATE_LIMIT_PER_USER=10        # Commands per minute
RATE_LIMIT_WINDOW=60          # Time window
```

### Security Settings
```bash
# Terminal Security
TERMINAL_SECURITY_MODE=strict
TERMINAL_LOG_COMMANDS=true

# Webhook Security  
WEBHOOK_SECRET=ultra_enhanced_webhook_secret_2024
```

## 🚦 Running the Bot

### Manual Start
```bash
cd /home/nike/ollama-discord-bot
python3 enhanced_discord_bot_v2.py
```

### Background Process
```bash
nohup python3 enhanced_discord_bot_v2.py > enhanced_bot.out 2>&1 &
```

### Check Status
```bash
ps aux | grep enhanced_discord_bot_v2.py
tail -f enhanced_bot.out
```

## 🛠️ Troubleshooting

### Terminal Issues
- **Session expired:** Use `!terminal` to create new session
- **Command blocked:** Check allowed commands list
- **Permission denied:** Commands run as bot user only

### Webhook Issues  
- **Port conflicts:** Change `WEBHOOK_PORT` in .env
- **Authentication:** Verify `WEBHOOK_SECRET` matches
- **Network:** Check firewall rules for webhook port

### Agent Integration
- **Timeout errors:** Increase `AGENT_TIMEOUT` setting
- **Bridge issues:** Verify ollama-agent-bridge.py exists
- **Model errors:** Check Ollama service status

## 📁 File Structure
```
/home/nike/ollama-discord-bot/
├── enhanced_discord_bot_v2.py      # Main bot code
├── ollama-agent-bridge.py          # Agent integration
├── start_enhanced_bot.sh           # Startup script
├── .env                            # Configuration
├── enhanced_bot.out                # Runtime logs
├── enhanced_discord_bot.log        # Application logs
└── SERVER_SETUP_GUIDE.md          # Discord server setup
```

## 🔬 Research Applications

### PhD Cybersecurity Research
- **Terminal access** for real-time analysis
- **Agent consultation** for expert insights
- **Webhook integration** with research tools
- **Automated data collection** for studies

### Criminology Studies
- **Secure command execution** for forensics
- **Multi-agent analysis** for case studies
- **Real-time alerts** for incident tracking
- **Scheduled reporting** for longitudinal studies

## 🎯 Next Steps

1. **Add bot to Discord server** using invite link
2. **Test terminal functionality** with basic commands
3. **Configure webhook integrations** for research tools
4. **Set up research data collection** channels
5. **Customize agent workflows** for specific studies

## 📞 Support

The bot includes comprehensive error handling and logging. Check:
- `enhanced_bot.out` for runtime logs
- `enhanced_discord_bot.log` for application logs  
- Discord channel messages for user feedback
- Webhook endpoints for integration status

---

**Enhanced Discord Bot V2** - Empowering PhD research with AI agents, secure terminals, and intelligent automation. 🚀🔬