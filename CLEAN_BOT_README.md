# Clean Enhanced Discord Bot - PhD Research Assistant

🎓 **Academic Research-Focused Discord Bot** (Cybersecurity/hacking features removed)

## Current Status
✅ **RUNNING** - Process ID: 893383  
✅ **Features**: Terminal, Webhooks, Agents  
✅ **Database**: SQLite logging enabled  
✅ **Webhook Server**: Port 8085  

## Available Slash Commands

### `/terminal`
Creates a secure terminal session for basic development tasks
- **Safe Commands Only**: ls, cat, head, tail, grep, find, pwd, whoami, date, echo, git, python3, node, npm, pip3
- **Blocked**: All security/hacking tools, system modification commands
- **Timeout**: 5 minutes of inactivity
- **Directory Restriction**: /home/nike/ only

### `/term <command>`
Execute commands in your terminal session
- **Example**: `/term ls -la`
- **Example**: `/term git status`
- **Example**: `/term python3 --version`

### `/agent <agent_name> <query>`
Chat with AI agents via Ollama bridge
- **Example**: `/agent research "explain machine learning"`
- **Example**: `/agent assistant "help with Python code"`

### `/debug`
Show bot performance and system information
- Command statistics
- System resource usage
- Active terminal sessions
- Bot status

## Clean Features (No Cybersecurity)

### ✅ What's Included:
- **Secure Terminal**: Basic file operations, development tools
- **AI Agent Integration**: Chat with Ollama models
- **Webhook Server**: Research data integration
- **Performance Monitoring**: Command statistics and system metrics
- **Database Logging**: SQLite-based command and user tracking
- **Scheduled Tasks**: Automatic cleanup and maintenance
- **Rate Limiting**: Prevent spam and abuse

### ❌ What's Removed:
- All network scanning tools (nmap, netstat, ss)
- Security testing frameworks (Metasploit, Burp Suite)
- Password cracking tools (hashcat, john)
- Web security scanners (nikto, gobuster, sqlmap)
- Vulnerability analysis tools
- OSINT and threat intelligence features
- Dark web monitoring
- Cryptocurrency analysis
- Social engineering simulations

## File Structure

```
/home/nike/ollama-discord-bot/
├── clean_enhanced_bot.py          # Main clean bot file
├── clean_enhanced_bot.log         # Bot runtime logs
├── clean_bot_output.log          # Background process output
├── clean_bot.db                   # SQLite database
├── .env                          # Environment configuration
└── CLEAN_BOT_README.md           # This documentation
```

## Configuration

### Environment Variables (.env)
```env
DISCORD_TOKEN=your_discord_token
WEBHOOK_PORT=8085
WEBHOOK_SECRET=research_webhook_secret
TERMINAL_TIMEOUT=300
DEBUG_MODE=true
```

### Webhook Endpoints
- **Research Data**: `POST http://localhost:8085/webhook/research`
- **Status Check**: `GET http://localhost:8085/webhook/status`

### Authentication
```bash
curl -X POST http://localhost:8085/webhook/research \
  -H "Authorization: Bearer research_webhook_secret" \
  -H "Content-Type: application/json" \
  -d '{"channel_id": "123456789", "message": "Research update"}'
```

## Usage Examples

### Academic Research Workflow
```
1. /terminal                    # Create secure session
2. /term git clone https://... # Clone research repository
3. /term ls -la                # Explore files
4. /term python3 analysis.py   # Run analysis scripts
5. /agent research "explain results"  # Get AI insights
6. /debug                      # Check system performance
```

### Safe Development Tasks
```
- /term git status
- /term git log --oneline -10
- /term python3 -m pip list
- /term npm install
- /term find . -name "*.py" | head -10
- /term cat requirements.txt
```

## Management Commands

### Start Bot
```bash
cd /home/nike/ollama-discord-bot
python3 clean_enhanced_bot.py
```

### Background Mode
```bash
cd /home/nike/ollama-discord-bot
nohup python3 clean_enhanced_bot.py > clean_bot_output.log 2>&1 &
```

### Stop Bot
```bash
pkill -f "clean_enhanced_bot.py"
```

### Check Status
```bash
ps aux | grep clean_enhanced_bot
tail -f clean_enhanced_bot.log
```

### View Database
```bash
sqlite3 clean_bot.db
.tables
.schema users
SELECT * FROM command_history LIMIT 10;
```

## Security & Safety Features

### Terminal Security
- **Command Whitelist**: Only approved commands allowed
- **Path Restriction**: Limited to /home/nike/ directory
- **Timeout Protection**: Sessions expire after 5 minutes
- **Input Validation**: All commands sanitized and validated
- **Complex Syntax Blocking**: No pipes, redirects, or command chaining

### Rate Limiting
- Terminal creation: 3 per 5 minutes
- Command execution: 10 per minute
- Agent queries: 5 per minute

### Audit Logging
- All commands logged to SQLite database
- User activity tracking
- Performance metrics collection
- Error logging and monitoring

## Academic Integration

### Research Data Webhooks
Send research updates directly to Discord channels:
```json
{
  "channel_id": "your_channel_id",
  "message": "Data analysis complete",
  "details": "Found 95% accuracy in model predictions"
}
```

### AI Agent Queries
Perfect for academic research assistance:
- Literature review help
- Code explanation
- Data analysis interpretation
- Academic writing support

## Support & Troubleshooting

### Common Issues
1. **Bot not responding**: Check if process is running with `ps aux | grep clean_enhanced_bot`
2. **Terminal timeout**: Sessions expire after 5 minutes - create new one with `/terminal`
3. **Command blocked**: Only whitelisted commands allowed - see safe commands list
4. **Rate limited**: Wait and try again, limits reset automatically

### Log Analysis
```bash
# View recent activity
tail -50 clean_enhanced_bot.log

# Search for errors
grep -i error clean_enhanced_bot.log

# Monitor real-time
tail -f clean_enhanced_bot.log
```

### Database Queries
```sql
-- Most used commands
SELECT command, COUNT(*) as usage FROM command_history 
GROUP BY command ORDER BY usage DESC LIMIT 10;

-- User activity
SELECT user_id, COUNT(*) as commands, MAX(timestamp) as last_seen 
FROM command_history GROUP BY user_id;

-- Error rate
SELECT 
  DATE(timestamp) as date,
  COUNT(*) as total_commands,
  SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as errors
FROM command_history 
GROUP BY DATE(timestamp);
```

## Performance Metrics

The bot tracks comprehensive performance data:
- **Command Statistics**: Usage frequency and success rates
- **Response Times**: Average execution times
- **System Resources**: Memory and CPU usage
- **Error Rates**: Command failure tracking
- **Uptime**: Bot operational duration

Access via `/debug` command or check the database directly.

---

🔬 **Clean PhD Research Bot** - Academic-focused, security tools removed, safe for educational environments.