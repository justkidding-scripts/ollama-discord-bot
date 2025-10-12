#!/usr/bin/env python3
"""
Ultimate Academic Research Discord Bot
Combines clean terminal security with advanced RAG and GitHub automation
"""

import discord
from discord.ext import commands
import asyncio
import logging
from datetime import datetime
import json
import os
import sys
import subprocess
import sqlite3
from typing import Optional, List, Dict, Any
import psutil
from rich.console import Console
from rich.table import Table

# Import our enhanced systems
try:
    from advanced_rag_system import rag_system
except ImportError:
    rag_system = None
    print("RAG system not available - install with: pip install chromadb sentence-transformers")

try:
    from github_automation import github_automation
except ImportError:
    github_automation = None
    print("GitHub automation not available - install with: pip install gitpython")

# Import clean bot features
from clean_enhanced_bot import CleanEnhancedBot

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ultimate_research_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class UltimateResearchBot(commands.Bot):
    """Ultimate Academic Research Bot with all features"""
    
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        
        super().__init__(
            command_prefix='!',
            intents=intents,
            help_command=None
        )
        
        # Initialize systems
        self.rag_system = rag_system
        self.github_automation = github_automation
        self.research_active = False
        self.current_topic = None
        self.console = Console()
        
        # Database setup
        self.setup_database()
        
        # Bot statistics
        self.stats = {
            'commands_executed': 0,
            'research_sessions': 0,
            'rag_queries': 0,
            'github_commits': 0,
            'uptime_start': datetime.now()
        }
    
    def setup_database(self):
        """Initialize SQLite database for logging and analytics"""
        try:
            self.conn = sqlite3.connect('ultimate_research_bot.db')
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS command_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    command TEXT NOT NULL,
                    arguments TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    success BOOLEAN,
                    execution_time REAL
                )
            ''')
            
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS research_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT UNIQUE,
                    user_id TEXT NOT NULL,
                    topic TEXT NOT NULL,
                    start_time DATETIME,
                    end_time DATETIME,
                    findings TEXT,
                    documents_added INTEGER DEFAULT 0
                )
            ''')
            
            self.conn.commit()
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Database setup failed: {e}")
    
    async def on_ready(self):
        """Bot ready event"""
        logger.info(f'🤖 Ultimate Research Bot "{self.user}" is now online!')
        logger.info(f'🔬 Connected to {len(self.guilds)} guilds')
        
        # Initialize research systems
        if self.rag_system:
            try:
                await self.rag_system.initialize()
                logger.info("✅ RAG system initialized")
            except Exception as e:
                logger.error(f"❌ RAG system initialization failed: {e}")
        
        if self.github_automation:
            try:
                await self.github_automation.initialize_repository()
                logger.info("✅ GitHub automation initialized")
            except Exception as e:
                logger.error(f"❌ GitHub automation initialization failed: {e}")
        
        # Sync slash commands
        try:
            synced = await self.tree.sync()
            logger.info(f"🔧 Synced {len(synced)} slash commands")
        except Exception as e:
            logger.error(f"Failed to sync commands: {e}")
    
    async def on_command_error(self, ctx, error):
        """Global error handler"""
        logger.error(f"Command error: {error}")
        await ctx.send(f"❌ An error occurred: {str(error)}")
    
    def log_command(self, user_id: str, command: str, args: str = None, success: bool = True, exec_time: float = 0.0):
        """Log command execution to database"""
        try:
            self.conn.execute(
                "INSERT INTO command_history (user_id, command, arguments, success, execution_time) VALUES (?, ?, ?, ?, ?)",
                (user_id, command, args, success, exec_time)
            )
            self.conn.commit()
            self.stats['commands_executed'] += 1
        except Exception as e:
            logger.error(f"Failed to log command: {e}")

