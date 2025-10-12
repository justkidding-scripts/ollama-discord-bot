#!/usr/bin/env python3
"""
🚀 Advanced Bot Launcher & Management System
A comprehensive interface to manage, organize, and extend Discord bots

Features:
- Bot lifecycle management (start/stop/restart)
- Dynamic command creation and management
- GitHub repository integration for extensions
- Module system for custom functionality
- Configuration management
- Performance monitoring
- Development tools
"""

import os
import sys
import json
import subprocess
import asyncio
import aiohttp
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Any
import time
from datetime import datetime
import sqlite3
import shutil
import git
from dataclasses import dataclass, asdict
import yaml
import logging
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.tree import Tree
from rich.syntax import Syntax

# Initialize Rich console
console = Console()

# Configuration
@dataclass
class BotConfig:
    name: str
    description: str
    main_file: str
    port: int
    status: str
    pid: Optional[int] = None
    created_at: str = ""
    last_modified: str = ""
    modules: List[str] = None
    github_repos: List[str] = None
    
    def __post_init__(self):
        if self.modules is None:
            self.modules = []
        if self.github_repos is None:
            self.github_repos = []

class BotLauncher:
    def __init__(self, workspace_dir: str = "/home/nike/clean-discord-bot"):
        self.workspace_dir = Path(workspace_dir)
        self.config_file = self.workspace_dir / "launcher_config.json"
        self.modules_dir = self.workspace_dir / "modules"
        self.extensions_dir = self.workspace_dir / "extensions"
        self.templates_dir = self.workspace_dir / "templates"
        self.db_file = self.workspace_dir / "launcher.db"
        
        # Create directories
        self.modules_dir.mkdir(exist_ok=True)
        self.extensions_dir.mkdir(exist_ok=True)
        self.templates_dir.mkdir(exist_ok=True)
        
        # Initialize database
        self.init_database()
        
        # Load configuration
        self.bots: Dict[str, BotConfig] = self.load_config()
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.workspace_dir / 'launcher.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def init_database(self):
        """Initialize SQLite database for tracking bot operations"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        # Bot tracking table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bot_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bot_name TEXT,
                action TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                details TEXT,
                success BOOLEAN
            )
        ''')
        
        # Module tracking table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS module_registry (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                module_name TEXT,
                module_type TEXT,
                source_repo TEXT,
                install_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                version TEXT,
                dependencies TEXT
            )
        ''')
        
        # Command tracking table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS custom_commands (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bot_name TEXT,
                command_name TEXT,
                command_code TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                active BOOLEAN DEFAULT TRUE
            )
        ''')
        
        conn.commit()
        conn.close()

    def log_action(self, bot_name: str, action: str, details: str, success: bool = True):
        """Log bot actions to database"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO bot_history (bot_name, action, details, success)
            VALUES (?, ?, ?, ?)
        ''', (bot_name, action, details, success))
        conn.commit()
        conn.close()

    def load_config(self) -> Dict[str, BotConfig]:
        """Load bot configurations from file"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    return {name: BotConfig(**config) for name, config in data.items()}
            except Exception as e:
                console.print(f"[red]Error loading config: {e}[/red]")
                return {}
        return {}

    def save_config(self):
        """Save bot configurations to file"""
        try:
            data = {name: asdict(config) for name, config in self.bots.items()}
            with open(self.config_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            console.print(f"[red]Error saving config: {e}[/red]")

    def display_main_menu(self):
        """Display the main launcher interface"""
        console.clear()
        
        # Title banner
        console.print(Panel.fit(
            "[bold blue]🚀 Advanced Discord Bot Launcher & Management System[/bold blue]\n"
            "[dim]Organize • Customize • Extend • Monitor[/dim]",
            border_style="blue"
        ))
        
        # Bot status overview
        table = Table(title="📊 Bot Status Overview", show_header=True)
        table.add_column("Bot Name", style="cyan")
        table.add_column("Status", justify="center")
        table.add_column("PID", justify="center")
        table.add_column("Main File", style="dim")
        table.add_column("Port", justify="center")
        table.add_column("Modules", justify="center")
        
        for name, config in self.bots.items():
            status_icon = "🟢" if config.status == "running" else "🔴"
            status_text = f"{status_icon} {config.status}"
            pid_text = str(config.pid) if config.pid else "-"
            modules_count = str(len(config.modules))
            
            table.add_row(
                name, status_text, pid_text, 
                config.main_file, str(config.port), modules_count
            )
        
        if not self.bots:
            table.add_row("No bots configured", "-", "-", "-", "-", "-")
        
        console.print(table)
        console.print()

    def display_menu_options(self):
        """Display menu options"""
        console.print("[bold cyan]🎯 Main Menu Options:[/bold cyan]")
        console.print("1. 🤖 Bot Management (start/stop/create)")
        console.print("2. ⚡ Command Creator (add custom commands)")
        console.print("3. 🧩 Module Manager (install/manage extensions)")
        console.print("4. 🐙 GitHub Integration (clone repos, sync)")
        console.print("5. 🔧 Configuration Editor")
        console.print("6. 📊 Performance Monitor")
        console.print("7. 🛠️  Development Tools")
        console.print("8. 📁 Workspace Manager")
        console.print("9. 📋 System Information")
        console.print("0. 🚪 Exit")
        console.print()

    # Bot Management Functions
    def bot_management_menu(self):
        """Bot management submenu"""
        while True:
            console.clear()
            console.print(Panel.fit("[bold green]🤖 Bot Management Center[/bold green]"))
            
            # Show current bots
            self.display_bot_list()
            
            console.print("[bold cyan]Bot Management Options:[/bold cyan]")
            console.print("1. 🚀 Start Bot")
            console.print("2. ⏹️  Stop Bot")
            console.print("3. 🔄 Restart Bot")
            console.print("4. ➕ Create New Bot")
            console.print("5. 🗑️  Delete Bot")
            console.print("6. 📊 Bot Details")
            console.print("0. ⬅️  Back to Main Menu")
            
            choice = Prompt.ask("Choose option", choices=["0", "1", "2", "3", "4", "5", "6"])
            
            if choice == "0":
                break
            elif choice == "1":
                self.start_bot()
            elif choice == "2":
                self.stop_bot()
            elif choice == "3":
                self.restart_bot()
            elif choice == "4":
                self.create_new_bot()
            elif choice == "5":
                self.delete_bot()
            elif choice == "6":
                self.show_bot_details()

    def display_bot_list(self):
        """Display list of bots with status"""
        if not self.bots:
            console.print("[yellow]No bots configured yet.[/yellow]")
            return
            
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Name")
        table.add_column("Status")
        table.add_column("Port")
        table.add_column("Modules")
        
        for name, config in self.bots.items():
            status = "🟢 Running" if config.status == "running" else "🔴 Stopped"
            table.add_row(name, status, str(config.port), str(len(config.modules)))
        
        console.print(table)
        console.print()

    def start_bot(self):
        """Start a bot"""
        if not self.bots:
            console.print("[yellow]No bots configured.[/yellow]")
            return
            
        bot_name = Prompt.ask("Enter bot name to start", choices=list(self.bots.keys()))
        config = self.bots[bot_name]
        
        if config.status == "running":
            console.print(f"[yellow]Bot {bot_name} is already running.[/yellow]")
            return
        
        try:
            # Check if main file exists
            main_file_path = self.workspace_dir / config.main_file
            if not main_file_path.exists():
                console.print(f"[red]Main file {config.main_file} not found![/red]")
                return
            
            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
                task = progress.add_task(f"Starting {bot_name}...", total=None)
                
                # Start the bot process
                process = subprocess.Popen([
                    sys.executable, str(main_file_path)
                ], cwd=self.workspace_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                
                # Wait a moment to check if it started successfully
                time.sleep(2)
                if process.poll() is None:
                    config.status = "running"
                    config.pid = process.pid
                    self.save_config()
                    self.log_action(bot_name, "start", f"Started with PID {process.pid}")
                    console.print(f"[green]✅ Bot {bot_name} started successfully! (PID: {process.pid})[/green]")
                else:
                    stdout, stderr = process.communicate()
                    error_msg = stderr.decode() if stderr else "Unknown error"
                    console.print(f"[red]❌ Failed to start {bot_name}: {error_msg}[/red]")
                    self.log_action(bot_name, "start", f"Failed: {error_msg}", False)
                    
        except Exception as e:
            console.print(f"[red]Error starting bot: {e}[/red]")
            self.log_action(bot_name, "start", f"Exception: {e}", False)
        
        input("\nPress Enter to continue...")

    def stop_bot(self):
        """Stop a running bot"""
        running_bots = {name: config for name, config in self.bots.items() if config.status == "running"}
        
        if not running_bots:
            console.print("[yellow]No running bots to stop.[/yellow]")
            return
        
        bot_name = Prompt.ask("Enter bot name to stop", choices=list(running_bots.keys()))
        config = self.bots[bot_name]
        
        try:
            if config.pid:
                os.kill(config.pid, 9)  # Force kill
                config.status = "stopped"
                config.pid = None
                self.save_config()
                self.log_action(bot_name, "stop", "Stopped successfully")
                console.print(f"[green]✅ Bot {bot_name} stopped successfully![/green]")
            else:
                console.print(f"[yellow]No PID found for {bot_name}[/yellow]")
        except Exception as e:
            console.print(f"[red]Error stopping bot: {e}[/red]")
            self.log_action(bot_name, "stop", f"Error: {e}", False)
        
        input("\nPress Enter to continue...")

    def restart_bot(self):
        """Restart a bot"""
        if not self.bots:
            console.print("[yellow]No bots configured.[/yellow]")
            return
        
        bot_name = Prompt.ask("Enter bot name to restart", choices=list(self.bots.keys()))
        
        # Stop if running
        if self.bots[bot_name].status == "running":
            console.print(f"Stopping {bot_name}...")
            self.bots[bot_name].status = "stopped"
            if self.bots[bot_name].pid:
                try:
                    os.kill(self.bots[bot_name].pid, 9)
                except:
                    pass
            time.sleep(1)
        
        # Start again
        console.print(f"Starting {bot_name}...")
        # Use the same logic as start_bot but without user input
        config = self.bots[bot_name]
        try:
            main_file_path = self.workspace_dir / config.main_file
            process = subprocess.Popen([
                sys.executable, str(main_file_path)
            ], cwd=self.workspace_dir)
            
            time.sleep(2)
            if process.poll() is None:
                config.status = "running"
                config.pid = process.pid
                self.save_config()
                self.log_action(bot_name, "restart", f"Restarted with PID {process.pid}")
                console.print(f"[green]✅ Bot {bot_name} restarted successfully![/green]")
            else:
                console.print(f"[red]❌ Failed to restart {bot_name}[/red]")
        except Exception as e:
            console.print(f"[red]Error restarting bot: {e}[/red]")
        
        input("\nPress Enter to continue...")

    def delete_bot(self):
        """Delete a bot configuration"""
        if not self.bots:
            console.print("[yellow]No bots to delete.[/yellow]")
            return
        
        bot_name = Prompt.ask("Enter bot name to delete", choices=list(self.bots.keys()))
        
        # Confirm deletion
        if not Confirm.ask(f"Are you sure you want to delete {bot_name}? This will remove the configuration but not the bot file."):
            return
        
        # Stop bot if running
        if self.bots[bot_name].status == "running":
            console.print(f"Stopping {bot_name} before deletion...")
            if self.bots[bot_name].pid:
                try:
                    os.kill(self.bots[bot_name].pid, 9)
                except:
                    pass
        
        # Remove from configuration
        del self.bots[bot_name]
        self.save_config()
        self.log_action(bot_name, "delete", "Configuration deleted")
        
        console.print(f"[green]✅ Bot {bot_name} deleted successfully![/green]")
        input("\nPress Enter to continue...")

    def show_bot_details(self):
        """Create a new bot from template"""
        console.print("[bold cyan]🛠️  Creating New Discord Bot[/bold cyan]")
        
        # Get bot details
        name = Prompt.ask("Bot name")
        if name in self.bots:
            console.print(f"[red]Bot {name} already exists![/red]")
            return
        
        description = Prompt.ask("Bot description")
        port = int(Prompt.ask("Webhook port", default="8086"))
        
        # Choose template
        templates = self.get_available_templates()
        console.print("\nAvailable templates:")
        for i, template in enumerate(templates, 1):
            console.print(f"{i}. {template}")
        
        template_choice = int(Prompt.ask("Choose template", choices=[str(i) for i in range(1, len(templates)+1)]))
        template_name = templates[template_choice - 1]
        
        # Create bot file
        main_file = f"{name}_bot.py"
        self.create_bot_from_template(name, template_name, port)
        
        # Add to configuration
        self.bots[name] = BotConfig(
            name=name,
            description=description,
            main_file=main_file,
            port=port,
            status="stopped",
            created_at=datetime.now().isoformat()
        )
        
        self.save_config()
        self.log_action(name, "create", f"Created from template {template_name}")
        
        console.print(f"[green]✅ Bot {name} created successfully![/green]")
        input("\nPress Enter to continue...")

    def get_available_templates(self) -> List[str]:
        """Get list of available bot templates"""
        templates = ["clean_enhanced", "basic", "research_assistant", "minimal"]
        
        # Check for custom templates
        if self.templates_dir.exists():
            custom_templates = [f.stem for f in self.templates_dir.glob("*.py")]
            templates.extend(custom_templates)
        
        return templates

    def create_bot_from_template(self, bot_name: str, template: str, port: int):
        """Create bot file from template"""
        if template == "clean_enhanced":
            # Copy the existing clean bot as template
            shutil.copy2(self.workspace_dir / "clean_enhanced_bot.py", 
                        self.workspace_dir / f"{bot_name}_bot.py")
        elif template == "basic":
            self.create_basic_bot_template(bot_name, port)
        elif template == "research_assistant":
            self.create_research_assistant_template(bot_name, port)
        elif template == "minimal":
            self.create_minimal_bot_template(bot_name, port)
        else:
            # Custom template
            template_file = self.templates_dir / f"{template}.py"
            if template_file.exists():
                shutil.copy2(template_file, self.workspace_dir / f"{bot_name}_bot.py")

    def create_basic_bot_template(self, bot_name: str, port: int):
        """Create a basic bot template"""
        template_code = f'''#!/usr/bin/env python3
