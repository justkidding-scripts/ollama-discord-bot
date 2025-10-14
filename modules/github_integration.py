#!/usr/bin/env python3
"""
🐙 GitHub Integration Module
Manage GitHub repositories, clone extensions, and sync with remote repositories

Features:
- Clone Discord bot extensions from GitHub
- Sync with remote repositories
- Browse and discover Discord bot modules
- Automatic dependency management
- Version control integration
- Extension marketplace
"""

import os
import sys
import json
import subprocess
import asyncio
import aiohttp
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import sqlite3
import shutil
from dataclasses import dataclass, asdict
import urllib.parse
import base64

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, DownloadColumn
from rich.tree import Tree
from rich.text import Text
from rich.columns import Columns
from rich.json import JSON

try:
    import git
    from git import Repo, InvalidGitRepositoryError, GitCommandError
    GIT_AVAILABLE = True
except ImportError:
    GIT_AVAILABLE = False

console = Console()

@dataclass
class GitHubRepo:
    owner: str
    name: str
    description: str
    url: str
    clone_url: str
    stars: int
    language: str
    updated_at: str
    topics: List[str]
    license: Optional[str] = None
    size: int = 0
    
@dataclass
class BotExtension:
    name: str
    description: str
    category: str
    repo_url: str
    local_path: str
    version: str
    author: str
    dependencies: List[str]
    commands: List[str]
    installed_at: str
    last_updated: str
    active: bool = True

