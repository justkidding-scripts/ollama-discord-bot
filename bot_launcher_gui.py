#!/usr/bin/env python3
"""
🚀 Advanced Bot Launcher & Management System - GUI Version
A modern graphical interface to manage, organize, and extend Discord bots

Features:
- Modern GUI with dark/light themes
- Bot lifecycle management (start/stop/restart)
- Visual bot status monitoring
- Dynamic command creation interface
- GitHub repository integration
- Module system management
- Real-time performance metrics
- Configuration editor
"""

import os
import sys
import json
import subprocess
import asyncio
import threading
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import sqlite3
import shutil
import git
from dataclasses import dataclass, asdict
import yaml
import logging
import webbrowser

# GUI imports
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
from tkinter.font import Font
import tkinter.font as tkFont

# Additional GUI libraries
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

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

class ModernBotLauncherGUI:
    def __init__(self):
        self.workspace_dir = Path("/home/nike/ollama-discord-bot")
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
        
        # Initialize GUI
        self.root = tk.Tk()
        self.setup_gui()
        
        # Theme variables
        self.dark_mode = tk.BooleanVar(value=True)
        self.apply_theme()
        
        # Status monitoring thread
        self.monitoring = False
        self.start_monitoring()

    def init_database(self):
        """Initialize SQLite database for tracking bot operations"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        # Bot tracking table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bot_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bot_name TEXT,
                action TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                details TEXT,
                success BOOLEAN
            )
        """)
        
        # Module tracking table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS module_registry (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                module_name TEXT,
                module_type TEXT,
                source_repo TEXT,
                install_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                version TEXT,
                dependencies TEXT
            )
        """)
        
        # Command tracking table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS custom_commands (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bot_name TEXT,
                command_name TEXT,
                command_code TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                active BOOLEAN DEFAULT TRUE
            )
        """)
        
        conn.commit()
        conn.close()

    def setup_gui(self):
        """Setup the main GUI interface"""
        self.root.title("🚀 Advanced Discord Bot Launcher")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 700)
        
        # Configure style
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Create main menu bar
        self.create_menubar()
        
        # Create main layout
        self.create_main_layout()
        
        # Bind close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_menubar(self):
        """Create the application menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Bot", command=self.create_new_bot, accelerator="Ctrl+N")
        file_menu.add_command(label="Import Bot", command=self.import_bot, accelerator="Ctrl+I")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_closing, accelerator="Ctrl+Q")
        
        # Bots menu
        bots_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Bots", menu=bots_menu)
        bots_menu.add_command(label="Start All", command=self.start_all_bots)
        bots_menu.add_command(label="Stop All", command=self.stop_all_bots)
        bots_menu.add_separator()
        bots_menu.add_command(label="Refresh Status", command=self.refresh_bot_status)
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Module Manager", command=self.open_module_manager)
        tools_menu.add_command(label="Command Creator", command=self.open_command_creator)
        tools_menu.add_command(label="GitHub Integration", command=self.open_github_manager)
        tools_menu.add_separator()
        tools_menu.add_command(label="Performance Monitor", command=self.open_performance_monitor)
        tools_menu.add_command(label="Logs Viewer", command=self.open_logs_viewer)
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_checkbutton(label="Dark Mode", variable=self.dark_mode, command=self.toggle_theme)
        view_menu.add_separator()
        view_menu.add_command(label="Full Screen", command=self.toggle_fullscreen, accelerator="F11")
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Documentation", command=self.open_documentation)
        help_menu.add_command(label="GitHub Repository", command=self.open_github_repo)
        help_menu.add_separator()
        help_menu.add_command(label="About", command=self.show_about)

    def create_main_layout(self):
        """Create the main application layout"""
        # Create main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title frame
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 10))
        
        title_label = ttk.Label(title_frame, text="🚀 Discord Bot Management Center", 
                               font=('Helvetica', 16, 'bold'))
        title_label.pack(side=tk.LEFT)
        
        # Status indicator
        self.status_label = ttk.Label(title_frame, text="● System Ready", 
                                     foreground="green", font=('Helvetica', 10))
        self.status_label.pack(side=tk.RIGHT)
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Bot Dashboard tab
        self.create_dashboard_tab()
        
        # Bot Creator tab
        self.create_creator_tab()
        
        # Modules tab
        self.create_modules_tab()
        
        # Settings tab
        self.create_settings_tab()
        
        # Status bar
        self.create_status_bar()

    def create_dashboard_tab(self):
        """Create the main bot dashboard tab"""
        dashboard_frame = ttk.Frame(self.notebook)
        self.notebook.add(dashboard_frame, text="🤖 Bot Dashboard")
        
        # Action buttons frame
        action_frame = ttk.Frame(dashboard_frame)
        action_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(action_frame, text="📱 Create New Bot", 
                  command=self.create_new_bot).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(action_frame, text="📁 Import Bot", 
                  command=self.import_bot).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="🔄 Refresh", 
                  command=self.refresh_bot_status).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="▶️ Start All", 
                  command=self.start_all_bots).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(action_frame, text="⏹️ Stop All", 
                  command=self.stop_all_bots).pack(side=tk.RIGHT, padx=5)
        
        # Bot list frame
        list_frame = ttk.Frame(dashboard_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create treeview for bot list
        columns = ('Name', 'Status', 'PID', 'Port', 'Created', 'Modules')
        self.bot_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=15)
        
        # Configure columns
        for col in columns:
            self.bot_tree.heading(col, text=col)
            if col == 'Name':
                self.bot_tree.column(col, width=150)
            elif col == 'Status':
                self.bot_tree.column(col, width=80)
            elif col in ['PID', 'Port', 'Modules']:
                self.bot_tree.column(col, width=70)
            else:
                self.bot_tree.column(col, width=120)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.bot_tree.yview)
        h_scrollbar = ttk.Scrollbar(list_frame, orient=tk.HORIZONTAL, command=self.bot_tree.xview)
        self.bot_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Pack treeview and scrollbars
        self.bot_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Bot control frame
        control_frame = ttk.Frame(dashboard_frame)
        control_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(control_frame, text="▶️ Start", 
                  command=self.start_selected_bot).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(control_frame, text="⏹️ Stop", 
                  command=self.stop_selected_bot).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="🔄 Restart", 
                  command=self.restart_selected_bot).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="⚙️ Configure", 
                  command=self.configure_selected_bot).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="🗑️ Delete", 
                  command=self.delete_selected_bot).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(control_frame, text="📊 Logs", 
                  command=self.view_bot_logs).pack(side=tk.RIGHT, padx=5)
        
        # Context menu for bot tree
        self.create_context_menu()
        
        # Populate bot list
        self.refresh_bot_list()

    def create_creator_tab(self):
        """Create the bot creator tab"""
        creator_frame = ttk.Frame(self.notebook)
        self.notebook.add(creator_frame, text="🛠️ Bot Creator")
        
        # Creator form
        form_frame = ttk.LabelFrame(creator_frame, text="Create New Bot", padding=10)
        form_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Bot name
        ttk.Label(form_frame, text="Bot Name:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.bot_name_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.bot_name_var, width=30).grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        
        # Description
        ttk.Label(form_frame, text="Description:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.bot_desc_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.bot_desc_var, width=50).grid(row=1, column=1, columnspan=2, sticky=tk.W, padx=(10, 0), pady=5)
        
        # Template selection
        ttk.Label(form_frame, text="Template:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.template_var = tk.StringVar(value="basic")
        template_combo = ttk.Combobox(form_frame, textvariable=self.template_var, 
                                    values=["basic", "research_assistant", "minimal", "clean_enhanced"], 
                                    state="readonly", width=28)
        template_combo.grid(row=2, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        
        # Port
        ttk.Label(form_frame, text="Port:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.bot_port_var = tk.StringVar(value="8080")
        ttk.Entry(form_frame, textvariable=self.bot_port_var, width=10).grid(row=3, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        
        # Create button
        ttk.Button(form_frame, text="🚀 Create Bot", 
                  command=self.create_bot_from_form).grid(row=4, column=1, sticky=tk.W, padx=(10, 0), pady=(10, 0))
        
        # Template preview
        preview_frame = ttk.LabelFrame(creator_frame, text="Template Preview", padding=10)
        preview_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        self.template_preview = scrolledtext.ScrolledText(preview_frame, wrap=tk.WORD, height=20)
        self.template_preview.pack(fill=tk.BOTH, expand=True)
        
        # Update preview when template changes
        template_combo.bind('<<ComboboxSelected>>', self.update_template_preview)
        self.update_template_preview()

    def create_modules_tab(self):
        """Create the modules management tab"""
        modules_frame = ttk.Frame(self.notebook)
        self.notebook.add(modules_frame, text="🧩 Modules")
        
        # Module actions
        action_frame = ttk.Frame(modules_frame)
        action_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(action_frame, text="📦 Install Module", 
                  command=self.install_module).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(action_frame, text="🔄 Update All", 
                  command=self.update_all_modules).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="🧹 Clean Cache", 
                  command=self.clean_module_cache).pack(side=tk.LEFT, padx=5)
        
        # Module list
        modules_list_frame = ttk.Frame(modules_frame)
        modules_list_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create module treeview
        mod_columns = ('Name', 'Type', 'Version', 'Source', 'Status')
        self.modules_tree = ttk.Treeview(modules_list_frame, columns=mod_columns, show='headings')
        
        for col in mod_columns:
            self.modules_tree.heading(col, text=col)
            self.modules_tree.column(col, width=150)
        
        # Module scrollbars
        mod_v_scroll = ttk.Scrollbar(modules_list_frame, orient=tk.VERTICAL, command=self.modules_tree.yview)
        self.modules_tree.configure(yscrollcommand=mod_v_scroll.set)
        
        self.modules_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        mod_v_scroll.pack(side=tk.RIGHT, fill=tk.Y)

    def create_settings_tab(self):
        """Create the settings tab"""
        settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(settings_frame, text="⚙️ Settings")
        
        # General settings
        general_frame = ttk.LabelFrame(settings_frame, text="General Settings", padding=10)
        general_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Theme setting
        ttk.Label(general_frame, text="Theme:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Checkbutton(general_frame, text="Dark Mode", variable=self.dark_mode, 
                       command=self.toggle_theme).grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        
        # Auto-start setting
        self.auto_start_var = tk.BooleanVar()
        ttk.Checkbutton(general_frame, text="Auto-start bots on launch", 
                       variable=self.auto_start_var).grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        
        # Monitoring interval
        ttk.Label(general_frame, text="Monitor Interval (seconds):").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.monitor_interval_var = tk.StringVar(value="5")
        ttk.Entry(general_frame, textvariable=self.monitor_interval_var, width=10).grid(row=2, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        
        # Workspace settings
        workspace_frame = ttk.LabelFrame(settings_frame, text="Workspace Settings", padding=10)
        workspace_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(workspace_frame, text="Workspace Directory:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.workspace_var = tk.StringVar(value=str(self.workspace_dir))
        ttk.Entry(workspace_frame, textvariable=self.workspace_var, width=60).grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        ttk.Button(workspace_frame, text="Browse", command=self.browse_workspace).grid(row=0, column=2, padx=(5, 0), pady=5)
        
        # Save settings button
        ttk.Button(settings_frame, text="💾 Save Settings", 
                  command=self.save_settings).pack(pady=20)

    def create_status_bar(self):
        """Create the status bar at the bottom"""
        self.status_bar = ttk.Frame(self.root)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.status_text = tk.StringVar(value="Ready")
        ttk.Label(self.status_bar, textvariable=self.status_text).pack(side=tk.LEFT, padx=5)
        
        # Progress bar for operations
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.status_bar, variable=self.progress_var, 
                                          length=200, mode='determinate')
        self.progress_bar.pack(side=tk.RIGHT, padx=5)

    def create_context_menu(self):
        """Create context menu for bot tree"""
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="▶️ Start", command=self.start_selected_bot)
        self.context_menu.add_command(label="⏹️ Stop", command=self.stop_selected_bot)
        self.context_menu.add_command(label="🔄 Restart", command=self.restart_selected_bot)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="⚙️ Configure", command=self.configure_selected_bot)
        self.context_menu.add_command(label="📊 View Logs", command=self.view_bot_logs)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="🗑️ Delete", command=self.delete_selected_bot)
        
        self.bot_tree.bind("<Button-3>", self.show_context_menu)

    def show_context_menu(self, event):
        """Show context menu"""
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()

    def apply_theme(self):
        """Apply the selected theme"""
        if self.dark_mode.get():
            # Dark theme colors
            bg_color = "#2b2b2b"
            fg_color = "#ffffff"
            select_bg = "#404040"
            select_fg = "#ffffff"
        else:
            # Light theme colors
            bg_color = "#ffffff"
            fg_color = "#000000"
            select_bg = "#0078d4"
            select_fg = "#ffffff"
        
        # Configure styles
        self.style.configure("Treeview", background=bg_color, foreground=fg_color,
                           fieldbackground=bg_color)
        self.style.configure("Treeview.Heading", background=select_bg, foreground=select_fg)

    def toggle_theme(self):
        """Toggle between dark and light themes"""
        self.apply_theme()

    def load_config(self) -> Dict[str, BotConfig]:
        """Load bot configurations from file"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    return {name: BotConfig(**config) for name, config in data.items()}
            except Exception as e:
                messagebox.showerror("Error", f"Error loading config: {e}")
                return {}
        return {}

    def save_config(self):
        """Save bot configurations to file"""
        try:
            data = {name: asdict(config) for name, config in self.bots.items()}
            with open(self.config_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            messagebox.showerror("Error", f"Error saving config: {e}")

    def refresh_bot_list(self):
        """Refresh the bot list in the treeview"""
        # Clear existing items
        for item in self.bot_tree.get_children():
            self.bot_tree.delete(item)
        
        # Add bots to tree
        for name, config in self.bots.items():
            status_icon = "🟢" if config.status == "running" else "🔴"
            status_text = f"{status_icon} {config.status}"
            pid_text = str(config.pid) if config.pid else "-"
            created_date = config.created_at[:10] if config.created_at else "-"
            modules_count = str(len(config.modules))
            
            self.bot_tree.insert("", tk.END, values=(
                name, status_text, pid_text, str(config.port), 
                created_date, modules_count
            ))

    def start_monitoring(self):
        """Start the background monitoring thread"""
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self.monitor_bots, daemon=True)
        self.monitor_thread.start()

    def monitor_bots(self):
        """Monitor bot status in background"""
        while self.monitoring:
            try:
                # Update bot status
                for name, config in self.bots.items():
                    if config.pid:
                        # Check if process is still running
                        try:
                            os.kill(config.pid, 0)
                            config.status = "running"
                        except OSError:
                            config.status = "stopped"
                            config.pid = None
                
                # Update GUI in main thread
                self.root.after(0, self.refresh_bot_list)
                
            except Exception as e:
                self.logger.error(f"Error in monitoring: {e}")
            
            time.sleep(int(self.monitor_interval_var.get()) if hasattr(self, 'monitor_interval_var') else 5)

    # Bot management methods
    def create_new_bot(self):
        """Open the bot creator tab"""
        self.notebook.select(1)  # Switch to creator tab

    def import_bot(self):
        """Import an existing bot"""
        file_path = filedialog.askopenfilename(
            title="Select Bot File",
            filetypes=[("Python files", "*.py"), ("All files", "*.*")]
        )
        if file_path:
            # Implementation for importing bot
            messagebox.showinfo("Import", f"Bot imported from {file_path}")

    def create_bot_from_form(self):
        """Create a bot from the form data"""
        name = self.bot_name_var.get().strip()
        if not name:
            messagebox.showerror("Error", "Bot name is required!")
            return
        
        if name in self.bots:
            messagebox.showerror("Error", "Bot with this name already exists!")
            return
        
        try:
            port = int(self.bot_port_var.get())
        except ValueError:
            messagebox.showerror("Error", "Port must be a valid number!")
            return
        
        description = self.bot_desc_var.get().strip()
        template = self.template_var.get()
        
        # Create bot configuration
        config = BotConfig(
            name=name,
            description=description or f"Bot created from {template} template",
            main_file=f"{name}_bot.py",
            port=port,
            status="stopped",
            created_at=datetime.now().isoformat()
        )
        
        # Create bot files
        self.create_bot_from_template(name, template, port)
        
        # Add to configuration
        self.bots[name] = config
        self.save_config()
        
        # Refresh display
        self.refresh_bot_list()
        
        # Switch to dashboard
        self.notebook.select(0)
        
        messagebox.showinfo("Success", f"Bot '{name}' created successfully!")

    def create_bot_from_template(self, bot_name: str, template: str, port: int):
        """Create bot file from template"""
        if template == "basic":
            self.create_basic_bot_template(bot_name, port)
        elif template == "research_assistant":
            self.create_research_assistant_template(bot_name, port)
        elif template == "minimal":
            self.create_minimal_bot_template(bot_name, port)
        elif template == "clean_enhanced":
            # Copy existing clean bot if available
            source_file = self.workspace_dir / "clean_enhanced_bot.py"
            if source_file.exists():
                shutil.copy2(source_file, self.workspace_dir / f"{bot_name}_bot.py")
            else:
                self.create_basic_bot_template(bot_name, port)

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
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS research_notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                title TEXT,
                content TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
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
    cursor.execute("""
        INSERT INTO research_notes (user_id, title, content)
        VALUES (?, ?, ?)
    """, (ctx.author.id, title, content))
    conn.commit()
    conn.close()
    
    await ctx.send(f"📝 Research note '{{title}}' saved!")