"""
Basic Discord Bot - {bot_name}
Generated by Bot Launcher System
"""

import discord
from discord.ext import commands
import asyncio
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BasicBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        
        super().__init__(
            command_prefix='!',
            intents=intents,
            help_command=None
        )

    async def on_ready(self):
        logger.info(f'{{self.user}} has connected to Discord!')
        await self.change_presence(
            activity=discord.Game(name="🤖 {bot_name} | !help")
        )

# Create bot instance
bot = BasicBot()

# Basic commands
@bot.command(name='hello')
async def hello(ctx):
    """Say hello"""
    await ctx.send(f'Hello {{ctx.author.mention}}! I am {bot_name}.')

@bot.command(name='info')
async def info(ctx):
    """Show bot information"""
    embed = discord.Embed(
        title="{bot_name}",
        description="A basic Discord bot created with Bot Launcher",
        color=0x00ff00,
        timestamp=datetime.now()
    )
    embed.add_field(name="Created", value="{datetime.now().strftime('%Y-%m-%d')}", inline=True)
    embed.add_field(name="Guilds", value=str(len(bot.guilds)), inline=True)
    await ctx.send(embed=embed)

if __name__ == '__main__':
    import os
    TOKEN = os.getenv('DISCORD_TOKEN')
    if TOKEN:
        bot.run(TOKEN)
    else:
        logger.error("DISCORD_TOKEN environment variable not set!")