class GitHubIntegration:
    def __init__(self, workspace_dir: str = "/home/nike/clean-discord-bot"):
        self.workspace_dir = Path(workspace_dir)
        self.extensions_dir = self.workspace_dir / "extensions"
        self.repos_dir = self.workspace_dir / "github_repos"
        self.db_file = self.workspace_dir / "launcher.db"
        
        # GitHub API configuration
        self.github_api_base = "https://api.github.com"
        self.github_token = os.getenv("GITHUB_TOKEN")  # Optional for higher rate limits
        
        # Create directories
        self.extensions_dir.mkdir(exist_ok=True)
        self.repos_dir.mkdir(exist_ok=True)
        
        # Initialize extension registry
        self.extensions: Dict[str, BotExtension] = self.load_extensions()
        
        # Popular Discord bot repositories (curated list)
        self.featured_repos = [
            "Rapptz/discord.py",
            "Gelbpunkt/discord.py",
            "nextcord/nextcord",
            "hikari-py/hikari",
            "magicguitars/easybot",
            "AlexFlipnote/discord_bot.py",
            "python-discord/bot",
            "fourjr/ticket-tool",
            "Defxult/reactionmenu",
            "AbstractUmbra/GuildConfigBot"
        ]

    def load_extensions(self) -> Dict[str, BotExtension]:
        """Load installed extensions from database"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT module_name, module_type, source_repo, install_date, version, dependencies
                FROM module_registry WHERE module_type = 'extension'
            ''')
            results = cursor.fetchall()
            conn.close()
            
            extensions = {}
            for name, mod_type, source, install_date, version, deps in results:
                extensions[name] = BotExtension(
                    name=name,
                    description="Discord bot extension",
                    category="Extension",
                    repo_url=source,
                    local_path=str(self.extensions_dir / name),
                    version=version or "unknown",
                    author="",
                    dependencies=json.loads(deps) if deps else [],
                    commands=[],
                    installed_at=install_date,
                    last_updated=install_date
                )
            
            return extensions
            
        except Exception as e:
            console.print(f"[red]Error loading extensions: {e}[/red]")
            return {}

    def save_extension(self, extension: BotExtension):
        """Save extension info to database"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO module_registry 
                (module_name, module_type, source_repo, version, dependencies)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                extension.name, 
                'extension',
                extension.repo_url,
                extension.version,
                json.dumps(extension.dependencies)
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            console.print(f"[red]Error saving extension: {e}[/red]")

    async def github_api_request(self, endpoint: str) -> Optional[Dict]:
        """Make GitHub API request with rate limiting"""
        url = f"{self.github_api_base}/{endpoint.lstrip('/')}"
        headers = {"Accept": "application/vnd.github.v3+json"}
        
        if self.github_token:
            headers["Authorization"] = f"token {self.github_token}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 403:
                        console.print("[red]GitHub API rate limit exceeded. Set GITHUB_TOKEN for higher limits.[/red]")
                        return None
                    else:
                        console.print(f"[red]GitHub API error: {response.status}[/red]")
                        return None
                        
        except Exception as e:
            console.print(f"[red]GitHub API request failed: {e}[/red]")
            return None

    def github_integration_menu(self):
        """Main GitHub integration interface"""
        while True:
            console.clear()
            console.print(Panel.fit("[bold green]🐙 GitHub Integration Center[/bold green]"))
            
            # Show installed extensions
            self.display_extensions_overview()
            
            console.print("[bold cyan]GitHub Integration Options:[/bold cyan]")
            console.print("1. 🔍 Discover Bot Extensions")
            console.print("2. 📥 Clone Repository")
            console.print("3. 🛠️ Install Extension")
            console.print("4. 🔄 Update Extensions")
            console.print("5. 🗂️ Manage Local Repositories")
            console.print("6. 📊 Extension Marketplace")
            console.print("7. ⚙️ Repository Settings")
            console.print("8. 📋 Import/Export Config")
            console.print("0. ⬅️ Back to Main Menu")
            
            choice = Prompt.ask("Choose option", choices=[str(i) for i in range(9)])
            
            if choice == "0":
                break
            elif choice == "1":
                asyncio.run(self.discover_extensions())
            elif choice == "2":
                asyncio.run(self.clone_repository())
            elif choice == "3":
                asyncio.run(self.install_extension())
            elif choice == "4":
                self.update_extensions()
            elif choice == "5":
                self.manage_repositories()
            elif choice == "6":
                asyncio.run(self.extension_marketplace())
            elif choice == "7":
                self.repository_settings()
            elif choice == "8":
                self.import_export_config()

    def display_extensions_overview(self):
        """Display overview of installed extensions"""
        if not self.extensions:
            console.print("[yellow]No extensions installed yet.[/yellow]")
            return
        
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Extension")
        table.add_column("Version")
        table.add_column("Source")
        table.add_column("Status")
        table.add_column("Updated")
        
        for name, ext in self.extensions.items():
            status = "🟢 Active" if ext.active else "🔴 Inactive"
            updated = datetime.fromisoformat(ext.last_updated).strftime("%m-%d") if ext.last_updated else "N/A"
            source_short = ext.repo_url.split("/")[-1] if "/" in ext.repo_url else ext.repo_url
            
            table.add_row(name, ext.version, source_short, status, updated)
        
        console.print(table)
        console.print()

    async def discover_extensions(self):
        """Discover popular Discord bot extensions"""
        console.clear()
        console.print(Panel.fit("[bold cyan]🔍 Discovering Discord Bot Extensions[/bold cyan]"))
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            task = progress.add_task("Searching GitHub for Discord bot extensions...", total=None)
            
            # Search for Discord bot repositories
            search_queries = [
                "discord bot python",
                "discord.py bot",
                "discord bot commands",
                "discord bot modules"
            ]
            
            all_repos = []
            for query in search_queries:
                progress.update(task, description=f"Searching: {query}")
                repos = await self.search_github_repos(query, per_page=10)
                if repos:
                    all_repos.extend(repos)
                time.sleep(1)  # Rate limiting
        
        if not all_repos:
            console.print("[red]No repositories found or API error.[/red]")
            input("Press Enter to continue...")
            return
        
        # Remove duplicates and sort by stars
        unique_repos = {repo.name: repo for repo in all_repos}
        sorted_repos = sorted(unique_repos.values(), key=lambda x: x.stars, reverse=True)
        
        # Display results
        console.print(f"\n[bold green]Found {len(sorted_repos)} Discord Bot Repositories:[/bold green]\n")
        
        table = Table(show_header=True, header_style="bold")
        table.add_column("Name", style="cyan")
        table.add_column("Description")
        table.add_column("⭐ Stars", justify="right")
        table.add_column("Language")
        table.add_column("Updated")
        
        for repo in sorted_repos[:20]:  # Show top 20
            updated = datetime.fromisoformat(repo.updated_at.replace('Z', '+00:00')).strftime("%m-%d")
            description = (repo.description[:50] + "...") if len(repo.description) > 50 else repo.description
            table.add_row(
                f"{repo.owner}/{repo.name}",
                description,
                str(repo.stars),
                repo.language or "N/A",
                updated
            )
        
        console.print(table)
        
        # Allow user to select and clone
        if Confirm.ask("\nWould you like to clone one of these repositories?"):
            repo_choice = Prompt.ask("Enter repository name (owner/name)")
            selected_repo = None
            for repo in sorted_repos:
                if f"{repo.owner}/{repo.name}" == repo_choice:
                    selected_repo = repo
                    break
            
            if selected_repo:
                await self.clone_specific_repo(selected_repo)
            else:
                console.print("[red]Repository not found in the list.[/red]")
        
        input("\nPress Enter to continue...")

    async def search_github_repos(self, query: str, per_page: int = 30) -> List[GitHubRepo]:
        """Search GitHub repositories"""
        endpoint = f"search/repositories?q={urllib.parse.quote(query)}&sort=stars&order=desc&per_page={per_page}"
        data = await self.github_api_request(endpoint)
        
        if not data or 'items' not in data:
            return []
        
        repos = []
        for item in data['items']:
            repo = GitHubRepo(
                owner=item['owner']['login'],
                name=item['name'],
                description=item['description'] or "No description",
                url=item['html_url'],
                clone_url=item['clone_url'],
                stars=item['stargazers_count'],
                language=item['language'],
                updated_at=item['updated_at'],
                topics=item.get('topics', []),
                license=item['license']['name'] if item['license'] else None,
                size=item['size']
            )
            repos.append(repo)
        
        return repos

    async def clone_repository(self):
        """Clone a repository by URL"""
        console.print("[bold cyan]📥 Clone GitHub Repository[/bold cyan]")
        
        repo_url = Prompt.ask("Enter repository URL or owner/name")
        
        # Handle different URL formats
        if not repo_url.startswith("http"):
            if "/" in repo_url:
                repo_url = f"https://github.com/{repo_url}.git"
            else:
                console.print("[red]Invalid repository format. Use 'owner/name' or full URL.[/red]")
                input("Press Enter to continue...")
                return
        
        # Extract repository name for local directory
        repo_name = repo_url.split("/")[-1].replace(".git", "")
        local_path = self.repos_dir / repo_name
        
        if local_path.exists():
            console.print(f"[yellow]Repository {repo_name} already exists locally.[/yellow]")
            if not Confirm.ask("Overwrite existing repository?"):
                return
            shutil.rmtree(local_path)
        
        # Clone repository
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            DownloadColumn(),
            transient=True,
        ) as progress:
            task = progress.add_task(f"Cloning {repo_name}...", total=None)
            
            try:
                if GIT_AVAILABLE:
                    Repo.clone_from(repo_url, local_path)
                else:
                    # Fallback to git command
                    result = subprocess.run([
                        "git", "clone", repo_url, str(local_path)
                    ], capture_output=True, text=True)
                    
                    if result.returncode != 0:
                        raise Exception(result.stderr)
                
                console.print(f"[green]✅ Repository {repo_name} cloned successfully![/green]")
                
                # Analyze repository for Discord bot features
                await self.analyze_repository(local_path, repo_url)
                
            except Exception as e:
                console.print(f"[red]❌ Failed to clone repository: {e}[/red]")
        
        input("Press Enter to continue...")

    async def clone_specific_repo(self, repo: GitHubRepo):
        """Clone a specific repository from search results"""
        local_path = self.repos_dir / repo.name
        
        if local_path.exists():
            if not Confirm.ask(f"Repository {repo.name} exists. Overwrite?"):
                return
            shutil.rmtree(local_path)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            task = progress.add_task(f"Cloning {repo.name}...", total=None)
            
            try:
                if GIT_AVAILABLE:
                    Repo.clone_from(repo.clone_url, local_path)
                else:
                    result = subprocess.run([
                        "git", "clone", repo.clone_url, str(local_path)
                    ], capture_output=True, text=True)
                    
                    if result.returncode != 0:
                        raise Exception(result.stderr)
                
                console.print(f"[green]✅ Repository {repo.name} cloned successfully![/green]")
                
                # Analyze for bot features
                await self.analyze_repository(local_path, repo.url)
                
            except Exception as e:
                console.print(f"[red]❌ Failed to clone repository: {e}[/red]")

    async def analyze_repository(self, repo_path: Path, repo_url: str):
        """Analyze repository for Discord bot features"""
        console.print(f"\n[bold]🔍 Analyzing repository structure...[/bold]")
        
        analysis = {
            'is_discord_bot': False,
            'main_files': [],
            'requirements': [],
            'commands': [],
            'cogs': [],
            'config_files': []
        }
        
        # Check for common Discord bot patterns
        discord_indicators = [
            'discord.py', 'discord', 'nextcord', 'hikari',
            'bot.py', 'main.py', 'client.py'
        ]
        
        python_files = list(repo_path.glob("**/*.py"))
        
        for file_path in python_files:
            try:
                content = file_path.read_text(encoding='utf-8')
                
                # Check for Discord bot indicators
                if any(indicator in content.lower() for indicator in discord_indicators):
                    analysis['is_discord_bot'] = True
                
                # Look for main bot files
                if any(pattern in file_path.name.lower() for pattern in ['bot.py', 'main.py', 'client.py']):
                    analysis['main_files'].append(str(file_path.relative_to(repo_path)))
                
                # Look for command definitions
                if '@bot.command' in content or '@client.command' in content:
                    analysis['commands'].extend([
                        line.strip() for line in content.split('\n')
                        if '@bot.command' in line or '@client.command' in line
                    ])
                
                # Look for cogs
                if 'commands.Cog' in content or 'class' in content and 'Cog' in content:
                    analysis['cogs'].append(str(file_path.relative_to(repo_path)))
                    
            except Exception:
                continue
        
        # Check for requirements.txt
        req_file = repo_path / "requirements.txt"
        if req_file.exists():
            try:
                requirements = req_file.read_text().strip().split('\n')
                analysis['requirements'] = [req.strip() for req in requirements if req.strip()]
            except Exception:
                pass
        
        # Check for config files
        for config_pattern in ['config.*', '*.env*', '*.json', '*.yaml', '*.yml']:
            analysis['config_files'].extend([
                str(f.relative_to(repo_path)) for f in repo_path.glob(config_pattern)
                if f.is_file()
            ])
        
        # Display analysis results
        self.display_repository_analysis(analysis, repo_path.name)
        
        # Offer to install as extension
        if analysis['is_discord_bot']:
            if Confirm.ask("This appears to be a Discord bot. Install as extension?"):
                await self.install_as_extension(repo_path, repo_url, analysis)

    def display_repository_analysis(self, analysis: Dict, repo_name: str):
        """Display repository analysis results"""
        console.print(f"\n[bold]📊 Analysis Results for {repo_name}:[/bold]")
        
        # Create analysis tree
        tree = Tree("📁 Repository Analysis")
        
        if analysis['is_discord_bot']:
            tree.add("✅ Discord Bot Detected")
        else:
            tree.add("❌ Not a Discord Bot")
        
        if analysis['main_files']:
            main_branch = tree.add("🎯 Main Files")
            for file in analysis['main_files'][:5]:  # Show first 5
                main_branch.add(file)
        
        if analysis['commands']:
            cmd_branch = tree.add(f"⚡ Commands ({len(analysis['commands'])})")
            for cmd in analysis['commands'][:3]:  # Show first 3
                cmd_branch.add(cmd.strip())
        
        if analysis['cogs']:
            cog_branch = tree.add(f"🧩 Cogs/Extensions ({len(analysis['cogs'])})")
            for cog in analysis['cogs'][:3]:
                cog_branch.add(cog)
        
        if analysis['requirements']:
            req_branch = tree.add(f"📦 Dependencies ({len(analysis['requirements'])})")
            for req in analysis['requirements'][:5]:
                req_branch.add(req)
        
        if analysis['config_files']:
            cfg_branch = tree.add(f"⚙️ Config Files ({len(analysis['config_files'])})")
            for cfg in analysis['config_files'][:3]:
                cfg_branch.add(cfg)
        
        console.print(tree)

    async def install_as_extension(self, repo_path: Path, repo_url: str, analysis: Dict):
        """Install repository as bot extension"""
        extension_name = Prompt.ask("Extension name", default=repo_path.name)
        
        # Create extension entry
        extension = BotExtension(
            name=extension_name,
            description=f"Extension from {repo_url}",
            category="GitHub",
            repo_url=repo_url,
            local_path=str(repo_path),
            version="1.0.0",
            author="",
            dependencies=analysis['requirements'],
            commands=[cmd.strip() for cmd in analysis['commands']],
            installed_at=datetime.now().isoformat(),
            last_updated=datetime.now().isoformat()
        )
        
        # Install dependencies
        if extension.dependencies:
            console.print(f"[yellow]Installing dependencies: {', '.join(extension.dependencies)}[/yellow]")
            try:
                subprocess.run([
                    sys.executable, "-m", "pip", "install"
                ] + extension.dependencies, check=True)
                console.print("[green]✅ Dependencies installed successfully![/green]")
            except subprocess.CalledProcessError as e:
                console.print(f"[red]❌ Failed to install dependencies: {e}[/red]")
        
        # Save extension
        self.extensions[extension_name] = extension
        self.save_extension(extension)
        
        console.print(f"[green]✅ Extension {extension_name} installed successfully![/green]")

    async def extension_marketplace(self):
        """Browse extension marketplace"""
        console.clear()
        console.print(Panel.fit("[bold magenta]📊 Discord Bot Extension Marketplace[/bold magenta]"))
        
        console.print("[bold]🔥 Featured Repositories:[/bold]\n")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            task = progress.add_task("Loading featured repositories...", total=len(self.featured_repos))
            
            featured_info = []
            for repo in self.featured_repos:
                progress.update(task, description=f"Fetching {repo}")
                info = await self.get_repo_info(repo)
                if info:
                    featured_info.append(info)
                progress.advance(task)
                time.sleep(0.5)  # Rate limiting
        
        # Display featured repositories
        table = Table(show_header=True, header_style="bold")
        table.add_column("Repository", style="cyan")
        table.add_column("Description")
        table.add_column("⭐", justify="right")
        table.add_column("Language")
        
        for repo in featured_info:
            description = (repo.description[:60] + "...") if len(repo.description) > 60 else repo.description
            table.add_row(
                f"{repo.owner}/{repo.name}",
                description,
                str(repo.stars),
                repo.language or "N/A"
            )
        
        console.print(table)
        
        if Confirm.ask("\nBrowse a repository?"):
            repo_choice = Prompt.ask("Enter repository name (owner/name)")
            selected = None
            for repo in featured_info:
                if f"{repo.owner}/{repo.name}" == repo_choice:
                    selected = repo
                    break
            
            if selected:
                await self.browse_repository_details(selected)
        
        input("\nPress Enter to continue...")

    async def get_repo_info(self, repo_path: str) -> Optional[GitHubRepo]:
        """Get repository information from GitHub API"""
        endpoint = f"repos/{repo_path}"
        data = await self.github_api_request(endpoint)
        
        if not data:
            return None
        
        return GitHubRepo(
            owner=data['owner']['login'],
            name=data['name'],
            description=data['description'] or "No description",
            url=data['html_url'],
            clone_url=data['clone_url'],
            stars=data['stargazers_count'],
            language=data['language'],
            updated_at=data['updated_at'],
            topics=data.get('topics', []),
            license=data['license']['name'] if data['license'] else None,
            size=data['size']
        )

    async def browse_repository_details(self, repo: GitHubRepo):
        """Show detailed repository information"""
        console.clear()
        console.print(Panel.fit(f"[bold cyan]📁 Repository: {repo.owner}/{repo.name}[/bold cyan]"))
        
        # Repository info table
        table = Table(show_header=False, box=None)
        table.add_column("Property", style="bold")
        table.add_column("Value")
        
        table.add_row("Description", repo.description)
        table.add_row("URL", repo.url)
        table.add_row("Stars", str(repo.stars))
        table.add_row("Language", repo.language or "N/A")
        table.add_row("License", repo.license or "N/A")
        table.add_row("Size", f"{repo.size} KB")
        table.add_row("Updated", repo.updated_at)
        
        if repo.topics:
            table.add_row("Topics", ", ".join(repo.topics))
        
        console.print(table)
        
        # Action options
        console.print(f"\n[bold cyan]Actions for {repo.name}:[/bold cyan]")
        console.print("1. 📥 Clone Repository")
        console.print("2. 🌐 Open in Browser")
        console.print("3. 📄 View README")
        console.print("0. ⬅️ Back")
        
        choice = Prompt.ask("Choose action", choices=["0", "1", "2", "3"])
        
        if choice == "1":
            await self.clone_specific_repo(repo)
        elif choice == "2":
            os.system(f"xdg-open {repo.url}")
        elif choice == "3":
            await self.view_repository_readme(repo)

    async def view_repository_readme(self, repo: GitHubRepo):
        """View repository README"""
        endpoint = f"repos/{repo.owner}/{repo.name}/readme"
        data = await self.github_api_request(endpoint)
        
        if not data:
            console.print("[red]README not found.[/red]")
            return
        
        try:
            # Decode base64 content
            readme_content = base64.b64decode(data['content']).decode('utf-8')
            
            console.clear()
            console.print(Panel.fit(f"[bold]📄 README: {repo.name}[/bold]"))
            
            # Show first 50 lines
            lines = readme_content.split('\n')[:50]
            console.print('\n'.join(lines))
            
            if len(readme_content.split('\n')) > 50:
                console.print("\n[dim]... (README truncated)[/dim]")
                
        except Exception as e:
            console.print(f"[red]Error decoding README: {e}[/red]")
        
        input("\nPress Enter to continue...")

    # Placeholder methods for remaining functionality
    async def install_extension(self):
        console.print("[yellow]🚧 Install Extension coming soon![/yellow]")
        input("Press Enter to continue...")

    def update_extensions(self):
        console.print("[yellow]🚧 Update Extensions coming soon![/yellow]")
        input("Press Enter to continue...")

    def manage_repositories(self):
        console.print("[yellow]🚧 Manage Repositories coming soon![/yellow]")
        input("Press Enter to continue...")

    def repository_settings(self):
        console.print("[yellow]🚧 Repository Settings coming soon![/yellow]")
        input("Press Enter to continue...")

    def import_export_config(self):
        console.print("[yellow]🚧 Import/Export Config coming soon![/yellow]")
        input("Press Enter to continue...")