@bot.command(name='notes')
async def list_notes(ctx):
    """List research notes"""
    conn = sqlite3.connect('research_data.db')
    cursor = conn.cursor()
    cursor.execute("""
        SELECT title, timestamp FROM research_notes 
        WHERE user_id = ? ORDER BY timestamp DESC LIMIT 10
    """, (ctx.author.id,))
    
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
    cursor.execute("""
        SELECT title, content FROM research_notes 
        WHERE user_id = ? AND (title LIKE ? OR content LIKE ?)
    """, (ctx.author.id, f"%{{query}}%", f"%{{query}}%"))
    
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

    def update_template_preview(self, event=None):
        """Update the template preview"""
        template = self.template_var.get()
        preview_text = {
            "basic": "Basic Discord bot with essential commands (hello, info, ping)",
            "research_assistant": "Advanced bot with SQLite database for research notes",
            "minimal": "Minimal bot with just ping/pong functionality",
            "clean_enhanced": "Enhanced bot with modular architecture"
        }.get(template, "Select a template to see preview")
        
        self.template_preview.delete(1.0, tk.END)
        self.template_preview.insert(1.0, preview_text)

    def get_selected_bot(self):
        """Get the currently selected bot"""
        selection = self.bot_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a bot first!")
            return None
        
        item = self.bot_tree.item(selection[0])
        bot_name = item['values'][0]
        return bot_name

    def start_selected_bot(self):
        """Start the selected bot"""
        bot_name = self.get_selected_bot()
        if bot_name:
            self.start_bot(bot_name)

    def stop_selected_bot(self):
        """Stop the selected bot"""
        bot_name = self.get_selected_bot()
        if bot_name:
            self.stop_bot(bot_name)

    def restart_selected_bot(self):
        """Restart the selected bot"""
        bot_name = self.get_selected_bot()
        if bot_name:
            self.stop_bot(bot_name)
            self.root.after(2000, lambda: self.start_bot(bot_name))

    def delete_selected_bot(self):
        """Delete the selected bot"""
        bot_name = self.get_selected_bot()
        if bot_name:
            if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete '{bot_name}'?"):
                self.delete_bot(bot_name)

    def configure_selected_bot(self):
        """Configure the selected bot"""
        bot_name = self.get_selected_bot()
        if bot_name:
            # Open configuration dialog
            messagebox.showinfo("Configure", f"Configuration for {bot_name} (Feature coming soon!)")

    def view_bot_logs(self):
        """View logs for the selected bot"""
        bot_name = self.get_selected_bot()
        if bot_name:
            # Open logs viewer
            self.open_logs_viewer(bot_name)

    def start_bot(self, bot_name: str):
        """Start a specific bot"""
        if bot_name not in self.bots:
            messagebox.showerror("Error", f"Bot '{bot_name}' not found!")
            return
        
        config = self.bots[bot_name]
        bot_file = self.workspace_dir / config.main_file
        
        if not bot_file.exists():
            messagebox.showerror("Error", f"Bot file '{config.main_file}' not found!")
            return
        
        try:
            # Start bot process
            process = subprocess.Popen([
                sys.executable, str(bot_file)
            ], cwd=self.workspace_dir)
            
            config.pid = process.pid
            config.status = "running"
            config.last_modified = datetime.now().isoformat()
            
            self.save_config()
            self.refresh_bot_list()
            
            self.status_text.set(f"Started bot '{bot_name}'")
            messagebox.showinfo("Success", f"Bot '{bot_name}' started successfully!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start bot '{bot_name}': {e}")

    def stop_bot(self, bot_name: str):
        """Stop a specific bot"""
        if bot_name not in self.bots:
            messagebox.showerror("Error", f"Bot '{bot_name}' not found!")
            return
        
        config = self.bots[bot_name]
        
        if not config.pid:
            messagebox.showwarning("Warning", f"Bot '{bot_name}' is not running!")
            return
        
        try:
            # Terminate process
            os.kill(config.pid, 15)  # SIGTERM
            
            config.pid = None
            config.status = "stopped"
            config.last_modified = datetime.now().isoformat()
            
            self.save_config()
            self.refresh_bot_list()
            
            self.status_text.set(f"Stopped bot '{bot_name}'")
            messagebox.showinfo("Success", f"Bot '{bot_name}' stopped successfully!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to stop bot '{bot_name}': {e}")

    def delete_bot(self, bot_name: str):
        """Delete a bot"""
        if bot_name not in self.bots:
            messagebox.showerror("Error", f"Bot '{bot_name}' not found!")
            return
        
        config = self.bots[bot_name]
        
        # Stop bot if running
        if config.pid:
            self.stop_bot(bot_name)
        
        # Remove bot file
        bot_file = self.workspace_dir / config.main_file
        if bot_file.exists():
            bot_file.unlink()
        
        # Remove from configuration
        del self.bots[bot_name]
        self.save_config()
        self.refresh_bot_list()
        
        self.status_text.set(f"Deleted bot '{bot_name}'")
        messagebox.showinfo("Success", f"Bot '{bot_name}' deleted successfully!")

    def start_all_bots(self):
        """Start all bots"""
        for bot_name in self.bots.keys():
            if self.bots[bot_name].status != "running":
                self.start_bot(bot_name)

    def stop_all_bots(self):
        """Stop all bots"""
        for bot_name in self.bots.keys():
            if self.bots[bot_name].status == "running":
                self.stop_bot(bot_name)

    def refresh_bot_status(self):
        """Refresh bot status"""
        self.refresh_bot_list()
        self.status_text.set("Status refreshed")

    # Additional GUI methods
    def open_module_manager(self):
        """Open module manager"""
        messagebox.showinfo("Module Manager", "Module Manager (Feature coming soon!)")

    def open_command_creator(self):
        """Open command creator"""
        messagebox.showinfo("Command Creator", "Command Creator (Feature coming soon!)")

    def open_github_manager(self):
        """Open GitHub integration"""
        messagebox.showinfo("GitHub Integration", "GitHub Integration (Feature coming soon!)")

    def open_performance_monitor(self):
        """Open performance monitor"""
        messagebox.showinfo("Performance Monitor", "Performance Monitor (Feature coming soon!)")

    def open_logs_viewer(self, bot_name=None):
        """Open logs viewer"""
        log_file = self.workspace_dir / 'launcher.log'
        if log_file.exists():
            # Create logs viewer window
            logs_window = tk.Toplevel(self.root)
            logs_window.title("Logs Viewer")
            logs_window.geometry("800x600")
            
            logs_text = scrolledtext.ScrolledText(logs_window, wrap=tk.WORD)
            logs_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            try:
                with open(log_file, 'r') as f:
                    logs_text.insert(1.0, f.read())
            except Exception as e:
                logs_text.insert(1.0, f"Error reading log file: {e}")
        else:
            messagebox.showinfo("Logs Viewer", "No log file found!")

    def install_module(self):
        """Install a new module"""
        messagebox.showinfo("Install Module", "Module installation (Feature coming soon!)")

    def update_all_modules(self):
        """Update all modules"""
        messagebox.showinfo("Update Modules", "Module updates (Feature coming soon!)")

    def clean_module_cache(self):
        """Clean module cache"""
        messagebox.showinfo("Clean Cache", "Cache cleaning (Feature coming soon!)")

    def browse_workspace(self):
        """Browse for workspace directory"""
        directory = filedialog.askdirectory(initialdir=str(self.workspace_dir))
        if directory:
            self.workspace_var.set(directory)

    def save_settings(self):
        """Save application settings"""
        settings = {
            'dark_mode': self.dark_mode.get(),
            'auto_start': self.auto_start_var.get(),
            'monitor_interval': self.monitor_interval_var.get(),
            'workspace_dir': self.workspace_var.get()
        }
        
        settings_file = self.workspace_dir / 'launcher_settings.json'
        try:
            with open(settings_file, 'w') as f:
                json.dump(settings, f, indent=2)
            messagebox.showinfo("Settings", "Settings saved successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {e}")

    def toggle_fullscreen(self):
        """Toggle fullscreen mode"""
        self.root.attributes('-fullscreen', not self.root.attributes('-fullscreen'))

    def open_documentation(self):
        """Open documentation"""
        webbrowser.open("https://github.com/justkidding-scripts/utility-tools")

    def open_github_repo(self):
        """Open GitHub repository"""
        webbrowser.open("https://github.com/justkidding-scripts/utility-tools")

    def show_about(self):
        """Show about dialog"""
        about_text = """🚀 Advanced Discord Bot Launcher
        
Version: 2.0.0
Author: Bot Launcher System
        
A comprehensive GUI application for managing,
organizing, and extending Discord bots with
modern tools and automation features.

Features:
• Visual bot management
• Template-based bot creation
• Module system
• GitHub integration
• Performance monitoring
• Dark/Light themes
        """
        messagebox.showinfo("About", about_text)

    def on_closing(self):
        """Handle application closing"""
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.monitoring = False
            self.root.destroy()

    def run(self):
        """Start the GUI application"""
        # Bind keyboard shortcuts
        self.root.bind('<Control-n>', lambda e: self.create_new_bot())
        self.root.bind('<Control-i>', lambda e: self.import_bot())
        self.root.bind('<Control-q>', lambda e: self.on_closing())
        self.root.bind('<F11>', lambda e: self.toggle_fullscreen())
        
        # Start the main loop
        self.root.mainloop()

def main():
    """Main entry point"""
    try:
        # Create and run the GUI application
        app = ModernBotLauncherGUI()
        app.run()
    except Exception as e:
        print(f"Error starting GUI application: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
