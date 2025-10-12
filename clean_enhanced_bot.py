#!/usr/bin/env python3
"""
Clean Enhanced Discord Bot - PhD Research Assistant
Features: Scheduled Tasks, Webhooks, Secure Terminal (NO cybersecurity/hacking tools)
"""

import discord
from discord.ext import commands, tasks
from discord import app_commands
import asyncio
import subprocess
import os
import json
import sys
import logging
import time
from datetime import datetime, timedelta
from collections import defaultdict, deque
from typing import Dict, List, Optional, Any, Union
import aiohttp
from aiohttp import web
import aiofiles
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv
import psutil
import sqlite3
import uuid
import shlex
from pathlib import Path

# Load environment variables
load_dotenv()

# Configuration
class CleanBotConfig:
    def __init__(self):
        self.TOKEN = os.getenv('DISCORD_TOKEN')
        self.WEBHOOK_PORT = int(os.getenv('WEBHOOK_PORT', 8085))
        self.WEBHOOK_SECRET = os.getenv('WEBHOOK_SECRET', 'research_webhook_secret')
        self.TERMINAL_TIMEOUT = int(os.getenv('TERMINAL_TIMEOUT', 300))
        self.MAX_OUTPUT_LENGTH = 1900
        self.DEBUG_MODE = os.getenv('DEBUG_MODE', 'false').lower() == 'true'

config = CleanBotConfig()

# Logging setup
log_level = logging.DEBUG if config.DEBUG_MODE else logging.INFO
logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/nike/ollama-discord-bot/clean_enhanced_bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Performance monitoring
class PerformanceMonitor:
    def __init__(self):
        self.command_stats = defaultdict(int)
        self.response_times = deque(maxlen=1000)
        self.error_counts = defaultdict(int)
        self.start_time = datetime.now()
        
    def record_command(self, command: str, execution_time: float, success: bool):
        self.command_stats[command] += 1
        self.response_times.append(execution_time)
        if not success:
            self.error_counts[command] += 1
            
    def get_stats(self) -> Dict[str, Any]:
        avg_response = sum(self.response_times) / len(self.response_times) if self.response_times else 0
        return {
            'total_commands': sum(self.command_stats.values()),
            'avg_response_time': round(avg_response, 3),
            'error_rate': sum(self.error_counts.values()) / max(sum(self.command_stats.values()), 1),
            'memory_usage': psutil.virtual_memory().percent,
            'cpu_usage': psutil.cpu_percent(),
            'uptime_seconds': (datetime.now() - self.start_time).total_seconds()
        }

# Database Manager
class DatabaseManager:
    def __init__(self, db_path: str = 'clean_bot.db'):
        self.db_path = db_path
        self.init_database()
        
    def init_database(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                command_count INTEGER DEFAULT 0
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS command_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                command TEXT,
                channel_id INTEGER,
                guild_id INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                execution_time REAL,
                success BOOLEAN
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")
        
    def log_command(self, user_id: int, command: str, channel_id: int, guild_id: int, 
                   execution_time: float, success: bool):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO command_history (user_id, command, channel_id, guild_id, 
                                       execution_time, success)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, command, channel_id, guild_id, execution_time, success))
        
        # Update user stats
        cursor.execute('''
            INSERT OR REPLACE INTO users (user_id, username, last_seen, command_count)
            VALUES (?, ?, CURRENT_TIMESTAMP, 
                    COALESCE((SELECT command_count FROM users WHERE user_id = ?), 0) + 1)
        ''', (user_id, str(user_id), user_id))
        
        conn.commit()
        conn.close()

