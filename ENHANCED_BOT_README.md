# Enhanced Discord Bot with 84-Agent Integration

## Overview

This Discord bot integrates your **84 specialized AI agents** with **Ollama local AI** to provide -level research assistance directly through Discord. Perfect for cybersecurity and criminology research teams.

## Features

### Agent Integration
- **84 Specialized Agents**: Security, research, coding, analysis, and AI specialists
- **Multi-Agent Workflows**: Chain agents for complex analysis
- **Autonomous Research**: Independent research using multiple agents
- **Local AI Processing**: Privacy-preserving with Ollama integration

### Discord Commands
- `!agent <name> <query>` - Chat with specific agent
- `!chain <agents> <query>` - Multi-agent workflows
- `!research <topic>` - Autonomous research mode
- `!agents` - List available agents by category
- `!system` - Check system status
- `!models` - List available AI models

## Prerequisites

### Required Software
```bash
# Core dependencies
sudo apt install -y python3 python3-discord python3-aiohttp python3-yaml

# Ollama (if not installed)
curl -fsSL https/ollama.ai/install.sh | sh
ollama pull llama3.2:3b
```

### Required Services
- **Ollama**: Running on localhost:11434
- **84-Agent System**: Installed in ~/.config/warp/plugins/agents/
- **Discord Bot Token**: From Discord Developer Portal

## Installation

### 1. Clone and Setup
```bash
cd /home/nike/ollama-discord-bot
chmod +x enhanced_agent_discord_bot.py
```

### 2. Configure Environment
Edit `.env` file:
```env
# Discord Configuration
DISCORD_TOKEN=your_bot_token_here
OLLAMA_HOST=http/localhost:11434
DEFAULT_MODEL=llama3.2:3b

# Rate Limiting (increased for research use)
RATE_LIMIT_PER_USER=8
RATE_LIMIT_WINDOW=60

# Logging
LOG_LEVEL=INFO
```

### 3. Discord Bot Setup
1. Go to https/discord.com/developers/applications
2. Create new application → Bot
3. Copy bot token to `.env` file
4. Enable "Message Content Intent"
5. Invite bot to your server with appropriate permissions

### 4. Test Installation
```bash
# Test agent integration
python3 ~/.config/warp/ollama-agent-bridge.py --status

# Test Discord bot (dry run)
python3 enhanced_agent_discord_bot.py --test
```

## Deployment

### Option 1: Manual Run
```bash
cd /home/nike/ollama-discord-bot
python3 enhanced_agent_discord_bot.py
```

### Option 2: Systemd Service (Recommended)
```bash
# Install service
sudo cp enhanced-discord-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable enhanced-discord-bot

# Start service
sudo systemctl start enhanced-discord-bot

# Check status
sudo systemctl status enhanced-discord-bot
journalctl -u enhanced-discord-bot -f
```

## Discord Usage Examples

### Basic Agent Chat
```
!agent security-auditor What are the top OWASP vulnerabilities to focus on?
!agent python-pro Optimize this database query for better performance
!agent data-scientist Analyze these fraud detection patterns
```

### Multi-Agent Workflows
```
!chain security-auditor,backend-security-coder,test-automator Analyze this REST API for security vulnerabilities

!chain data-scientist,business-analyst,risk-manager Assess cryptocurrency fraud risks
```

### Autonomous Research
```
!research advanced persistent threats in cryptocurrency exchanges
!research social engineering techniques in cybercrime
!research threat modeling for financial institutions
```

### System Management
```
!system # Check bot and agent system status
!agents # List all available agents by category
!models # Show available AI models
```

## Agent Categories

### Security Specialists
- `security-auditor` - Vulnerability assessment, OWASP compliance
- `backend-security-coder` - Secure backend coding practices
- `frontend-security-coder` - XSS prevention, CSP implementation
- `mobile-security-coder` - Mobile security patterns

### Research & Analysis
- `data-scientist` - Data analysis, SQL queries, BigQuery
- `business-analyst` - Metrics analysis, KPI tracking
- `risk-manager` - Risk assessment and management
- `docs-architect` - Technical documentation

### Development
- `python-pro` - Advanced Python development
- `javascript-pro` - Modern JavaScript/Node.js
- `backend-architect` - API design, microservices
- `frontend-developer` - React, responsive design

### Quality & Testing
- `test-automator` - Comprehensive test automation
- `debugger` - Error resolution and analysis
- `performance-engineer` - Application optimization
- `error-detective` - Log analysis and debugging

### AI & ML
- `ai-engineer` - LLM applications, RAG systems
- `ml-engineer` - ML pipelines, model serving
- `mlops-engineer` - ML infrastructure and operations
- `prompt-engineer` - LLM prompt optimization