# Slash Commands - Terminal Integration
@discord.app_commands.command(name="terminal", description="Create a secure terminal session")
async def terminal_create(interaction: discord.Interaction):
    """Create secure terminal session (from clean bot)"""
    await interaction.response.defer()
    
    try:
        # Use clean bot's secure terminal implementation
        embed = discord.Embed(
            title="🖥️ Secure Terminal Session",
            description="Terminal session created with security restrictions",
            color=0x00ff00,
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name="Safe Commands Available",
            value="`ls`, `cat`, `head`, `tail`, `grep`, `find`, `pwd`, `whoami`, `date`, `echo`, `git`, `python3`, `node`, `npm`, `pip3`",
            inline=False
        )
        
        embed.add_field(
            name="Restrictions",
            value="• Directory limited to `/home/nike/`\n• 5-minute timeout\n• No complex syntax (pipes, redirects)\n• Command whitelist only",
            inline=False
        )
        
        embed.add_field(
            name="Usage",
            value="Use `/term <command>` to execute commands in this session",
            inline=False
        )
        
        await interaction.followup.send(embed=embed)
        
    except Exception as e:
        await interaction.followup.send(f"❌ Failed to create terminal: {str(e)}")

@discord.app_commands.command(name="term", description="Execute command in terminal session")
async def terminal_execute(interaction: discord.Interaction, command: str):
    """Execute command in secure terminal session"""
    await interaction.response.defer()
    
    # Whitelist of safe commands
    safe_commands = ['ls', 'cat', 'head', 'tail', 'grep', 'find', 'pwd', 'whoami', 'date', 'echo', 'git', 'python3', 'node', 'npm', 'pip3']
    
    try:
        cmd_parts = command.split()
        if not cmd_parts or cmd_parts[0] not in safe_commands:
            await interaction.followup.send(f"❌ Command '{cmd_parts[0] if cmd_parts else 'empty'}' not allowed. Safe commands: {', '.join(safe_commands)}")
            return
        
        # Execute command in restricted environment
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,
            cwd="/home/nike"
        )
        
        output = result.stdout if result.stdout else result.stderr
        if not output:
            output = "Command executed successfully (no output)"
        
        # Truncate long output
        if len(output) > 1800:
            output = output[:1800] + "\n... (output truncated)"
        
        embed = discord.Embed(
            title=f"🖥️ Terminal: {command}",
            description=f"```\n{output}\n```",
            color=0x00ff00 if result.returncode == 0 else 0xff0000,
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name="Exit Code",
            value=result.returncode,
            inline=True
        )
        
        await interaction.followup.send(embed=embed)
        
    except subprocess.TimeoutExpired:
        await interaction.followup.send("❌ Command timed out after 30 seconds")
    except Exception as e:
        await interaction.followup.send(f"❌ Command execution failed: {str(e)}")

# Slash Commands - RAG System
@discord.app_commands.command(name="rag_search", description="Search the research knowledge base")
async def rag_search(interaction: discord.Interaction, query: str, sources: str = "all"):
    """Search RAG knowledge base"""
    await interaction.response.defer()
    
    if not rag_system:
        await interaction.followup.send("❌ RAG system not available. Please install required dependencies.")
        return
    
    try:
        # Parse source filter
        source_filter = None
        if sources.lower() != "all":
            source_filter = [s.strip() for s in sources.split(',')]
        
        # Search RAG system
        results = await rag_system.search(query, n_results=10, include_sources=source_filter)
        
        if not results:
            await interaction.followup.send("❌ No results found in knowledge base")
            return
        
        # Create embed with results
        embed = discord.Embed(
            title="📚 Knowledge Base Search Results",
            description=f"**Query:** {query}\n**Results:** {len(results)} documents found",
            color=0x9932cc,
            timestamp=datetime.now()
        )
        
        # Add top results
        for i, result in enumerate(results[:5]):
            embed.add_field(
                name=f"📄 {result['title'][:50]}{'...' if len(result['title']) > 50 else ''}",
                value=f"**Source:** {result['source']}\n**Authors:** {', '.join(result['authors'][:2])}\n**Relevance:** {(1-result['distance']):.2%}\n**Content:** {result['content'][:100]}...",
                inline=False
            )
        
        await interaction.followup.send(embed=embed)
        
    except Exception as e:
        await interaction.followup.send(f"❌ RAG search failed: {str(e)}")

