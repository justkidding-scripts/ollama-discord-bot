#!/usr/bin/env python3
"""
Enhanced Discord Bot with 84-Agent Integration
Bridges Discord with Ollama-Agent system for PhD research workflows
"""

import discord
from discord.ext import commands, tasks
import asyncio
import aiohttp
import json
import logging
import time
import os
import sys
from typing import Optional, Dict, Any, List
import traceback
import subprocess
import yaml
from pathlib import Path
import re

# Add Warp config path for agent integration
sys.path.append('/home/nike/.config/warp')

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/nike/ollama-discord-bot/enhanced_agent_bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class EnhancedAgentDiscordBot:
    def __init__(self, token: str, ollama_host: str = "http://localhost:11434"):
        # Discord setup
        intents = discord.Intents.default()
        intents.message_content = True
        self.bot = commands.Bot(command_prefix='!', intents=intents)
        self.token = token
        
        # Ollama setup
        self.ollama_host = ollama_host
        self.session: Optional[aiohttp.ClientSession] = None
        self.default_model = "llama3.2:3b"
        
        # Agent system integration
        self.agents_dir = Path.home() / ".config/warp/plugins/agents/agents"
        self.bridge_script = Path.home() / ".config/warp/ollama-agent-bridge.py"
        self.available_agents = self.load_available_agents()
        
        # Rate limiting and conversation management
        self.user_requests = {}
        self.rate_limit = 8  # requests per minute (increased for research use)
        self.conversations = {}
        self.max_history = 15
        self.agent_sessions = {}  # Track active agent sessions per user
        
        # Statistics
        self.stats = {
            'messages_processed': 0,
            'agent_queries': 0,
            'chain_workflows': 0,
            'research_sessions': 0,
            'errors': 0,
            'uptime_start': time.time()
        }
        
        # Agent categories for easy discovery
        self.agent_categories = {
            'security': ['security-auditor', 'backend-security-coder', 'frontend-security-coder', 'mobile-security-coder'],
            'research': ['data-scientist', 'business-analyst', 'risk-manager', 'docs-architect'],
            'coding': ['python-pro', 'javascript-pro', 'backend-architect', 'frontend-developer'],
            'analysis': ['performance-engineer', 'debugger', 'error-detective', 'test-automator'],
            'ai': ['ai-engineer', 'ml-engineer', 'mlops-engineer', 'prompt-engineer']
        }
        
        self.setup_bot_events()
        self.setup_commands()
    
    def load_available_agents(self) -> Dict[str, Dict]:
        """Load available agents from the agents directory"""
        agents = {}
        if not self.agents_dir.exists():
            logger.warning(f"Agents directory not found: {self.agents_dir}")
            return agents
        
        for agent_file in self.agents_dir.glob("*.md"):
            try:
                with open(agent_file, 'r') as f:
                    content = f.read()
                
                # Extract frontmatter
                if content.startswith('---'):
                    parts = content.split('---', 2)
                    if len(parts) >= 3:
                        frontmatter = yaml.safe_load(parts[1])
                        agent_name = agent_file.stem
                        agents[agent_name] = {
                            'name': frontmatter.get('name', agent_name),
                            'description': frontmatter.get('description', 'No description available'),
                            'model': frontmatter.get('model', 'sonnet'),
                            'prompt': parts[2].strip()
                        }
            except Exception as e:
                logger.error(f"Error loading agent {agent_file}: {e}")
        
        logger.info(f"Loaded {len(agents)} agents")
        return agents
    
    async def start_session(self):
        """Initialize aiohttp session"""
        if not self.session or self.session.closed:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=300)
            )
    
    async def close_session(self):
        """Close aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def call_agent_bridge(self, command: str, agent: str = None, query: str = None, 
                               chain: str = None, research_topic: str = None) -> str:
        """Call the Ollama-Agent bridge script"""
        try:
            cmd = ['python3', str(self.bridge_script)]
            
            if command == 'agent' and agent and query:
                cmd.extend(['--agent', agent, '--query', query])
            elif command == 'chain' and chain and query:
                cmd.extend(['--chain', chain, '--query', query])
            elif command == 'research' and research_topic:
                cmd.extend(['--research', research_topic])
            elif command == 'status':
                cmd.append('--status')
            elif command == 'models':
                cmd.append('--models')
            else:
                return "❌ Invalid command parameters"
            
            # Execute with timeout
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=120.0)
            except asyncio.TimeoutError:
                process.kill()
                return "⏰ Agent request timed out. Try a simpler query."
            
            if process.returncode == 0:
                return stdout.decode('utf-8', errors='replace').strip()
            else:
                error_msg = stderr.decode('utf-8', errors='replace').strip()
                logger.error(f"Agent bridge error: {error_msg}")
                return f"❌ Agent error: {error_msg[:200]}..."
                
        except Exception as e:
            logger.error(f"Error calling agent bridge: {e}")
            return f"❌ System error: {str(e)[:100]}..."
    
    async def check_rate_limit(self, user_id: int) -> bool:
        """Check if user is within rate limits"""
        current_time = time.time()
        user_requests = self.user_requests.get(user_id, [])
        
        # Remove requests older than 1 minute
        user_requests = [req_time for req_time in user_requests if current_time - req_time < 60]
        
        if len(user_requests) >= self.rate_limit:
            return False
        
        user_requests.append(current_time)
        self.user_requests[user_id] = user_requests
        return True
    
    async def send_long_message(self, ctx, content: str, max_length: int = 1900):
        """Send long messages by splitting them"""
        if len(content) <= max_length:
            await ctx.send(content)
            return
        
        chunks = []
        current_chunk = ""
        
        for line in content.split('\n'):
            if len(current_chunk) + len(line) + 1 > max_length:
                if current_chunk:
                    chunks.append(current_chunk)
                    current_chunk = line
                else:
                    # Line is too long, split it
                    while len(line) > max_length:
                        chunks.append(line[:max_length])
                        line = line[max_length:]
                    current_chunk = line
            else:
                current_chunk += ('\n' + line) if current_chunk else line
        
        if current_chunk:
            chunks.append(current_chunk)
        
        for i, chunk in enumerate(chunks):
            if i == 0:
                await ctx.send(chunk)
            else:
                await ctx.send(f"**[Continued {i+1}/{len(chunks)}]**\n{chunk}")
    
    def setup_bot_events(self):
        @self.bot.event
        async def on_ready():
            logger.info(f'{self.bot.user} has connected to Discord!')
            logger.info(f'Bot ID: {self.bot.user.id}')
            logger.info(f'Connected to {len(self.bot.guilds)} servers')
            
            if len(self.bot.guilds) == 0:
                logger.warning("⚠️  Bot is not connected to any servers!")
                logger.warning("Add the bot to a server using the invite link in bot_invite_link.txt")
                # Don't exit, just warn and continue
            
            await self.start_session()
            
            # Set bot status
            server_count = len(self.bot.guilds)
            status_msg = f"!help | 84 AI Agents | {server_count} servers" if server_count > 0 else "!help | Waiting for server invite"
            
            activity = discord.Activity(
                type=discord.ActivityType.listening,
                name=status_msg
            )
            await self.bot.change_presence(activity=activity)
        
        @self.bot.event
        async def on_message(message):
            if message.author == self.bot.user:
                return
            await self.bot.process_commands(message)
        
        @self.bot.event
        async def on_command_error(ctx, error):
            logger.error(f"Command error: {error}")
            self.stats['errors'] += 1
            
            if isinstance(error, commands.CommandOnCooldown):
                await ctx.send(f"⏰ Command cooldown. Try again in {error.retry_after:.1f}s")
            elif isinstance(error, commands.MissingRequiredArgument):
                await ctx.send("❌ Missing argument. Use `!help` for command info.")
            else:
                await ctx.send(f"❌ Error: {str(error)[:100]}...")
        
        @self.bot.event
        async def on_guild_join(guild):
            logger.info(f"Bot added to server: {guild.name} (ID: {guild.id})")
            # Update status to reflect new server count
            server_count = len(self.bot.guilds)
            activity = discord.Activity(
                type=discord.ActivityType.listening,
                name=f"!help | 84 AI Agents | {server_count} servers"
            )
            await self.bot.change_presence(activity=activity)
        
        @self.bot.event
        async def on_guild_remove(guild):
            logger.info(f"Bot removed from server: {guild.name} (ID: {guild.id})")
            # Update status to reflect new server count
            server_count = len(self.bot.guilds)
            status_msg = f"!help | 84 AI Agents | {server_count} servers" if server_count > 0 else "!help | Waiting for server invite"
            activity = discord.Activity(
                type=discord.ActivityType.listening,
                name=status_msg
            )
            await self.bot.change_presence(activity=activity)
    
    def setup_commands(self):
        @self.bot.command(name='agent', help='Chat with a specific AI agent')
        @commands.cooldown(1, 8, commands.BucketType.user)
        async def agent_chat(ctx, agent_name: str = None, *, query: str = None):
            """Chat with a specific agent"""
            if not agent_name:
                # Show available agents by category
                embed = discord.Embed(
                    title="🤖 Available AI Agents",
                    description="Use `!agent <name> <query>` to chat with an agent",
                    color=0x00ff00
                )
                
                for category, agents in self.agent_categories.items():
                    available = [a for a in agents if a in self.available_agents]
                    if available:
                        embed.add_field(
                            name=f"📂 {category.title()}",
                            value=", ".join(f"`{a}`" for a in available[:5]),
                            inline=False
                        )
                
                embed.add_field(
                    name="📋 Quick Examples",
                    value="`!agent security-auditor analyze this code for vulnerabilities`\n"
                          "`!agent python-pro optimize this database query`\n"
                          "`!agent data-scientist analyze fraud patterns`",
                    inline=False
                )
                
                await ctx.send(embed=embed)
                return
            
            if not query:
                await ctx.send("❌ Please provide a query. Example: `!agent security-auditor <your question>`")
                return
            
            if agent_name not in self.available_agents:
                await ctx.send(f"❌ Agent `{agent_name}` not found. Use `!agent` to see available agents.")
                return
            
            if not await self.check_rate_limit(ctx.author.id):
                await ctx.send("⏰ Rate limit exceeded. Please wait before making another request.")
                return
            
            async with ctx.typing():
                response = await self.call_agent_bridge('agent', agent=agent_name, query=query)
                
                # Create rich embed response
                agent_info = self.available_agents[agent_name]
                embed = discord.Embed(
                    title=f"🤖 {agent_info['name']}",
                    color=0x0099ff
                )
                embed.set_footer(text=f"Model: {agent_info['model']} | Requested by {ctx.author.display_name}")
                
                await self.send_long_message(ctx, response)
                self.stats['agent_queries'] += 1
        
        @self.bot.command(name='chain', help='Chain multiple agents for complex analysis')
        @commands.cooldown(1, 15, commands.BucketType.user)
        async def chain_agents(ctx, agents: str = None, *, query: str = None):
            """Chain multiple agents for complex workflows"""
            if not agents or not query:
                embed = discord.Embed(
                    title="🔗 Agent Chaining",
                    description="Chain multiple agents for complex analysis",
                    color=0xff9900
                )
                embed.add_field(
                    name="Usage",
                    value="`!chain agent1,agent2,agent3 <your query>`",
                    inline=False
                )
                embed.add_field(
                    name="Examples",
                    value="`!chain security-auditor,backend-security-coder,test-automator analyze this API`\n"
                          "`!chain data-scientist,business-analyst,risk-manager fraud detection`",
                    inline=False
                )
                embed.add_field(
                    name="Recommended Chains",
                    value="**Security**: `security-auditor,backend-security-coder`\n"
                          "**Research**: `data-scientist,business-analyst`\n"
                          "**Development**: `backend-architect,python-pro,test-automator`",
                    inline=False
                )
                await ctx.send(embed=embed)
                return
            
            if not await self.check_rate_limit(ctx.author.id):
                await ctx.send("⏰ Rate limit exceeded. Please wait before making another request.")
                return
            
            # Validate agents
            agent_list = [a.strip() for a in agents.split(',')]
            invalid_agents = [a for a in agent_list if a not in self.available_agents]
            if invalid_agents:
                await ctx.send(f"❌ Invalid agents: {', '.join(invalid_agents)}")
                return
            
            async with ctx.typing():
                await ctx.send(f"🔗 Chaining agents: {' → '.join(agent_list)}")
                response = await self.call_agent_bridge('chain', chain=agents, query=query)
                await self.send_long_message(ctx, response)
                self.stats['chain_workflows'] += 1
        
        @self.bot.command(name='research', help='Autonomous research mode with multiple agents')
        @commands.cooldown(1, 30, commands.BucketType.user)
        async def autonomous_research(ctx, *, topic: str = None):
            """Autonomous research using multiple specialized agents"""
            if not topic:
                embed = discord.Embed(
                    title="🧠 Autonomous Research Mode",
                    description="AI agents conduct independent research on your topic",
                    color=0x9900ff
                )
                embed.add_field(
                    name="Usage",
                    value="`!research <research topic>`",
                    inline=False
                )
                embed.add_field(
                    name="Examples",
                    value="`!research cryptocurrency fraud detection`\n"
                          "`!research social engineering techniques`\n"
                          "`!research advanced persistent threats`",
                    inline=False
                )
                embed.add_field(
                    name="⚠️ Note",
                    value="Research mode takes 2-5 minutes and uses multiple agents",
                    inline=False
                )
                await ctx.send(embed=embed)
                return
            
            if not await self.check_rate_limit(ctx.author.id):
                await ctx.send("⏰ Rate limit exceeded. Please wait before making another request.")
                return
            
            async with ctx.typing():
                await ctx.send(f"🧠 Starting autonomous research on: **{topic}**\n⏳ This may take 2-5 minutes...")
                response = await self.call_agent_bridge('research', research_topic=topic)
                
                embed = discord.Embed(
                    title=f"📊 Research Results: {topic}",
                    color=0x9900ff
                )
                embed.set_footer(text=f"Research completed for {ctx.author.display_name}")
                
                await self.send_long_message(ctx, response)
                self.stats['research_sessions'] += 1
        
        @self.bot.command(name='agents', help='List available agents by category')
        async def list_agents(ctx):
            """List all available agents by category"""
            embed = discord.Embed(
                title="🤖 AI Agent Directory",
                description=f"**{len(self.available_agents)} specialized agents available**",
                color=0x00ff00
            )
            
            for category, agents in self.agent_categories.items():
                available = [a for a in agents if a in self.available_agents]
                if available:
                    embed.add_field(
                        name=f"📂 {category.title()} ({len(available)} agents)",
                        value="\n".join(f"• `{a}`" for a in available),
                        inline=True
                    )
            
            embed.add_field(
                name="🚀 Quick Start",
                value="`!agent <name> <query>` - Chat with agent\n"
                      "`!chain <agents> <query>` - Multi-agent workflow\n"
                      "`!research <topic>` - Autonomous research",
                inline=False
            )
            
            await ctx.send(embed=embed)
        
        @self.bot.command(name='system', help='Check system status')
        async def system_status(ctx):
            """Show system and integration status"""
            status_response = await self.call_agent_bridge('status')
            
            embed = discord.Embed(
                title="🔧 System Status",
                color=0x0099ff
            )
            embed.add_field(name="Agents", value=f"{len(self.available_agents)} loaded", inline=True)
            embed.add_field(name="Active Sessions", value=len(self.conversations), inline=True)
            embed.add_field(name="Messages Processed", value=self.stats['messages_processed'], inline=True)
            embed.add_field(name="Agent Queries", value=self.stats['agent_queries'], inline=True)
            embed.add_field(name="Research Sessions", value=self.stats['research_sessions'], inline=True)
            embed.add_field(name="Chain Workflows", value=self.stats['chain_workflows'], inline=True)
            
            uptime = time.time() - self.stats['uptime_start']
            embed.add_field(name="Uptime", value=f"{uptime/3600:.1f} hours", inline=False)
            embed.add_field(name="Ollama Status", value=status_response[:100], inline=False)
            
            await ctx.send(embed=embed)
        
        @self.bot.command(name='models', help='List available AI models')
        async def list_models(ctx):
            """List available Ollama models"""
            models_response = await self.call_agent_bridge('models')
            
            embed = discord.Embed(
                title="🤖 Available AI Models",
                description=models_response,
                color=0x00ff00
            )
            
            await ctx.send(embed=embed)
    
    async def run(self):
        """Run the bot"""
        try:
            await self.bot.start(self.token)
        except Exception as e:
            logger.error(f"Bot error: {e}")
        finally:
            await self.close_session()

async def main():
    # Load configuration
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        logger.error("DISCORD_TOKEN environment variable not set")
        return
    
    ollama_host = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
    
    # Create and run bot
    bot = EnhancedAgentDiscordBot(token, ollama_host)
    await bot.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot shutdown requested")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        traceback.print_exc()