## ️ Configuration

### Rate Limiting
- Default: 8 requests per user per minute
- Research mode: 30-second cooldown
- Chain workflows: 15-second cooldown

### Agent Selection
- Agents automatically mapped by specialization
- Smart model selection based on query complexity
- Context preservation across conversations

### Security Features
- Local AI processing (no external API calls)
- Rate limiting per user
- Input validation and sanitization
- Secure systemd service configuration

## Monitoring & Logs

### System Logs
```bash
# Service logs
journalctl -u enhanced-discord-bot -f

# Application logs
tail -f /home/nike/ollama-discord-bot/enhanced_agent_bot.log

# Ollama logs
journalctl -u ollama -f
```

### Performance Monitoring
```bash
# Check bot status
!system

# Monitor resource usage
htop
ollama ps
```

## ️ Troubleshooting

### Common Issues

**Bot Not Responding**
```bash
# Check service status
sudo systemctl status enhanced-discord-bot

# Restart service
sudo systemctl restart enhanced-discord-bot

# Check Discord token
echo $DISCORD_TOKEN
```

**Agent Integration Errors**
```bash
# Test agent bridge
python3 ~/.config/warp/ollama-agent-bridge.py --status

# Check agent directory
ls -la ~/.config/warp/plugins/agents/agents/

# Test Ollama connection
curl http/localhost:11434/api/tags
```

**Rate Limiting Issues**
```bash
# Adjust in .env file
RATE_LIMIT_PER_USER=10
RATE_LIMIT_WINDOW=60

# Restart bot
sudo systemctl restart enhanced-discord-bot
```

**Memory/Performance Issues**
```bash
# Monitor resources
htop
free -h

# Check Ollama model usage
ollama ps

# Consider lighter model
ollama pull llama3.2:1b
```

### Error Codes
- ` Agent error` - Agent bridge communication failure
- `⏰ Rate limit exceeded` - User sending too many requests
- ` Agent not found` - Invalid agent name
- `⏰ Agent request timed out` - Query too complex or system overloaded

## Advanced Configuration

### Custom Agent Chains
Create preset workflows in the bot configuration:
```python
PRESET_CHAINS = {
 'security-audit': 'security-auditor,backend-security-coder,test-automator',
 'research-analysis': 'data-scientist,business-analyst,risk-manager',
 'code-review': 'code-reviewer,security-auditor,performance-engineer'
}
```

### Model Optimization
```bash
# Install specialized models
ollama pull codellama:7b # For coding tasks
ollama pull mistral:7b # For analysis tasks
ollama pull llama3.2:1b # For fast responses
```

### Integration with Other Services
- Webhook support for external notifications
- Database integration for conversation history
- API endpoints for programmatic access

## Performance Tuning

### For High Load
```env
RATE_LIMIT_PER_USER=15
MAX_CONCURRENT_REQUESTS=10
TIMEOUT_SECONDS=180
```

### For Research Groups
```env
RESEARCH_MODE_COOLDOWN=20
CHAIN_WORKFLOW_COOLDOWN=10
MAX_CONVERSATION_HISTORY=20
```

## Security Considerations

### Production Deployment
1. Use environment variables for sensitive data
2. Enable Discord server-specific bot permissions
3. Monitor and log all interactions
4. Regular security updates for dependencies
5. Firewall configuration for Ollama service

### Privacy Features
- All AI processing happens locally
- No external API calls for agent queries
- Conversation data stays on your server
- Configurable data retention policies

## API Reference

### Bot Commands
| Command | Cooldown | Description |
|---------|----------|-------------|
| `!agent` | 8s | Single agent query |
| `!chain` | 15s | Multi-agent workflow |
| `!research` | 30s | Autonomous research |
| `!agents` | None | List available agents |
| `!system` | None | System status |
| `!models` | None | Available models |

### Agent Categories
| Category | Count | Examples |
|----------|-------|----------|
| Security | 4 | security-auditor, backend-security-coder |
| Research | 4 | data-scientist, business-analyst |
| Coding | 4 | python-pro, backend-architect |
| Analysis | 4 | performance-engineer, debugger |
| AI/ML | 4 | ai-engineer, ml-engineer |

## Support

### Getting Help
1. Check system status: `!system`
2. Review logs: `journalctl -u enhanced-discord-bot`
3. Test agent integration: `python3 ~/.config/warp/ollama-agent-bridge.py --status`
4. Validate Discord permissions and token

### Contributing
- Report issues in the project repository
- Submit feature requests via Discord
- Contribute to agent development
- Share research workflows and use cases

---

** You now have a complete AI-powered Discord bot with 84 specialized agents!** Perfect for research teams, students, and cybersecurity professionals who need powerful AI assistance accessible through Discord.