'''
        
        with open(self.workspace_dir / f"{bot_name}_bot.py", 'w') as f:
            f.write(template_code)

    def create_minimal_bot_template(self, bot_name: str, port: int):
        """Create a minimal bot template"""
        template_code = f'''#!/usr/bin/env python3
"""
Minimal Discord Bot - {bot_name}
"""

import discord
import os

client = discord.Client(intents=discord.Intents.default())

@client.event
async def on_ready():
    print(f'{{client.user}} has connected to Discord!')

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    
    if message.content == '!ping':
        await message.channel.send('Pong!')

if __name__ == '__main__':
    TOKEN = os.getenv('DISCORD_TOKEN')
    if TOKEN:
        client.run(TOKEN)
    else:
        print("DISCORD_TOKEN environment variable not set!")
'''
        
        with open(self.workspace_dir / f"{bot_name}_bot.py", 'w') as f:
            f.write(template_code)

    def create_research_assistant_template(self, bot_name: str, port: int):
        """Create a research assistant bot template"""
        template_code = f'''#!/usr/bin/env python3
"""
Research Assistant Discord Bot - {bot_name}
Generated by Bot Launcher System
"""

import discord
from discord.ext import commands
import asyncio
import logging
from datetime import datetime
import sqlite3
import aiohttp
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ResearchBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        
        super().__init__(
            command_prefix='!',
            intents=intents,
            help_command=None
        )
        
        # Initialize research database
        self.init_research_db()

    def init_research_db(self):
        conn = sqlite3.connect('research_data.db')
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS research_notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                title TEXT,
                content TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()

    async def on_ready(self):
        logger.info(f'{{self.user}} Research Assistant Ready!')
        await self.change_presence(
            activity=discord.Game(name="🔬 {bot_name} Research Assistant | !help")
        )

