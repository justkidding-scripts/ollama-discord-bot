# Multi-Agent Discord Bot

**A powerful Discord bot with 10 specialized AI agents powered by Ollama**

## Features

- **10 Specialized Agents** - Development, creative, business, education & support
- **Agent Chaining** - Combine multiple agents for complex workflows
- **Multi-Agent Analysis** - Collaborative research and problem-solving
- **Local AI** - Privacy-preserving with Ollama (no external API calls)
- **Fast & Reliable** - Built-in rate limiting and error handling
- **Rich Discord Integration** - Embeds, reactions, typing indicators

## Quick Start

### 1. Prerequisites
```bash
# Ensure Ollama is running
systemctl --user status ollama
ollama list # Should show llama3.2:3b
```

### 2. Configure Discord Token
```bash
# Edit .env file
nano .env

# Set your Discord bot token:
DISCORD_TOKEN=your_actual_discord_bot_token_here
```

### 3. Deploy Bot
```bash
# Run deployment script
./deploy_enhanced_bot.sh
```

### 4. Test Bot
Invite your bot to Discord and try:
```
!help
!agent python-developer create a simple web server
!agents
```

## Commands

### Core Commands
- `!help` - Show all available commands
- `!agent <name> <query>` - Chat with a specific agent
- `!agents` - List all available agents by category
- `!chain <agents> <query>` - Chain multiple agents for workflows
- `!research <topic>` - Multi-agent collaborative analysis
- `!system` - Check bot status and statistics
- `!models` - Show available AI models

## Available Agents

### Development
- **python-developer** - Python programming, web development, scripting
- **web-developer** - HTML, CSS, JavaScript, responsive design
- **backend-developer** - APIs, databases, server architecture

### Creative & Content
- **content-writer** - Writing, editing, content creation, storytelling
- **designer** - UI/UX design, graphics, visual concepts

### Business & Planning
- **business-advisor** - Strategy, planning, market analysis
- **project-manager** - Project planning, coordination, workflow optimization

### Education & Support
- **tutor** - Education, explanations, skill development
- **general-assistant** - General questions, everyday tasks, problem solving
- **tech-helper** - Technical troubleshooting, software help, IT support

## Usage Examples

### Basic Agent Queries
```
!agent python-developer How do I create a REST API with FastAPI?
!agent content-writer Write a compelling product description for a smartphone
!agent business-advisor What are key metrics for a SaaS startup?
!agent designer What are current UI/UX trends for mobile apps?
```

### Multi-Agent Workflows
```
!chain python-developer,web-developer Create a full-stack web application
!chain content-writer,designer Create a blog post with visual layout suggestions
!chain business-advisor,project-manager Plan a product launch timeline
```

### Collaborative Analysis
```
!research web development best practices for 2024
!research starting an online business
!research machine learning fundamentals
!research effective team management strategies
```

## Configuration

### Environment Variables (.env)
```bash
# Discord Configuration
DISCORD_TOKEN=your_discord_bot_token_here
OLLAMA_HOST=http/localhost:11434
DEFAULT_MODEL=llama3.2:3b

# Rate Limiting
RATE_LIMIT_PER_USER=8 # Requests per minute
RATE_LIMIT_WINDOW=60 # Rate limit window in seconds

# Advanced Settings
MAX_MESSAGE_LENGTH=1900 # Max Discord message length
RESEARCH_COOLDOWN=30 # Cooldown for research command
CHAIN_COOLDOWN=15 # Cooldown for chain command
AGENT_TIMEOUT=120 # Max seconds per agent query
LOG_LEVEL=INFO # Logging level
```

### System Requirements
- **RAM**: 4GB+ (8GB recommended)
- **CPU**: 4+ cores for concurrent agent processing
- **Storage**: 5GB+ for models and logs
- **Network**: Stable internet for Discord connectivity

## Monitoring & Logs

### Service Management
```bash
# Check bot service status
sudo systemctl status enhanced-discord-bot

# View live logs
journalctl -u enhanced-discord-bot -f

# Restart bot service
sudo systemctl restart enhanced-discord-bot
```

### Log Files
- **Bot logs**: `/home/nike/ollama-discord-bot/enhanced_agent_bot.log`
- **System logs**: `journalctl -u enhanced-discord-bot`
- **Ollama logs**: `journalctl -u ollama --user`

## ️ Troubleshooting

### Bot Won't Start
1. Check Discord token in `.env` file
2. Verify Ollama is running: `systemctl --user status ollama`
3. Check dependencies: `source discord-bot-env/bin/activate && pip list`

### Agents Not Responding
1. Test bridge: `python3 ollama-agent-bridge.py --status`
2. Check models: `ollama list`
3. Restart Ollama: `systemctl --user restart ollama`

### Performance Issues
1. Monitor resources: `htop` and `free -h`
2. Adjust rate limits in `.env` file
3. Check log files for errors

## Development

### Project Structure
```
ollama-discord-bot/
├── enhanced_discord_bot_v2.py # Main Discord bot
├── ollama-agent-bridge.py # Agent bridge system
├── deploy_enhanced_bot.sh # Deployment script
├── .env # Configuration
├── discord-bot-env/ # Python virtual environment
├── enhanced-discord-bot.service # Systemd service file
└── logs/ # Log files
```

### Adding New Agents
1. Edit `ollama-agent-bridge.py`
2. Add agent to `mock_agents` dictionary
3. Update `agent_categories` in Discord bot
4. Restart bot service

### Extending Functionality
- Add new Discord commands in `enhanced_discord_bot_v2.py`
- Create custom agent workflows
- Integrate with external APIs
- Add database persistence

## Security

- **Local Processing** - All AI runs locally via Ollama
- **Rate Limiting** - Prevents spam and abuse
- **Input Validation** - Sanitizes user inputs
- **Error Handling** - Graceful failure recovery
- **Secure Configuration** - Environment variables for secrets

## Performance Tips

1. **Optimize Rate Limits** - Adjust based on server size
2. **Monitor Resources** - Keep an eye on CPU and memory usage
3. **Use Agent Chains Wisely** - For complex multi-step problems
4. **Regular Updates** - Keep Ollama and dependencies current

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is open source and available under the [MIT License](LICENSE).

---

** Your multi-agent Discord bot is ready!**

Perfect for developers, content creators, businesses, and anyone who needs AI assistance directly in Discord. The local Ollama integration ensures privacy while providing powerful AI capabilities through specialized agents.

*Built with ️ using Ollama, Discord.py, and Python*