# Clean Terminal (basic commands only)
class CleanTerminal:
    def __init__(self, user_id: int, channel_id: int):
        self.user_id = user_id
        self.channel_id = channel_id
        self.session_id = str(uuid.uuid4())[:8]
        self.created_at = datetime.now()
        self.last_used = datetime.now()
        self.command_count = 0
        self.cwd = "/home/nike"
        
        # Basic safe commands only
        self.allowed_commands = {
            'ls', 'cat', 'head', 'tail', 'grep', 'find', 'pwd', 'whoami', 'date', 'echo',
            'git', 'python3', 'node', 'npm', 'pip3', 'wc', 'sort', 'uniq', 'cut'
        }
        
        self.forbidden_commands = {
            'rm', 'rmdir', 'chmod', 'chown', 'sudo', 'su', 'passwd', 'systemctl', 'kill', 
            'killall', 'pkill', 'shutdown', 'reboot', 'fdisk', 'mkfs', 'dd',
            # Remove all security/hacking related commands
            'nmap', 'netstat', 'ss', 'wireshark', 'tcpdump', 'metasploit', 'aircrack',
            'hydra', 'john', 'hashcat', 'burpsuite', 'sqlmap', 'nikto', 'dirb', 'gobuster'
        }
        
    def is_command_allowed(self, command: str) -> tuple[bool, str]:
        if not command.strip():
            return False, "Empty command"
            
        try:
            parts = shlex.split(command.strip())
        except ValueError as e:
            return False, f"Invalid command syntax: {e}"
            
        if not parts:
            return False, "No command provided"
            
        base_command = parts[0]
        
        # Check forbidden commands
        if base_command in self.forbidden_commands:
            return False, f"Command '{base_command}' is not allowed"
            
        # Check allowed commands
        if base_command in self.allowed_commands:
            return True, "Command allowed"
            
        # Block complex commands
        if any(char in command for char in ['|', '>', '<', '&&', '||', ';', '`', '$(']):
            return False, "Complex command syntax not allowed"
            
        return False, f"Command '{base_command}' not in allowlist"
    
    async def execute_command(self, command: str) -> tuple[str, int]:
        allowed, reason = self.is_command_allowed(command)
        if not allowed:
            return f"❌ {reason}", 1
            
        self.last_used = datetime.now()
        self.command_count += 1
        
        try:
            result = subprocess.run(
                command, shell=True, cwd=self.cwd, capture_output=True, text=True, timeout=30
            )
            
            # Handle cd commands
            if command.strip().startswith('cd '):
                new_dir = command.strip()[3:].strip() or self.cwd
                if new_dir.startswith('/home/nike') or not new_dir.startswith('/'):
                    if new_dir.startswith('/'):
                        if os.path.isdir(new_dir):
                            self.cwd = new_dir
                    else:
                        potential = os.path.abspath(os.path.join(self.cwd, new_dir))
                        if potential.startswith('/home/nike') and os.path.isdir(potential):
                            self.cwd = potential
            
            output = result.stdout
            if result.stderr:
                output += f"\n{result.stderr}"
                
            return output or "Command completed", result.returncode
            
        except subprocess.TimeoutExpired:
            return "❌ Command timed out", 1
        except Exception as e:
            return f"❌ Error: {str(e)}", 1
    
    def is_expired(self) -> bool:
        return (datetime.now() - self.last_used).seconds > config.TERMINAL_TIMEOUT

# Clean Webhook Server
class CleanWebhookServer:
    def __init__(self, bot_instance):
        self.bot = bot_instance
        self.app = web.Application()
        self.setup_routes()
        
    def setup_routes(self):
        self.app.router.add_post('/webhook/research', self.handle_research_webhook)
        self.app.router.add_get('/webhook/status', self.handle_status)
        
    async def handle_research_webhook(self, request):
        try:
            auth_header = request.headers.get('Authorization', '')
            if not auth_header.startswith('Bearer ') or auth_header[7:] != config.WEBHOOK_SECRET:
                return web.json_response({'error': 'Unauthorized'}, status=401)
                
            data = await request.json()
            
            channel_id = data.get('channel_id')
            message = data.get('message', 'Research data received')
            
            if channel_id:
                channel = self.bot.get_channel(int(channel_id))
                if channel:
                    embed = discord.Embed(
                        title="🔬 Research Data",
                        description=message,
                        color=0x00ff00,
                        timestamp=datetime.now()
                    )
                    if 'details' in data:
                        embed.add_field(name="Details", value=data['details'], inline=False)
                    
                    await channel.send(embed=embed)
                    
            return web.json_response({'status': 'success'})
            
        except Exception as e:
            logger.error(f"Webhook error: {e}")
            return web.json_response({'error': 'Internal error'}, status=500)
            
    async def handle_status(self, request):
        return web.json_response({
            'status': 'online',
            'bot_guilds': len(self.bot.guilds),
            'active_terminals': len(self.bot.active_terminals),
            'timestamp': datetime.now().isoformat()
        })

# Main Bot Class
class CleanBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        
        super().__init__(
            command_prefix='!',
            intents=intents,
            help_command=None,
            case_insensitive=True
        )
        
        self.performance = PerformanceMonitor()
        self.database = DatabaseManager()
        self.scheduler = AsyncIOScheduler()
        self.active_terminals: Dict[str, Dict] = {}
        self.user_rate_limits: Dict[int, List[float]] = defaultdict(list)
        
    async def setup_hook(self):
        logger.info("Setting up slash commands...")
        await self.tree.sync()
        logger.info("Slash commands synced")

