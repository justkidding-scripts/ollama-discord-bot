# Clean Enhanced Discord Bot - Research Assistant

 **Academic Research-Focused Discord Bot** - A clean, secure Discord bot designed for research environments with all cybersecurity/hacking features removed.

[![Python 3.x](https/img.shields.io/badge/python-3.x-blue.svg)](https/www.python.org/)
[![Discord.py](https/img.shields.io/badge/discord.py-2.x-blue.svg)](https/discordpy.readthedocs.io/)
[![License](https/img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## Overview

This Discord bot provides a secure, academic-focused environment for researchers. It includes safe terminal access, AI agent integration, and research data webhooks while maintaining strict security boundaries.

## Features

### Core Capabilities
- **️ Secure Terminal**: Sandboxed terminal with whitelisted commands only
- ** AI Agent Integration**: Connect with Ollama models for research assistance
- ** Webhook Server**: Research data integration and notifications
- ** Performance Monitoring**: Command statistics and system metrics
- **️ Database Logging**: SQLite-based audit trails and user tracking
- **⏰ Scheduled Tasks**: Automatic cleanup and maintenance
- **️ Rate Limiting**: Built-in protection against spam and abuse

### Security Features Removed
- All network scanning tools (nmap, netstat, ss)
- Security testing frameworks (Metasploit, Burp Suite)
- Password cracking tools (hashcat, john)
- Web security scanners (nikto, gobuster, sqlmap)
- OSINT and threat intelligence tools
- Dark web monitoring capabilities
- Cryptocurrency analysis tools
- Social engineering simulation features

## Quick Start

### Prerequisites
- Python 3.8+
- Discord Bot Token
- Ollama (optional, for AI agents)

### Installation

1. **Clone the repository**
```bash
git clone https/github.com/yourusername/ollama-discord-bot.git
cd ollama-discord-bot
```

2. **Install dependencies**
```bash
pip3 install -r requirements.txt
```

3. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your Discord token
```

4. **Run the bot**
```bash
python3 clean_enhanced_bot.py
```

## Slash Commands

### `/terminal`
Creates a secure terminal session for basic development tasks.
- **Safe Commands**: ls, cat, head, tail, grep, find, pwd, whoami, date, echo, git, python3, node, npm, pip3
- **Restrictions**: /home/user directory only, 5-minute timeout
- **Security**: Command whitelist, input validation, no complex syntax

### `/term <command>`
Execute commands in your active terminal session.
```
/term ls -la
/term git status
/term python3 --version
```

### `/agent <agent_name> <query>`
Chat with AI agents for research assistance.
```
/agent research "explain machine learning concepts"
/agent assistant "help debug Python code"
```

### `/debug`
Display bot performance and system information.
- Command usage statistics
- System resource monitoring
- Active terminal sessions
- Error rates and uptime

## Configuration

### Environment Variables
```env
DISCORD_TOKEN=your_discord_bot_token
WEBHOOK_PORT=8085
WEBHOOK_SECRET=your_webhook_secret
TERMINAL_TIMEOUT=300
DEBUG_MODE=true
```

### Webhook Integration
Send research data to Discord channels:
```bash
curl -X POST http/localhost:8085/webhook/research \\
 -H "Authorization: Bearer your_webhook_secret" \\
 -H "Content-Type: application/json" \\
 -d '{"channel_id": "123456789", "message": "Analysis complete"}'
```

## Security & Safety

### Terminal Security
- **Command Whitelist**: Only pre-approved commands allowed
- **Path Restriction**: Limited to designated directories
- **Input Validation**: All commands sanitized and validated
- **Session Timeout**: Automatic cleanup after inactivity
- **Complex Syntax Blocking**: No pipes, redirects, or command chaining

### Rate Limiting
- Terminal creation: 3 per 5 minutes
- Command execution: 10 per minute
- Agent queries: 5 per minute

### Audit Logging
All activities logged to SQLite database:
- User commands and responses
- System performance metrics
- Error tracking and analysis
- Session management

## Development

### Project Structure
```
├── clean_enhanced_bot.py # Main bot application
├── CLEAN_BOT_README.md # Detailed documentation
├── requirements.txt # Python dependencies
├── .env # Environment configuration
├── .gitignore # Git exclusions
└── README.md # This file
```

### Adding Features
1. Fork the repository
2. Create a feature branch
3. Implement changes with tests
4. Submit a pull request

### Running in Development
```bash
export DEBUG_MODE=true
python3 clean_enhanced_bot.py
```

## Deployment

### Background Mode
```bash
nohup python3 clean_enhanced_bot.py > bot_output.log 2>&1 &
```

### Process Management
```bash
# Check status
ps aux | grep clean_enhanced_bot

# Stop bot
pkill -f "clean_enhanced_bot.py"

# View logs
tail -f clean_enhanced_bot.log
```

### Systemd Service (Optional)
Create `/etc/systemd/system/clean-discord-bot.service`:
```ini
[Unit]
Description=Clean Enhanced Discord Bot
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectorypath/to/bot
ExecStartusr/bin/python3 clean_enhanced_bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

## Usage Examples

### Academic Research Workflow
```
1. /terminal # Create secure session
2. /term git clone https/repo.git # Clone research repository
3. /term ls -la # Explore project structure
4. /term python3 analysis.py # Run data analysis
5. /agent research "interpret results" # Get AI insights
6. /debug # Monitor performance
```

### Safe Development Tasks
```
/term git status
/term git log --oneline -10
/term python3 -m pip list
/term find . -name "*.py" | head -10
/term cat requirements.txt
```

## Contributing

1. **Fork** the repository
2. **Create** your feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- **Documentation**: See [CLEAN_BOT_README.md](CLEAN_BOT_README.md) for detailed usage
- **Issues**: Report bugs via GitHub Issues
- **Questions**: Use GitHub Discussions

## Academic Context

This bot was developed specifically for research environments where security tools need to be removed while maintaining development functionality. It provides a safe, monitored environment for academic collaboration and research automation.

---

 **Clean Research Bot** - Academic-focused, security tools removed, safe for educational environments.