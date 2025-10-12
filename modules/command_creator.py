#!/usr/bin/env python3
"""
⚡ Dynamic Command Creator Module
Create, edit, and manage custom Discord commands on-the-fly

Features:
- Visual command builder interface
- Code templates for common command types
- Syntax validation and testing
- Hot-reload commands without restart
- Command versioning and rollback
- Permissions and rate limiting setup
"""

import os
import sys
import ast
import inspect
import importlib
import traceback
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
import sqlite3
import json
from dataclasses import dataclass, asdict

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.text import Text
from rich.syntax import Syntax
from rich.columns import Columns

console = Console()

@dataclass
class CommandTemplate:
    name: str
    description: str
    category: str
    template_code: str
    parameters: List[str]
    examples: List[str]

@dataclass
class CustomCommand:
    name: str
    description: str
    code: str
    bot_name: str
    category: str
    permissions: List[str]
    rate_limit: int
    created_at: str
    modified_at: str
    version: int = 1
    active: bool = True

class CommandCreator:
    def __init__(self, workspace_dir: str = "/home/nike/clean-discord-bot"):
        self.workspace_dir = Path(workspace_dir)
        self.commands_dir = self.workspace_dir / "custom_commands"
        self.templates_dir = self.workspace_dir / "command_templates"
        self.db_file = self.workspace_dir / "launcher.db"
        
        # Create directories
        self.commands_dir.mkdir(exist_ok=True)
        self.templates_dir.mkdir(exist_ok=True)
        
        # Initialize templates
        self.init_command_templates()
        
        # Load existing commands
        self.commands: Dict[str, CustomCommand] = self.load_commands()

    def init_command_templates(self):
        """Initialize built-in command templates"""
        templates = {
            "basic_response": CommandTemplate(
                name="Basic Response",
                description="Simple command that sends a response",
                category="Basic",
                template_code='''@bot.command(name='{command_name}')
async def {command_name}(ctx):
    """Your command description here"""
    await ctx.send("Your response here!")''',
                parameters=["command_name"],
                examples=["!hello", "!info"]
            ),
            
            "embed_response": CommandTemplate(
                name="Embed Response", 
                description="Command that sends a rich embed",
                category="Basic",
                template_code='''@bot.command(name='{command_name}')
async def {command_name}(ctx):
    """Your command description here"""
    embed = discord.Embed(
        title="Your Title",
        description="Your description",
        color=0x00ff00,
        timestamp=datetime.now()
    )
    embed.add_field(name="Field 1", value="Value 1", inline=True)
    embed.add_field(name="Field 2", value="Value 2", inline=True)
    await ctx.send(embed=embed)''',
                parameters=["command_name"],
                examples=["!status", "!about"]
            ),
            
            "user_input": CommandTemplate(
                name="User Input Handler",
                description="Command that processes user arguments",
                category="Interactive",
                template_code='''@bot.command(name='{command_name}')
async def {command_name}(ctx, *, user_input: str = None):
    """Your command description here"""
    if not user_input:
        await ctx.send("Please provide some input!")
        return
    
    # Process user input here
    response = f"You said: {user_input}"
    await ctx.send(response)''',
                parameters=["command_name"],
                examples=["!echo hello world", "!process some text"]
            ),
            
            "database_query": CommandTemplate(
                name="Database Query",
                description="Command that interacts with database",
                category="Data",
                template_code='''@bot.command(name='{command_name}')
async def {command_name}(ctx, query: str = None):
    """Your command description here"""
    import sqlite3
    
    if not query:
        await ctx.send("Please provide a search query!")
        return
    
    try:
        # Example database interaction
        conn = sqlite3.connect('your_database.db')
        cursor = conn.cursor()
        
        # Your query logic here
        cursor.execute("SELECT * FROM your_table WHERE name LIKE ?", (f"%{query}%",))
        results = cursor.fetchall()
        
        if results:
            response = f"Found {len(results)} results for '{query}'"
        else:
            response = f"No results found for '{query}'"
        
        conn.close()
        await ctx.send(response)
        
    except Exception as e:
        await ctx.send(f"Database error: {str(e)}")''',
                parameters=["command_name"],
                examples=["!search python", "!lookup discord"]
            ),
            
            "api_request": CommandTemplate(
                name="API Request",
                description="Command that makes external API calls",
                category="Network",
                template_code='''@bot.command(name='{command_name}')
async def {command_name}(ctx, query: str = None):
    """Your command description here"""
    import aiohttp
    
    if not query:
        await ctx.send("Please provide a search query!")
        return
    
    try:
        async with aiohttp.ClientSession() as session:
            # Example API call - replace with your API
            url = f"https://api.example.com/search?q={query}"
            headers = {"User-Agent": "Discord Bot"}
            
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    # Process API response here
                    result = data.get('result', 'No data')
                    await ctx.send(f"API Result: {result}")
                else:
                    await ctx.send(f"API Error: {response.status}")
                    
    except Exception as e:
        await ctx.send(f"Request failed: {str(e)}")''',
                parameters=["command_name"],
                examples=["!weather london", "!news technology"]
            ),
            
            "math_calculator": CommandTemplate(
                name="Math Calculator",
                description="Command that performs calculations",
                category="Utility",
                template_code='''@bot.command(name='{command_name}')
async def {command_name}(ctx, *, expression: str = None):
    """Calculate mathematical expressions safely"""
    if not expression:
        await ctx.send("Please provide a mathematical expression!")
        return
    
    try:
        # Safe evaluation of mathematical expressions
        import ast
        import operator
        
        # Allowed operators
        operators = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.Pow: operator.pow,
            ast.USub: operator.neg,
        }
        
        def eval_expr(node):
            if isinstance(node, ast.Num):
                return node.n
            elif isinstance(node, ast.BinOp):
                return operators[type(node.op)](eval_expr(node.left), eval_expr(node.right))
            elif isinstance(node, ast.UnaryOp):
                return operators[type(node.op)](eval_expr(node.operand))
            else:
                raise TypeError(node)
        
        result = eval_expr(ast.parse(expression, mode='eval').body)
        await ctx.send(f"Result: `{expression}` = **{result}**")
        
    except Exception as e:
        await ctx.send(f"Calculation error: {str(e)}")''',
                parameters=["command_name"],
                examples=["!calc 2 + 2", "!math 10 * 5 + 3"]
            ),
            
            "file_operations": CommandTemplate(
                name="File Operations",
                description="Command that handles file operations",
                category="Utility",
                template_code='''@bot.command(name='{command_name}')
async def {command_name}(ctx, action: str = None, filename: str = None):
    """Handle file operations safely"""
    if not action or not filename:
        await ctx.send("Usage: `!{command_name} <action> <filename>`\\nActions: read, write, list, delete")
        return
    
    try:
        # Secure file operations within workspace
        workspace = Path("/home/nike/clean-discord-bot/user_files")
        workspace.mkdir(exist_ok=True)
        
        file_path = workspace / filename
        
        # Security check - ensure file is within workspace
        if not str(file_path.resolve()).startswith(str(workspace.resolve())):
            await ctx.send("❌ Access denied: File outside workspace")
            return
        
        if action.lower() == "read":
            if file_path.exists():
                content = file_path.read_text()[:1000]  # Limit content
                await ctx.send(f"```\\n{content}\\n```")
            else:
                await ctx.send("❌ File not found")
                
        elif action.lower() == "write":
            await ctx.send("Please upload a file to write, or use `!{command_name} create <filename>` first")
            
        elif action.lower() == "list":
            files = [f.name for f in workspace.glob("*") if f.is_file()]
            if files:
                await ctx.send(f"📁 Files: {', '.join(files)}")
            else:
                await ctx.send("📁 No files found")
                
        elif action.lower() == "delete":
            if file_path.exists():
                file_path.unlink()
                await ctx.send(f"🗑️ Deleted: {filename}")
            else:
                await ctx.send("❌ File not found")
        else:
            await ctx.send("❌ Invalid action")
            
    except Exception as e:
        await ctx.send(f"File operation error: {str(e)}")''',
                parameters=["command_name"],
                examples=["!files list", "!files read notes.txt"]
            )
        }
        
        # Save templates to files
        for template_name, template in templates.items():
            template_file = self.templates_dir / f"{template_name}.json"
            if not template_file.exists():
                with open(template_file, 'w') as f:
                    json.dump(asdict(template), f, indent=2)

    def load_commands(self) -> Dict[str, CustomCommand]:
        """Load custom commands from database"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT bot_name, command_name, command_code, created_at, modified_at, active
                FROM custom_commands WHERE active = 1
            ''')
            results = cursor.fetchall()
            conn.close()
            
            commands = {}
            for bot_name, cmd_name, code, created, modified, active in results:
                commands[f"{bot_name}_{cmd_name}"] = CustomCommand(
                    name=cmd_name,
                    description="Custom command",
                    code=code,
                    bot_name=bot_name,
                    category="Custom",
                    permissions=[],
                    rate_limit=5,
                    created_at=created,
                    modified_at=modified,
                    active=bool(active)
                )
            
            return commands
            
        except Exception as e:
            console.print(f"[red]Error loading commands: {e}[/red]")
            return {}

    def save_command(self, command: CustomCommand):
        """Save custom command to database"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            # Check if command exists
            cursor.execute('''
                SELECT id FROM custom_commands 
                WHERE bot_name = ? AND command_name = ?
            ''', (command.bot_name, command.name))
            
            if cursor.fetchone():
                # Update existing
                cursor.execute('''
                    UPDATE custom_commands 
                    SET command_code = ?, modified_at = CURRENT_TIMESTAMP, active = ?
                    WHERE bot_name = ? AND command_name = ?
                ''', (command.code, command.active, command.bot_name, command.name))
            else:
                # Insert new
                cursor.execute('''
                    INSERT INTO custom_commands (bot_name, command_name, command_code, active)
                    VALUES (?, ?, ?, ?)
                ''', (command.bot_name, command.name, command.code, command.active))
            
            conn.commit()
            conn.close()
            
            # Also save to file for backup
            cmd_file = self.commands_dir / f"{command.bot_name}_{command.name}.py"
            with open(cmd_file, 'w') as f:
                f.write(f"# Custom Command: {command.name}\n")
                f.write(f"# Bot: {command.bot_name}\n")
                f.write(f"# Created: {command.created_at}\n\n")
                f.write(command.code)
                
        except Exception as e:
            console.print(f"[red]Error saving command: {e}[/red]")

    def command_creator_menu(self, bot_configs: Dict):
        """Main command creator interface"""
        while True:
            console.clear()
            console.print(Panel.fit("[bold yellow]⚡ Dynamic Command Creator[/bold yellow]"))
            
            # Show existing commands
            self.display_command_list()
            
            console.print("[bold cyan]Command Creator Options:[/bold cyan]")
            console.print("1. 📝 Create New Command")
            console.print("2. ✏️  Edit Existing Command")
            console.print("3. 🗑️  Delete Command")
            console.print("4. 📋 View Command Templates")
            console.print("5. 🧪 Test Command")
            console.print("6. 🔄 Reload Commands (Hot Reload)")
            console.print("7. 📊 Command Statistics")
            console.print("0. ⬅️  Back to Main Menu")
            
            choice = Prompt.ask("Choose option", choices=["0", "1", "2", "3", "4", "5", "6", "7"])
            
            if choice == "0":
                break
            elif choice == "1":
                self.create_new_command(bot_configs)
            elif choice == "2":
                self.edit_command()
            elif choice == "3":
                self.delete_command()
            elif choice == "4":
                self.view_templates()
            elif choice == "5":
                self.test_command()
            elif choice == "6":
                self.reload_commands()
            elif choice == "7":
                self.show_command_stats()

    def display_command_list(self):
        """Display list of custom commands"""
        if not self.commands:
            console.print("[yellow]No custom commands created yet.[/yellow]")
            return
        
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Command")
        table.add_column("Bot")
        table.add_column("Category")
        table.add_column("Status")
        table.add_column("Created")
        
        for cmd_key, command in self.commands.items():
            status = "🟢 Active" if command.active else "🔴 Inactive"
            created = datetime.fromisoformat(command.created_at).strftime("%m-%d")
            table.add_row(
                command.name, command.bot_name, command.category, status, created
            )
        
        console.print(table)
        console.print()

    def create_new_command(self, bot_configs: Dict):
        """Create a new custom command"""
        console.print("[bold cyan]📝 Creating New Command[/bold cyan]")
        
        # Select target bot
        if not bot_configs:
            console.print("[red]No bots configured! Please create a bot first.[/red]")
            input("Press Enter to continue...")
            return
        
        bot_name = Prompt.ask("Select target bot", choices=list(bot_configs.keys()))
        command_name = Prompt.ask("Command name (without prefix)")
        
        # Check if command exists
        cmd_key = f"{bot_name}_{command_name}"
        if cmd_key in self.commands:
            console.print(f"[red]Command {command_name} already exists for {bot_name}![/red]")
            return
        
        # Select template
        templates = self.get_available_templates()
        console.print("\n[bold]Available Templates:[/bold]")
        for i, (template_name, template) in enumerate(templates.items(), 1):
            console.print(f"{i}. {template.name} - {template.description}")
        
        template_choice = int(Prompt.ask("Choose template", choices=[str(i) for i in range(1, len(templates)+1)]))
        template_name = list(templates.keys())[template_choice - 1]
        template = templates[template_name]
        
        # Generate command code
        command_code = template.template_code.format(command_name=command_name)
        
        # Show code for review/editing
        console.print(f"\n[bold]Generated Code Preview:[/bold]")
        syntax = Syntax(command_code, "python", theme="monokai", line_numbers=True)
        console.print(syntax)
        
        if Confirm.ask("Would you like to edit this code?"):
            command_code = self.code_editor(command_code)
        
        # Validate syntax
        if not self.validate_command_syntax(command_code):
            console.print("[red]❌ Invalid Python syntax! Please fix and try again.[/red]")
            input("Press Enter to continue...")
            return
        
        # Create command
        command = CustomCommand(
            name=command_name,
            description=template.description,
            code=command_code,
            bot_name=bot_name,
            category=template.category,
            permissions=[],
            rate_limit=5,
            created_at=datetime.now().isoformat(),
            modified_at=datetime.now().isoformat()
        )
        
        self.commands[cmd_key] = command
        self.save_command(command)
        
        console.print(f"[green]✅ Command {command_name} created successfully![/green]")
        
        # Ask if they want to deploy immediately
        if Confirm.ask("Deploy command to bot now?"):
            self.deploy_command_to_bot(command, bot_configs[bot_name])
        
        input("Press Enter to continue...")

    def get_available_templates(self) -> Dict[str, CommandTemplate]:
        """Get available command templates"""
        templates = {}
        
        for template_file in self.templates_dir.glob("*.json"):
            try:
                with open(template_file, 'r') as f:
                    data = json.load(f)
                    templates[template_file.stem] = CommandTemplate(**data)
            except Exception as e:
                console.print(f"[red]Error loading template {template_file}: {e}[/red]")
        
        return templates

    def code_editor(self, initial_code: str) -> str:
        """Simple code editor interface"""
        console.print("[bold]Code Editor - Enter your code (type 'END' on a new line to finish):[/bold]")
        console.print("[dim]Current code:[/dim]")
        
        syntax = Syntax(initial_code, "python", theme="monokai", line_numbers=True)
        console.print(syntax)
        console.print()
        
        console.print("[yellow]Enter new code (or press Enter to keep current):[/yellow]")
        lines = []
        while True:
            try:
                line = input(">>> ")
                if line.strip() == "END":
                    break
                lines.append(line)
            except KeyboardInterrupt:
                break
        
        if lines:
            return "\n".join(lines)
        return initial_code

    def validate_command_syntax(self, code: str) -> bool:
        """Validate Python syntax"""
        try:
            ast.parse(code)
            return True
        except SyntaxError as e:
            console.print(f"[red]Syntax Error: {e}[/red]")
            return False

    def deploy_command_to_bot(self, command: CustomCommand, bot_config):
        """Deploy command to running bot (hot reload)"""
        try:
            # This would require implementing hot-reload functionality in the target bot
            # For now, just show instructions
            console.print(f"[yellow]📋 To deploy command '{command.name}' to {command.bot_name}:[/yellow]")
            console.print(f"1. Restart the {command.bot_name} bot")
            console.print(f"2. Or implement hot-reload in your bot code")
            console.print(f"3. Command file saved to: custom_commands/{command.bot_name}_{command.name}.py")
            
        except Exception as e:
            console.print(f"[red]Deployment error: {e}[/red]")

    def view_templates(self):
        """View available command templates"""
        console.clear()
        console.print(Panel.fit("[bold cyan]📋 Command Templates Library[/bold cyan]"))
        
        templates = self.get_available_templates()
        
        for template_name, template in templates.items():
            console.print(f"\n[bold blue]{template.name}[/bold blue]")
            console.print(f"Category: {template.category}")
            console.print(f"Description: {template.description}")
            console.print(f"Parameters: {', '.join(template.parameters)}")
            
            if template.examples:
                console.print(f"Examples: {', '.join(template.examples)}")
            
            # Show code preview
            console.print("[dim]Code Preview:[/dim]")
            syntax = Syntax(template.template_code[:200] + "...", "python", theme="monokai")
            console.print(syntax)
            console.print("-" * 50)
        
        input("\nPress Enter to continue...")

    # Placeholder methods for remaining functionality
    def edit_command(self):
        console.print("[yellow]🚧 Edit Command coming soon![/yellow]")
        input("Press Enter to continue...")

    def delete_command(self):
        console.print("[yellow]🚧 Delete Command coming soon![/yellow]")
        input("Press Enter to continue...")

    def test_command(self):
        console.print("[yellow]🚧 Test Command coming soon![/yellow]")
        input("Press Enter to continue...")

    def reload_commands(self):
        console.print("[yellow]🚧 Hot Reload coming soon![/yellow]")
        input("Press Enter to continue...")

    def show_command_stats(self):
        console.print("[yellow]🚧 Command Statistics coming soon![/yellow]")
        input("Press Enter to continue...")