# Global bot instance
bot = CleanBot()

# Rate limiting
def rate_limit(max_calls: int = 5, window: int = 60):
    def decorator(func):
        async def wrapper(ctx, *args, **kwargs):
            start_time = time.time()
            user_id = ctx.author.id if hasattr(ctx, 'author') else ctx.user.id
            command_name = func.__name__
            
            now = time.time()
            bot.user_rate_limits[user_id] = [
                timestamp for timestamp in bot.user_rate_limits[user_id] 
                if now - timestamp < window
            ]
            
            if len(bot.user_rate_limits[user_id]) >= max_calls:
                await ctx.send("❌ Rate limit exceeded. Please wait.")
                return
                
            bot.user_rate_limits[user_id].append(now)
            
            try:
                result = await func(ctx, *args, **kwargs)
                execution_time = time.time() - start_time
                bot.performance.record_command(command_name, execution_time, True)
                
                channel_id = getattr(ctx, 'channel_id', getattr(ctx.channel, 'id', 0))
                guild_id = getattr(ctx, 'guild_id', getattr(ctx.guild, 'id', 0) if hasattr(ctx, 'guild') and ctx.guild else 0)
                
                bot.database.log_command(
                    user_id=user_id,
                    command=command_name,
                    channel_id=channel_id,
                    guild_id=guild_id,
                    execution_time=execution_time,
                    success=True
                )
                
                return result
                
            except Exception as e:
                execution_time = time.time() - start_time
                bot.performance.record_command(command_name, execution_time, False)
                await ctx.send(f"❌ Error: {str(e)}")
                raise
        return wrapper
    return decorator