# Create bot instance
bot = ResearchBot()

# Research commands
@bot.command(name='note')
async def add_note(ctx, title: str, *, content: str):
    """Add a research note"""
    conn = sqlite3.connect('research_data.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO research_notes (user_id, title, content)
        VALUES (?, ?, ?)
    ''', (ctx.author.id, title, content))
    conn.commit()
    conn.close()
    
    await ctx.send(f"📝 Research note '{{title}}' saved!")

@bot.command(name='notes')
async def list_notes(ctx):
    """List research notes"""
    conn = sqlite3.connect('research_data.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT title, timestamp FROM research_notes 
        WHERE user_id = ? ORDER BY timestamp DESC LIMIT 10
    ''', (ctx.author.id,))
    
    results = cursor.fetchall()
    conn.close()
    
    if results:
        embed = discord.Embed(title="📚 Your Research Notes", color=0x00ff00)
        for title, timestamp in results:
            embed.add_field(name=title, value=timestamp[:10], inline=False)
        await ctx.send(embed=embed)
    else:
        await ctx.send("No research notes found. Use `!note <title> <content>` to add one.")

@bot.command(name='search')
async def search_notes(ctx, *, query: str):
    """Search research notes"""
    conn = sqlite3.connect('research_data.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT title, content FROM research_notes 
        WHERE user_id = ? AND (title LIKE ? OR content LIKE ?)
    ''', (ctx.author.id, f"%{{query}}%", f"%{{query}}%"))
    
    results = cursor.fetchall()
    conn.close()
    
    if results:
        embed = discord.Embed(title=f"🔍 Search Results for '{{query}}'", color=0x0099ff)
        for title, content in results[:5]:  # Limit to 5 results
            content_preview = content[:100] + "..." if len(content) > 100 else content
            embed.add_field(name=title, value=content_preview, inline=False)
        await ctx.send(embed=embed)
    else:
        await ctx.send(f"No notes found matching '{{query}}'.")

if __name__ == '__main__':
    import os
    TOKEN = os.getenv('DISCORD_TOKEN')
    if TOKEN:
        bot.run(TOKEN)
    else:
        logger.error("DISCORD_TOKEN environment variable not set!")
'''
        
        with open(self.workspace_dir / f"{bot_name}_bot.py", 'w') as f:
            f.write(template_code)

    def show_bot_details(self):
        """Show detailed information about a bot"""
        if not self.bots:
            console.print("[yellow]No bots configured.[/yellow]")
            return
        
        bot_name = Prompt.ask("Enter bot name", choices=list(self.bots.keys()))
        config = self.bots[bot_name]
        
        console.clear()
        console.print(Panel.fit(f"[bold cyan]🤖 Bot Details: {bot_name}[/bold cyan]"))
        
        # Basic info table
        table = Table(show_header=False, box=None)
        table.add_column("Property", style="bold")
        table.add_column("Value")
        
        table.add_row("Name", config.name)
        table.add_row("Description", config.description)
        table.add_row("Main File", config.main_file)
        table.add_row("Port", str(config.port))
        table.add_row("Status", f"🟢 {config.status}" if config.status == "running" else f"🔴 {config.status}")
        table.add_row("PID", str(config.pid) if config.pid else "N/A")
        table.add_row("Created", config.created_at)
        table.add_row("Modules", ", ".join(config.modules) if config.modules else "None")
        table.add_row("GitHub Repos", ", ".join(config.github_repos) if config.github_repos else "None")
        
        console.print(table)
        
        # Show recent actions
        console.print("\n[bold cyan]📋 Recent Actions:[/bold cyan]")
        self.show_bot_history(bot_name)
        
        input("\nPress Enter to continue...")

    def show_bot_history(self, bot_name: str, limit: int = 10):
        """Show recent actions for a bot"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT action, timestamp, details, success FROM bot_history 
            WHERE bot_name = ? ORDER BY timestamp DESC LIMIT ?
        ''', (bot_name, limit))
        
        results = cursor.fetchall()
        conn.close()
        
        if not results:
            console.print("[dim]No history available[/dim]")
            return
        
        table = Table(show_header=True, header_style="bold")
        table.add_column("Action")
        table.add_column("Time")
        table.add_column("Details")
        table.add_column("Status")
        
        for action, timestamp, details, success in results:
            status_icon = "✅" if success else "❌"
            time_str = datetime.fromisoformat(timestamp).strftime("%m-%d %H:%M")
            table.add_row(action.title(), time_str, details[:50] + "..." if len(details) > 50 else details, status_icon)
        
        console.print(table)

    def run(self):
        """Main launcher loop"""
        try:
            while True:
                self.display_main_menu()
                self.display_menu_options()
                
                choice = Prompt.ask("Choose an option", choices=[str(i) for i in range(10)])
                
                if choice == "0":
                    console.print("[green]👋 Goodbye![/green]")
                    break
                elif choice == "1":
                    self.bot_management_menu()
                elif choice == "2":
                    self.command_creator_menu()
                elif choice == "3":
                    self.module_manager_menu()
                elif choice == "4":
                    self.github_integration_menu()
                elif choice == "5":
                    self.configuration_editor_menu()
                elif choice == "6":
                    self.performance_monitor_menu()
                elif choice == "7":
                    self.development_tools_menu()
                elif choice == "8":
                    self.workspace_manager_menu()
                elif choice == "9":
                    self.system_information_menu()
                    
        except KeyboardInterrupt:
            console.print("\n[yellow]Interrupted by user[/yellow]")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")

    # Integrated modules
    def command_creator_menu(self):
        """Launch command creator module"""
        try:
            from modules.command_creator import CommandCreator
            creator = CommandCreator(workspace_dir=str(self.workspace_dir))
            creator.command_creator_menu(self.bots)
        except ImportError as e:
            console.print(f"[red]Command Creator module not available: {e}[/red]")
            input("Press Enter to continue...")
        except Exception as e:
            console.print(f"[red]Error loading Command Creator: {e}[/red]")
            input("Press Enter to continue...")

    def module_manager_menu(self):
        console.print("[yellow]🚧 Module Manager coming soon![/yellow]")
        input("Press Enter to continue...")

    def github_integration_menu(self):
        """Launch GitHub integration module"""
        try:
            from modules.github_integration import GitHubIntegration
            github = GitHubIntegration(workspace_dir=str(self.workspace_dir))
            github.github_integration_menu()
        except ImportError as e:
            console.print(f"[red]GitHub Integration module not available: {e}[/red]")
            input("Press Enter to continue...")
        except Exception as e:
            console.print(f"[red]Error loading GitHub Integration: {e}[/red]")
            input("Press Enter to continue...")

    def configuration_editor_menu(self):
        console.print("[yellow]🚧 Configuration Editor coming soon![/yellow]")
        input("Press Enter to continue...")

    def performance_monitor_menu(self):
        console.print("[yellow]🚧 Performance Monitor coming soon![/yellow]")
        input("Press Enter to continue...")

    def development_tools_menu(self):
        console.print("[yellow]🚧 Development Tools coming soon![/yellow]")
        input("Press Enter to continue...")

    def workspace_manager_menu(self):
        console.print("[yellow]🚧 Workspace Manager coming soon![/yellow]")
        input("Press Enter to continue...")

    def system_information_menu(self):
        console.print("[yellow]🚧 System Information coming soon![/yellow]")
        input("Press Enter to continue...")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Advanced Discord Bot Launcher")
    parser.add_argument("--workspace", default="/home/nike/clean-discord-bot", 
                       help="Workspace directory")
    parser.add_argument("--config", help="Configuration file path")
    
    args = parser.parse_args()
    
    launcher = BotLauncher(workspace_dir=args.workspace)
    launcher.run()

if __name__ == "__main__":
    main()