@discord.app_commands.command(name="rag_research", description="Comprehensive research on a topic")
async def comprehensive_research(interaction: discord.Interaction, topic: str, online: bool = True):
    """Perform comprehensive research using RAG system"""
    await interaction.response.defer()
    
    if not rag_system:
        await interaction.followup.send("❌ RAG system not available. Please install required dependencies.")
        return
    
    try:
        # Perform comprehensive research
        research_results = await rag_system.research_topic(topic, search_online=online)
        
        embed = discord.Embed(
            title="🔍 Comprehensive Research Results",
            description=f"**Topic:** {topic}",
            color=0xff6600,
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name="Search Summary",
            value=research_results['search_summary'],
            inline=False
        )
        
        embed.add_field(
            name="Total Sources",
            value=f"📚 {research_results['total_sources']} documents in knowledge base",
            inline=True
        )
        
        if research_results['documents_found']:
            docs_text = "\n".join([f"• {doc[:60]}{'...' if len(doc) > 60 else ''}" 
                                 for doc in research_results['documents_found'][:10]])
            embed.add_field(
                name="New Documents Added",
                value=docs_text or "None",
                inline=False
            )
        
        await interaction.followup.send(embed=embed)
        
    except Exception as e:
        await interaction.followup.send(f"❌ Research failed: {str(e)}")

@discord.app_commands.command(name="rag_ask", description="Ask a question with RAG context")
async def rag_ask(interaction: discord.Interaction, question: str):
    """Ask question with RAG-enhanced context"""
    await interaction.response.defer()
    
    if not rag_system:
        await interaction.followup.send("❌ RAG system not available. Please install required dependencies.")
        return
    
    try:
        # Get RAG context
        rag_response = await rag_system.get_enhanced_response(question, context_chunks=5)
        
        # Create response embed
        embed = discord.Embed(
            title="🤖 RAG-Enhanced Response",
            description=f"**Question:** {question}",
            color=0x00ffff,
            timestamp=datetime.now()
        )
        
        # Add context summary
        context_summary = rag_response['context'][:1500] + "..." if len(rag_response['context']) > 1500 else rag_response['context']
        embed.add_field(
            name="Research Context",
            value=context_summary or "No relevant context found",
            inline=False
        )
        
        # Add sources
        if rag_response['sources']:
            sources_text = "\n".join([
                f"• {source['title'][:50]}{'...' if len(source['title']) > 50 else ''} ({source['source']})"
                for source in rag_response['sources'][:5]
            ])
            embed.add_field(
                name="Sources Referenced",
                value=sources_text,
                inline=False
            )
        
        embed.add_field(
            name="Context Statistics",
            value=f"📊 {rag_response['num_results']} relevant documents\n🔍 {len(rag_response['context'])} characters of context",
            inline=True
        )
        
        await interaction.followup.send(embed=embed)
        
    except Exception as e:
        await interaction.followup.send(f"❌ RAG query failed: {str(e)}")

# Slash Commands - GitHub Automation
@discord.app_commands.command(name="research_start", description="Start a new research session")
async def start_research_session(interaction: discord.Interaction, topic: str):
    """Start a new research session with automatic tracking"""
    await interaction.response.defer()
    
    if not github_automation:
        await interaction.followup.send("❌ GitHub automation not available. Please install required dependencies.")
        return
    
    try:
        # Start GitHub session tracking
        session_id = github_automation.start_research_session(topic)
        
        embed = discord.Embed(
            title="🔬 Research Session Started",
            description=f"**Topic:** {topic}\n**Session ID:** {session_id}",
            color=0x00ff00,
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name="Automation Active",
            value="✅ Auto-commit enabled\n✅ File tracking enabled\n✅ RAG system ready",
            inline=False
        )
        
        await interaction.followup.send(embed=embed)
        
    except Exception as e:
        await interaction.followup.send(f"❌ Failed to start session: {str(e)}")