# CLEAN SLASH COMMANDS (no cybersecurity features)
@bot.tree.command(name="terminal", description="Create a secure terminal session")
async def slash_terminal(interaction: discord.Interaction):
    await interaction.response.defer()
    
    user_id = interaction.user.id
    channel_id = interaction.channel_id
    
    # Check existing
    existing = None
    for sid, term_data in bot.active_terminals.items():
        if term_data['instance'].user_id == user_id and term_data['instance'].channel_id == channel_id:
            existing = sid
            break
    
    if existing:
        embed = discord.Embed(
            title="🖥️ Using Existing Terminal",
            description=f"Session: `{existing}`",
            color=0x00ff00
        )
        await interaction.followup.send(embed=embed)
        return
    
    # Create new terminal
    terminal = CleanTerminal(user_id, channel_id)
    bot.active_terminals[terminal.session_id] = {
        'instance': terminal,
        'user': interaction.user.display_name
    }
    
    embed = discord.Embed(
        title="🖥️ Terminal Created",
        description=f"Session: `{terminal.session_id}`",
        color=0x00ff00
    )
    embed.add_field(name="Directory", value=terminal.cwd, inline=True)
    embed.add_field(name="Timeout", value=f"{config.TERMINAL_TIMEOUT//60}min", inline=True)
    embed.add_field(name="Usage", value="Use `/term <command>` to execute", inline=False)
    embed.add_field(name="Safe Commands", value="Basic file operations, git, python3, npm", inline=False)
    
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="term", description="Execute terminal command")
async def slash_term(interaction: discord.Interaction, command: str):
    await interaction.response.defer()
    
    user_id = interaction.user.id
    channel_id = interaction.channel_id
    
    # Find terminal
    terminal_session = None
    for sid, term_data in bot.active_terminals.items():
        if term_data['instance'].user_id == user_id and term_data['instance'].channel_id == channel_id:
            terminal_session = term_data['instance']
            break
    
    if not terminal_session:
        embed = discord.Embed(
            title="❌ No Terminal Session",
            description="Use `/terminal` first",
            color=0xff0000
        )
        await interaction.followup.send(embed=embed)
        return
    
    if terminal_session.is_expired():
        for sid, term_data in list(bot.active_terminals.items()):
            if term_data['instance'] == terminal_session:
                del bot.active_terminals[sid]
                break
        
        embed = discord.Embed(
            title="❌ Session Expired",
            description="Use `/terminal` to create new session",
            color=0xff0000
        )
        await interaction.followup.send(embed=embed)
        return
    
    # Execute command
    output, exit_code = await terminal_session.execute_command(command)
    
    if len(output) > config.MAX_OUTPUT_LENGTH:
        output = output[:config.MAX_OUTPUT_LENGTH] + "\n... (truncated)"
    
    color = 0x00ff00 if exit_code == 0 else 0xff0000
    embed = discord.Embed(
        title=f"🖥️ Terminal: {terminal_session.session_id}",
        color=color
    )
    embed.add_field(name="Command", value=f"```bash\n{command}\n```", inline=False)
    embed.add_field(name="Output", value=f"```\n{output}\n```", inline=False)
    embed.add_field(name="Exit Code", value=exit_code, inline=True)
    embed.add_field(name="Directory", value=terminal_session.cwd, inline=True)
    
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="agent", description="Chat with AI agent")
async def slash_agent(interaction: discord.Interaction, agent_name: str, query: str):
    await interaction.response.defer()
    
    try:
        result = subprocess.run([
            'python3', '/home/nike/ollama-agent-bridge.py',
            'agent', agent_name, query
        ], capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            response = result.stdout.strip()
            if len(response) > config.MAX_OUTPUT_LENGTH:
                response = response[:config.MAX_OUTPUT_LENGTH] + "\n... (truncated)"
                
            embed = discord.Embed(
                title=f"🤖 Agent: {agent_name}",
                description=response,
                color=0x00ff00
            )
            await interaction.followup.send(embed=embed)
        else:
            embed = discord.Embed(
                title="❌ Agent Error",
                description=result.stderr,
                color=0xff0000
            )
            await interaction.followup.send(embed=embed)
            
    except Exception as e:
        embed = discord.Embed(
            title="❌ Error",
            description=str(e),
            color=0xff0000
        )
        await interaction.followup.send(embed=embed)

@bot.tree.command(name="debug", description="Show bot debug information")
async def slash_debug(interaction: discord.Interaction):
    await interaction.response.defer()
    
    stats = bot.performance.get_stats()
    
    embed = discord.Embed(
        title="🔍 Bot Debug Information",
        description=f"Debug Mode: {'ON' if config.DEBUG_MODE else 'OFF'}",
        color=0x0099ff
    )
    
    embed.add_field(name="Performance", 
                   value=f"Commands: {stats['total_commands']}\n"
                         f"Avg Response: {stats['avg_response_time']}s\n"
                         f"Error Rate: {stats['error_rate']:.2%}", 
                   inline=True)
    
    embed.add_field(name="System", 
                   value=f"Memory: {stats['memory_usage']:.1f}%\n"
                         f"CPU: {stats['cpu_usage']:.1f}%\n"
                         f"Uptime: {stats['uptime_seconds']//3600:.1f}h", 
                   inline=True)
    
    embed.add_field(name="Bot Status", 
                   value=f"Guilds: {len(bot.guilds)}\n"
                         f"Terminals: {len(bot.active_terminals)}\n"
                         f"Features: Terminal, Webhooks, Agents", 
                   inline=True)
    
    await interaction.followup.send(embed=embed)

# Bot Events
@bot.event
async def on_ready():
    logger.info(f'🚀 {bot.user} Clean Enhanced Bot Connected!')
    logger.info(f'Connected to {len(bot.guilds)} server(s)')
    
    await bot.change_presence(
        activity=discord.Game(name="🔬 Clean PhD Research Bot | /debug")
    )
    
    bot.scheduler.start()
    logger.info("Clean bot fully operational!")

@bot.event 
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    logger.error(f"Command error: {error}")

# Cleanup task
@tasks.loop(hours=2)
async def cleanup_terminals():
    expired = []
    for sid, term_data in list(bot.active_terminals.items()):
        if term_data['instance'].is_expired():
            expired.append(sid)
            del bot.active_terminals[sid]
    
    if expired:
        logger.info(f"Cleaned up {len(expired)} expired terminals")

# Start webhook server
async def start_webhook_server():
    webhook_server = CleanWebhookServer(bot)
    runner = web.AppRunner(webhook_server.app)
    await runner.setup()
    site = web.TCPSite(runner, 'localhost', config.WEBHOOK_PORT)
    await site.start()
    logger.info(f"Clean webhook server started on port {config.WEBHOOK_PORT}")

# Main function
async def main():
    try:
        logger.info("🚀 Starting Clean Enhanced Bot...")
        
        cleanup_terminals.start()
        asyncio.create_task(start_webhook_server())
        
        await bot.start(config.TOKEN)
        
    except Exception as e:
        logger.error(f"Bot startup failed: {e}")
        raise

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot shutdown requested")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)