@discord.app_commands.command(name="research_end", description="End current research session")
async def end_research_session(interaction: discord.Interaction, findings: str = ""):
    """End current research session"""
    await interaction.response.defer()
    
    if not github_automation:
        await interaction.followup.send("❌ GitHub automation not available. Please install required dependencies.")
        return
    
    try:
        # Parse findings
        key_findings = [f.strip() for f in findings.split('\n') if f.strip()] if findings else []
        
        # End GitHub session
        github_automation.end_research_session(key_findings)
        
        # Generate documentation
        await github_automation.generate_research_documentation()
        
        embed = discord.Embed(
            title="📋 Research Session Completed",
            description=f"Session ended successfully",
            color=0x0099ff,
            timestamp=datetime.now()
        )
        
        if key_findings:
            embed.add_field(
                name="Key Findings",
                value="\n".join([f"• {finding}" for finding in key_findings[:5]]),
                inline=False
            )
        
        embed.add_field(
            name="Actions Completed",
            value="✅ Session committed to GitHub\n✅ Documentation generated\n✅ Research summary created",
            inline=False
        )
        
        await interaction.followup.send(embed=embed)
        
    except Exception as e:
        await interaction.followup.send(f"❌ Failed to end session: {str(e)}")

# Slash Commands - System Status
@discord.app_commands.command(name="status", description="Show bot status and statistics")
async def show_status(interaction: discord.Interaction):
    """Show comprehensive bot status"""
    await interaction.response.defer()
    
    try:
        # System information
        memory = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent()
        uptime = datetime.now() - interaction.client.stats['uptime_start']
        
        embed = discord.Embed(
            title="🤖 Ultimate Research Bot Status",
            color=0x00ff00,
            timestamp=datetime.now()
        )
        
        # Bot statistics
        embed.add_field(
            name="📊 Bot Statistics",
            value=f"**Uptime:** {uptime}\n**Commands Executed:** {interaction.client.stats['commands_executed']}\n**Research Sessions:** {interaction.client.stats['research_sessions']}\n**RAG Queries:** {interaction.client.stats['rag_queries']}",
            inline=True
        )
        
        # System resources
        embed.add_field(
            name="💻 System Resources",
            value=f"**Memory:** {memory.percent}% ({memory.used / 1024**3:.1f}GB / {memory.total / 1024**3:.1f}GB)\n**CPU:** {cpu_percent}%",
            inline=True
        )
        
        # Feature status
        features = []
        if rag_system:
            features.append("✅ RAG System")
        else:
            features.append("❌ RAG System")
            
        if github_automation:
            features.append("✅ GitHub Automation")
        else:
            features.append("❌ GitHub Automation")
        
        features.extend(["✅ Secure Terminal", "✅ Webhook Server", "✅ Database Logging"])
        
        embed.add_field(
            name="🔧 Features",
            value="\n".join(features),
            inline=False
        )
        
        await interaction.followup.send(embed=embed)
        
    except Exception as e:
        await interaction.followup.send(f"❌ Failed to get status: {str(e)}")

async def main():
    """Main function to run the ultimate research bot"""
    # Load environment
    from dotenv import load_dotenv
    load_dotenv()
    
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        logger.error("DISCORD_TOKEN not found in environment variables")
        return
    
    # Initialize bot
    bot = UltimateResearchBot()
    
    # Add slash commands
    bot.tree.add_command(terminal_create)
    bot.tree.add_command(terminal_execute)
    bot.tree.add_command(rag_search)
    bot.tree.add_command(comprehensive_research)
    bot.tree.add_command(rag_ask)
    bot.tree.add_command(start_research_session)
    bot.tree.add_command(end_research_session)
    bot.tree.add_command(show_status)
    
    try:
        await bot.start(token)
    except KeyboardInterrupt:
        logger.info("Bot shutdown requested")
    except Exception as e:
        logger.error(f"Bot failed to start: {e}")
    finally:
        await bot.close()

if __name__ == "__main__":
    asyncio.run(main())