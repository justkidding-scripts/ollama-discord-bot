#!/usr/bin/env python3
"""
🚀 Advanced Discord Bot Launcher - Native GUI Version
A professional native GUI application for managing Discord bots

Features:
- Modern native interface using PyQt5
- Real-time bot status monitoring
- Template-based bot creation
- Configuration management
- Log viewer and system monitoring
- Dark/Light theme support
"""

import sys
import os
import json
import subprocess
import threading
import time
import logging
import webbrowser
import base64
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import sqlite3
try:
    from cryptography.fernet import Fernet
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

# PyQt5 imports
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QGridLayout, QTabWidget, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QLineEdit, QTextEdit, QComboBox, QCheckBox,
    QProgressBar, QStatusBar, QMenuBar, QMenu, QAction, QMessageBox,
    QDialog, QDialogButtonBox, QFormLayout, QGroupBox, QSplitter,
    QTreeWidget, QTreeWidgetItem, QHeaderView, QFrame, QScrollArea,
    QSpinBox, QFileDialog, QSystemTrayIcon, QListWidget, QListWidgetItem,
    QAbstractItemView, QInputDialog, QToolButton
)
from PyQt5.QtCore import (
    Qt, QTimer, QThread, pyqtSignal, QSize, QRect, QSettings,
    QStandardPaths, QUrl, QPropertyAnimation, QEasingCurve
)
from PyQt5.QtGui import (
    QIcon, QFont, QPixmap, QPalette, QColor, QDesktopServices,
    QFontMetrics, QPainter, QBrush, QPen
)

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

@dataclass
class Credential:
    name: str
    type: str  # 'token', 'webhook', 'api_key', 'url', 'other'
    value: str
    description: str = ""
    created_at: str = ""
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()

class BotMonitorThread(QThread):
    """Background thread for monitoring bot status"""
    status_updated = pyqtSignal(str, str, int)  # bot_name, status, pid
    
    def __init__(self, bots: Dict[str, BotConfig]):
        super().__init__()
        self.bots = bots
        self.running = False
    
    def run(self):
        self.running = True
        while self.running:
            for name, config in self.bots.items():
                if config.pid:
                    try:
                        # Check if process is still running
                        os.kill(config.pid, 0)
                        if config.status != "running":
                            config.status = "running"
                            self.status_updated.emit(name, "running", config.pid)
                    except OSError:
                        # Process is dead
                        config.status = "stopped"
                        config.pid = None
                        self.status_updated.emit(name, "stopped", 0)
            
            time.sleep(2)  # Check every 2 seconds
    
    def stop(self):
        self.running = False
        self.wait()

class BotCreatorDialog(QDialog):
    """Dialog for creating new bots"""
    
    def __init__(self, parent=None, workspace_dir=None):
        super().__init__(parent)
        self.workspace_dir = workspace_dir or Path.cwd()
        self.setWindowTitle("Create New Bot")
        self.setModal(True)
        self.resize(600, 500)
        
        self.setup_ui()
        self.bot_config = None
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Form section
        form_group = QGroupBox("Bot Configuration")
        form_layout = QFormLayout()
        
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Enter bot name (required)")
        self.name_edit.setToolTip("Enter a unique name for your bot (required)")
        form_layout.addRow("Bot Name:", self.name_edit)
        
        self.desc_edit = QLineEdit()
        self.desc_edit.setPlaceholderText("Bot description (optional)")
        self.desc_edit.setToolTip("Brief description of what your bot does")
        form_layout.addRow("Description:", self.desc_edit)
        
        self.template_combo = QComboBox()
        self.template_combo.addItems([
            "basic", "research_assistant", "minimal", "clean_enhanced"
        ])
        self.template_combo.currentTextChanged.connect(self.update_preview)
        self.template_combo.setToolTip("Select a bot template with pre-configured features and capabilities")
        form_layout.addRow("Template:", self.template_combo)
        
        self.port_spin = QSpinBox()
        self.port_spin.setRange(1000, 65535)
        self.port_spin.setValue(8080)
        self.port_spin.setToolTip("Port number for the bot (if applicable)")
        form_layout.addRow("Port:", self.port_spin)
        
        form_group.setLayout(form_layout)
        layout.addWidget(form_group)
        
        # Preview section
        preview_group = QGroupBox("Template Preview")
        preview_layout = QVBoxLayout()
        
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setMaximumHeight(200)
        preview_layout.addWidget(self.preview_text)
        
        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.button(QDialogButtonBox.Ok).setToolTip("Create a new bot with the specified configuration")
        button_box.button(QDialogButtonBox.Cancel).setToolTip("Cancel bot creation and return to dashboard")
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        # Initial preview
        self.update_preview()
    
    def update_preview(self):
        template = self.template_combo.currentText()
        preview_text = {
            "basic": "Creates a basic Discord bot with essential commands (hello, info, ping)\nIncludes logging, command handling, and proper Discord intents setup.",
            "research_assistant": "Advanced bot with SQLite database integration for research notes\nFeatures: note taking, search functionality, data persistence.",
            "minimal": "Minimal bot implementation with just ping/pong functionality\nPerfect for learning or as a starting template.",
            "clean_enhanced": "Enhanced bot with modular architecture and advanced features\nIncludes plugin system, configuration management, and monitoring."
        }.get(template, "Select a template to see preview")
        
        self.preview_text.setPlainText(preview_text)
    
    def accept(self):
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Warning", "Bot name is required!")
            return
        
        self.bot_config = BotConfig(
            name=name,
            description=self.desc_edit.text().strip() or f"Bot created from {self.template_combo.currentText()} template",
            main_file=f"{name}_bot.py",
            port=self.port_spin.value(),
            status="stopped",
            created_at=datetime.now().isoformat()
        )
        
        super().accept()

class CredentialsManagerDialog(QDialog):
    """Dialog for managing Discord credentials, tokens, webhooks, etc."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("🔐 Credentials Manager")
        self.setModal(True)
        self.resize(700, 500)
        
        self.credentials = self.load_credentials()
        self.setup_ui()
        self.refresh_credentials_list()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        header_label = QLabel("Manage Discord Tokens, Webhooks, and API Keys")
        header_label.setStyleSheet("font-size: 14px; font-weight: bold; margin: 10px;")
        header_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(header_label)
        
        # Main content
        content_layout = QHBoxLayout()
        
        # Left side - Credentials list
        left_group = QGroupBox("Stored Credentials")
        left_layout = QVBoxLayout()
        
        self.credentials_list = QListWidget()
        self.credentials_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.credentials_list.itemSelectionChanged.connect(self.on_credential_selected)
        left_layout.addWidget(self.credentials_list)
        
        # List buttons
        list_buttons = QHBoxLayout()
        
        self.add_btn = QPushButton("➕ Add")
        self.add_btn.clicked.connect(self.add_credential)
        self.add_btn.setToolTip("Add a new credential")
        list_buttons.addWidget(self.add_btn)
        
        self.edit_btn = QPushButton("✏️ Edit")
        self.edit_btn.clicked.connect(self.edit_credential)
        self.edit_btn.setToolTip("Edit the selected credential")
        self.edit_btn.setEnabled(False)
        list_buttons.addWidget(self.edit_btn)
        
        self.delete_btn = QPushButton("🗑️ Delete")
        self.delete_btn.clicked.connect(self.delete_credential)
        self.delete_btn.setToolTip("Delete the selected credential")
        self.delete_btn.setEnabled(False)
        list_buttons.addWidget(self.delete_btn)
        
        self.copy_btn = QPushButton("📋 Copy")
        self.copy_btn.clicked.connect(self.copy_credential_value)
        self.copy_btn.setToolTip("Copy credential value to clipboard")
        self.copy_btn.setEnabled(False)
        list_buttons.addWidget(self.copy_btn)
        
        left_layout.addLayout(list_buttons)
        left_group.setLayout(left_layout)
        content_layout.addWidget(left_group, 2)
        
        # Right side - Credential details
        right_group = QGroupBox("Credential Details")
        right_layout = QFormLayout()
        
        self.name_label = QLabel("-")
        right_layout.addRow("Name:", self.name_label)
        
        self.type_label = QLabel("-")
        right_layout.addRow("Type:", self.type_label)
        
        self.description_label = QLabel("-")
        self.description_label.setWordWrap(True)
        right_layout.addRow("Description:", self.description_label)
        
        self.value_label = QLabel("-")
        self.value_label.setStyleSheet("font-family: monospace; background-color: #f0f0f0; padding: 5px; border: 1px solid #ccc;")
        self.value_label.setWordWrap(True)
        right_layout.addRow("Value:", self.value_label)
        
        self.created_label = QLabel("-")
        right_layout.addRow("Created:", self.created_label)
        
        right_group.setLayout(right_layout)
        content_layout.addWidget(right_group, 1)
        
        layout.addLayout(content_layout)
        
        # Quick access section
        quick_group = QGroupBox("🚀 Quick Access")
        quick_layout = QHBoxLayout()
        
        self.quick_combo = QComboBox()
        self.quick_combo.setToolTip("Select a credential to quickly copy to clipboard")
        quick_layout.addWidget(self.quick_combo)
        
        self.quick_copy_btn = QPushButton("📋 Quick Copy")
        self.quick_copy_btn.clicked.connect(self.quick_copy_selected)
        self.quick_copy_btn.setToolTip("Copy selected credential to clipboard")
        quick_layout.addWidget(self.quick_copy_btn)
        
        quick_group.setLayout(quick_layout)
        layout.addWidget(quick_group)
        
        # Bottom buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Close)
        button_box.button(QDialogButtonBox.Close).setToolTip("Close the credentials manager")
        button_box.rejected.connect(self.accept)
        layout.addWidget(button_box)
    
    def load_credentials(self) -> Dict[str, Credential]:
        """Load credentials from encrypted storage"""
        credentials_file = self.parent.workspace_dir / "credentials.enc" if self.parent else Path("credentials.enc")
        
        if not credentials_file.exists():
            return {}
        
        try:
            if CRYPTO_AVAILABLE:
                # Load encrypted credentials
                key_file = credentials_file.parent / ".cred_key"
                if key_file.exists():
                    with open(key_file, 'rb') as f:
                        key = f.read()
                    
                    fernet = Fernet(key)
                    with open(credentials_file, 'rb') as f:
                        encrypted_data = f.read()
                    
                    decrypted_data = fernet.decrypt(encrypted_data)
                    data = json.loads(decrypted_data.decode())
                    
                    return {name: Credential(**cred) for name, cred in data.items()}
            else:
                # Fallback to base64 encoding (less secure)
                with open(credentials_file, 'r') as f:
                    encoded_data = f.read()
                
                decoded_data = base64.b64decode(encoded_data.encode()).decode()
                data = json.loads(decoded_data)
                
                return {name: Credential(**cred) for name, cred in data.items()}
                
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load credentials: {e}")
            return {}
    
    def save_credentials(self):
        """Save credentials to encrypted storage"""
        credentials_file = self.parent.workspace_dir / "credentials.enc" if self.parent else Path("credentials.enc")
        
        try:
            data = {name: asdict(cred) for name, cred in self.credentials.items()}
            json_data = json.dumps(data, indent=2)
            
            if CRYPTO_AVAILABLE:
                # Save with encryption
                key_file = credentials_file.parent / ".cred_key"
                
                if not key_file.exists():
                    # Generate new encryption key
                    key = Fernet.generate_key()
                    with open(key_file, 'wb') as f:
                        f.write(key)
                    key_file.chmod(0o600)  # Restrict permissions
                else:
                    with open(key_file, 'rb') as f:
                        key = f.read()
                
                fernet = Fernet(key)
                encrypted_data = fernet.encrypt(json_data.encode())
                
                with open(credentials_file, 'wb') as f:
                    f.write(encrypted_data)
                    
            else:
                # Fallback to base64 encoding
                encoded_data = base64.b64encode(json_data.encode()).decode()
                with open(credentials_file, 'w') as f:
                    f.write(encoded_data)
            
            credentials_file.chmod(0o600)  # Restrict permissions
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save credentials: {e}")
    
    def refresh_credentials_list(self):
        """Refresh the credentials list and quick access combo"""
        self.credentials_list.clear()
        self.quick_combo.clear()
        
        for name, cred in self.credentials.items():
            # List widget item with icon based on type
            icon_map = {
                'token': '🔑',
                'webhook': '🔗',
                'api_key': '🗝️',
                'url': '🌐',
                'other': '📝'
            }
            icon = icon_map.get(cred.type, '📝')
            
            item = QListWidgetItem(f"{icon} {name} ({cred.type})")
            item.setData(Qt.UserRole, name)
            self.credentials_list.addItem(item)
            
            # Quick access combo
            self.quick_combo.addItem(f"{icon} {name}", name)
    
    def on_credential_selected(self):
        """Handle credential selection"""
        selected_items = self.credentials_list.selectedItems()
        
        if selected_items:
            item = selected_items[0]
            cred_name = item.data(Qt.UserRole)
            cred = self.credentials.get(cred_name)
            
            if cred:
                self.name_label.setText(cred.name)
                self.type_label.setText(cred.type.title())
                self.description_label.setText(cred.description or "No description")
                
                # Mask sensitive values
                if cred.type in ['token', 'api_key']:
                    masked_value = f"{cred.value[:8]}...{cred.value[-4:]}" if len(cred.value) > 12 else "***masked***"
                    self.value_label.setText(masked_value)
                else:
                    self.value_label.setText(cred.value)
                
                self.created_label.setText(cred.created_at[:19].replace('T', ' '))
                
                # Enable buttons
                self.edit_btn.setEnabled(True)
                self.delete_btn.setEnabled(True)
                self.copy_btn.setEnabled(True)
            else:
                self.clear_details()
        else:
            self.clear_details()
    
    def clear_details(self):
        """Clear credential details display"""
        self.name_label.setText("-")
        self.type_label.setText("-")
        self.description_label.setText("-")
        self.value_label.setText("-")
        self.created_label.setText("-")
        
        self.edit_btn.setEnabled(False)
        self.delete_btn.setEnabled(False)
        self.copy_btn.setEnabled(False)
    
    def add_credential(self):
        """Add a new credential"""
        dialog = CredentialEditDialog(self)
        if dialog.exec_() == QDialog.Accepted and dialog.credential:
            cred = dialog.credential
            if cred.name in self.credentials:
                QMessageBox.warning(self, "Warning", f"Credential '{cred.name}' already exists!")
                return
            
            self.credentials[cred.name] = cred
            self.save_credentials()
            self.refresh_credentials_list()
    
    def edit_credential(self):
        """Edit selected credential"""
        selected_items = self.credentials_list.selectedItems()
        if not selected_items:
            return
        
        cred_name = selected_items[0].data(Qt.UserRole)
        cred = self.credentials.get(cred_name)
        
        if cred:
            dialog = CredentialEditDialog(self, cred)
            if dialog.exec_() == QDialog.Accepted and dialog.credential:
                new_cred = dialog.credential
                
                # Handle name change
                if new_cred.name != cred_name:
                    del self.credentials[cred_name]
                
                self.credentials[new_cred.name] = new_cred
                self.save_credentials()
                self.refresh_credentials_list()
    
    def delete_credential(self):
        """Delete selected credential"""
        selected_items = self.credentials_list.selectedItems()
        if not selected_items:
            return
        
        cred_name = selected_items[0].data(Qt.UserRole)
        
        reply = QMessageBox.question(self, "Delete Credential", 
                                   f"Are you sure you want to delete '{cred_name}'?\n\nThis action cannot be undone.",
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            del self.credentials[cred_name]
            self.save_credentials()
            self.refresh_credentials_list()
            self.clear_details()
    
    def copy_credential_value(self):
        """Copy selected credential value to clipboard"""
        selected_items = self.credentials_list.selectedItems()
        if not selected_items:
            return
        
        cred_name = selected_items[0].data(Qt.UserRole)
        cred = self.credentials.get(cred_name)
        
        if cred:
            clipboard = QApplication.clipboard()
            clipboard.setText(cred.value)
            self.parent.status_bar.showMessage(f"Copied '{cred_name}' to clipboard") if self.parent else None
    
    def quick_copy_selected(self):
        """Quick copy from combo box selection"""
        current_data = self.quick_combo.currentData()
        if current_data:
            cred = self.credentials.get(current_data)
            if cred:
                clipboard = QApplication.clipboard()
                clipboard.setText(cred.value)
                self.parent.status_bar.showMessage(f"Copied '{cred.name}' to clipboard") if self.parent else None

class CredentialEditDialog(QDialog):
    """Dialog for adding/editing credentials"""
    
    def __init__(self, parent=None, credential=None):
        super().__init__(parent)
        self.credential = None
        self.editing_credential = credential
        
        self.setWindowTitle("Edit Credential" if credential else "Add Credential")
        self.setModal(True)
        self.resize(400, 300)
        
        self.setup_ui()
        
        if credential:
            self.populate_fields(credential)
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Form
        form_layout = QFormLayout()
        
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("e.g., main_bot_token, webhook_logs")
        self.name_edit.setToolTip("Unique name for this credential")
        form_layout.addRow("Name:", self.name_edit)
        
        self.type_combo = QComboBox()
        self.type_combo.addItems(['token', 'webhook', 'api_key', 'url', 'other'])
        self.type_combo.setToolTip("Type of credential being stored")
        form_layout.addRow("Type:", self.type_combo)
        
        self.value_edit = QLineEdit()
        self.value_edit.setPlaceholderText("Enter the actual token/webhook/URL value")
        self.value_edit.setToolTip("The sensitive value to store securely")
        form_layout.addRow("Value:", self.value_edit)
        
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("Optional description...")
        self.description_edit.setMaximumHeight(80)
        self.description_edit.setToolTip("Optional description for this credential")
        form_layout.addRow("Description:", self.description_edit)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.button(QDialogButtonBox.Ok).setToolTip("Save this credential")
        button_box.button(QDialogButtonBox.Cancel).setToolTip("Cancel without saving")
        button_box.accepted.connect(self.accept_credential)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def populate_fields(self, credential):
        """Populate form fields with existing credential data"""
        self.name_edit.setText(credential.name)
        self.type_combo.setCurrentText(credential.type)
        self.value_edit.setText(credential.value)
        self.description_edit.setPlainText(credential.description)
    
    def accept_credential(self):
        """Validate and accept credential"""
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Warning", "Credential name is required!")
            return
        
        value = self.value_edit.text().strip()
        if not value:
            QMessageBox.warning(self, "Warning", "Credential value is required!")
            return
        
        self.credential = Credential(
            name=name,
            type=self.type_combo.currentText(),
            value=value,
            description=self.description_edit.toPlainText().strip(),
            created_at=self.editing_credential.created_at if self.editing_credential else ""
        )
        
        super().accept()

class LogViewerDialog(QDialog):
    """Dialog for viewing bot logs"""
    
    def __init__(self, parent=None, log_file=None):
        super().__init__(parent)
        self.log_file = log_file
        self.setWindowTitle("Log Viewer")
        self.resize(800, 600)
        
        self.setup_ui()
        self.load_logs()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Controls
        controls_layout = QHBoxLayout()
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.load_logs)
        refresh_btn.setToolTip("Reload the log file to show latest entries")
        controls_layout.addWidget(refresh_btn)
        
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.clear_logs)
        clear_btn.setToolTip("Clear the displayed log content")
        controls_layout.addWidget(clear_btn)
        
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
        
        # Log display
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 10))
        layout.addWidget(self.log_text)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        close_btn.setToolTip("Close the log viewer and return to dashboard")
        layout.addWidget(close_btn)
    
    def load_logs(self):
        if self.log_file and self.log_file.exists():
            try:
                with open(self.log_file, 'r') as f:
                    content = f.read()
                    # Show last 1000 lines to avoid memory issues
                    lines = content.split('\n')
                    if len(lines) > 1000:
                        lines = lines[-1000:]
                        content = '\n'.join(lines)
                    self.log_text.setPlainText(content)
                    
                    # Scroll to bottom
                    scrollbar = self.log_text.verticalScrollBar()
                    scrollbar.setValue(scrollbar.maximum())
            except Exception as e:
                self.log_text.setPlainText(f"Error reading log file: {e}")
        else:
            self.log_text.setPlainText("No log file found or file doesn't exist.")
    
    def clear_logs(self):
        self.log_text.clear()

class DiscordBotLauncherGUI(QMainWindow):
    """Main GUI application window"""
    
    def __init__(self):
        super().__init__()
        
        # Initialize paths and configuration
        self.workspace_dir = Path("/home/nike/ollama-discord-bot")
        self.config_file = self.workspace_dir / "launcher_config.json"
        self.db_file = self.workspace_dir / "launcher.db"
        self.log_file = self.workspace_dir / "launcher.log"
        
        # Create directories
        self.workspace_dir.mkdir(exist_ok=True)
        
        # Initialize database and configuration
        self.init_database()
        self.bots: Dict[str, BotConfig] = self.load_config()
        
        # Setup logging
        self.setup_logging()
        
        # Initialize GUI
        self.setup_ui()
        self.apply_dark_theme()
        
        # Start monitoring thread
        self.monitor_thread = BotMonitorThread(self.bots)
        self.monitor_thread.status_updated.connect(self.update_bot_status)
        self.monitor_thread.start()
        
        # Auto-refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_bot_table)
        self.refresh_timer.start(5000)  # Refresh every 5 seconds
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("Bot Launcher GUI started")
    
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.log_file),
                logging.StreamHandler()
            ]
        )
    
    def init_database(self):
        """Initialize SQLite database"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
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
        
        conn.commit()
        conn.close()
    
    def setup_ui(self):
        """Setup the main user interface"""
        self.setWindowTitle("🚀 Discord Bot Launcher - Native GUI")
        self.setGeometry(100, 100, 1200, 800)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
        # Create main tabs
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # Dashboard tab
        self.create_dashboard_tab()
        
        # Bot Creator tab
        self.create_creator_tab()
        
        # Settings tab
        self.create_settings_tab()
        
        # Initial refresh
        self.refresh_bot_table()
    
    def create_menu_bar(self):
        """Create application menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('&File')
        
        new_bot_action = QAction('&New Bot', self)
        new_bot_action.setShortcut('Ctrl+N')
        new_bot_action.triggered.connect(self.create_new_bot)
        file_menu.addAction(new_bot_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('E&xit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Bots menu
        bots_menu = menubar.addMenu('&Bots')
        
        start_all_action = QAction('Start &All', self)
        start_all_action.triggered.connect(self.start_all_bots)
        bots_menu.addAction(start_all_action)
        
        stop_all_action = QAction('&Stop All', self)
        stop_all_action.triggered.connect(self.stop_all_bots)
        bots_menu.addAction(stop_all_action)
        
        bots_menu.addSeparator()
        
        refresh_action = QAction('&Refresh', self)
        refresh_action.setShortcut('F5')
        refresh_action.triggered.connect(self.refresh_bot_table)
        bots_menu.addAction(refresh_action)
        
        # Developer Tools menu
        dev_menu = menubar.addMenu('&Developer')
        
        discord_cli_action = QAction('Open Discord &CLI Terminal', self)
        discord_cli_action.setShortcut('Ctrl+T')
        discord_cli_action.triggered.connect(self.open_discord_cli_terminal)
        dev_menu.addAction(discord_cli_action)
        
        dev_portal_action = QAction('Open Developer &Portal', self)
        dev_portal_action.setShortcut('Ctrl+P')
        dev_portal_action.triggered.connect(self.open_discord_developer_portal)
        dev_menu.addAction(dev_portal_action)
        
        dev_menu.addSeparator()
        
        docs_action = QAction('Discord.py &Documentation', self)
        docs_action.triggered.connect(self.open_discordpy_docs)
        dev_menu.addAction(docs_action)
        
        dev_menu.addSeparator()
        
        credentials_action = QAction('🔐 &Credentials Manager', self)
        credentials_action.setShortcut('Ctrl+K')
        credentials_action.triggered.connect(self.open_credentials_manager)
        dev_menu.addAction(credentials_action)
        
        # Help menu
        help_menu = menubar.addMenu('&Help')
        
        about_action = QAction('&About', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def create_dashboard_tab(self):
        """Create the main dashboard tab"""
        dashboard_widget = QWidget()
        layout = QVBoxLayout(dashboard_widget)
        
        # Action buttons
        buttons_layout = QHBoxLayout()
        
        self.create_btn = QPushButton("📱 Create New Bot")
        self.create_btn.clicked.connect(self.create_new_bot)
        self.create_btn.setToolTip("Create a new Discord bot from available templates")
        buttons_layout.addWidget(self.create_btn)
        
        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.clicked.connect(self.refresh_bot_table)
        self.refresh_btn.setToolTip("Refresh the bot list and status information")
        buttons_layout.addWidget(self.refresh_btn)
        
        buttons_layout.addStretch()
        
        self.start_all_btn = QPushButton("▶️ Start All")
        self.start_all_btn.clicked.connect(self.start_all_bots)
        self.start_all_btn.setToolTip("Start all configured bots at once")
        buttons_layout.addWidget(self.start_all_btn)
        
        self.stop_all_btn = QPushButton("⏹️ Stop All")
        self.stop_all_btn.clicked.connect(self.stop_all_bots)
        self.stop_all_btn.setToolTip("Stop all running bots at once")
        buttons_layout.addWidget(self.stop_all_btn)
        
        layout.addLayout(buttons_layout)
        
        # Bot table
        self.bot_table = QTableWidget()
        self.bot_table.setColumnCount(6)
        self.bot_table.setHorizontalHeaderLabels([
            "Name", "Status", "PID", "Port", "Created", "Actions"
        ])
        self.bot_table.setToolTip("Select a bot to view details and perform actions")
        
        # Make table look better
        self.bot_table.horizontalHeader().setStretchLastSection(True)
        self.bot_table.setAlternatingRowColors(True)
        self.bot_table.setSelectionBehavior(QTableWidget.SelectRows)
        
        layout.addWidget(self.bot_table)
        
        # Control buttons
        controls_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("▶️ Start")
        self.start_btn.clicked.connect(self.start_selected_bot)
        self.start_btn.setToolTip("Start the selected bot instance")
        controls_layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("⏹️ Stop")
        self.stop_btn.clicked.connect(self.stop_selected_bot)
        self.stop_btn.setToolTip("Stop the selected running bot")
        controls_layout.addWidget(self.stop_btn)
        
        self.restart_btn = QPushButton("🔄 Restart")
        self.restart_btn.clicked.connect(self.restart_selected_bot)
        self.restart_btn.setToolTip("Restart the selected bot (stop then start)")
        controls_layout.addWidget(self.restart_btn)
        
        controls_layout.addStretch()
        
        self.logs_btn = QPushButton("📊 View Logs")
        self.logs_btn.clicked.connect(self.view_bot_logs)
        self.logs_btn.setToolTip("View the log output from the selected bot")
        controls_layout.addWidget(self.logs_btn)
        
        self.delete_btn = QPushButton("🗑️ Delete")
        self.delete_btn.clicked.connect(self.delete_selected_bot)
        self.delete_btn.setToolTip("Permanently delete the selected bot and its configuration")
        controls_layout.addWidget(self.delete_btn)
        
        controls_layout.addStretch()
        
        # Developer tools buttons
        self.discord_cli_btn = QPushButton("💻 Discord CLI")
        self.discord_cli_btn.clicked.connect(self.open_discord_cli_terminal)
        self.discord_cli_btn.setToolTip("Open terminal with Discord CLI for bot management")
        self.discord_cli_btn.setStyleSheet("QPushButton { background-color: #5865F2; color: white; }")
        controls_layout.addWidget(self.discord_cli_btn)
        
        self.dev_portal_btn = QPushButton("🌐 Dev Portal")
        self.dev_portal_btn.clicked.connect(self.open_discord_developer_portal)
        self.dev_portal_btn.setToolTip("Open Discord Developer Portal in browser")
        self.dev_portal_btn.setStyleSheet("QPushButton { background-color: #5865F2; color: white; }")
        controls_layout.addWidget(self.dev_portal_btn)
        
        self.credentials_btn = QPushButton("🔐 Credentials")
        self.credentials_btn.clicked.connect(self.open_credentials_manager)
        self.credentials_btn.setToolTip("Manage Discord tokens, webhooks, and API keys")
        self.credentials_btn.setStyleSheet("QPushButton { background-color: #FF6B35; color: white; }")
        controls_layout.addWidget(self.credentials_btn)
        
        layout.addLayout(controls_layout)
        
        self.tab_widget.addTab(dashboard_widget, "🤖 Dashboard")
    
    def create_creator_tab(self):
        """Create the bot creator tab"""
        creator_widget = QWidget()
        layout = QVBoxLayout(creator_widget)
        
        # Instructions
        info_label = QLabel("Create a new Discord bot using our templates")
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setStyleSheet("font-size: 14px; font-weight: bold; margin: 10px;")
        layout.addWidget(info_label)
        
        # Create button
        create_new_btn = QPushButton("🛮️ Create New Bot")
        create_new_btn.setMinimumHeight(50)
        create_new_btn.clicked.connect(self.create_new_bot)
        create_new_btn.setToolTip("Open the bot creation wizard to create a new Discord bot")
        layout.addWidget(create_new_btn)
        
        # Templates info
        templates_group = QGroupBox("Available Templates")
        templates_layout = QVBoxLayout()
        
        templates = [
            ("Basic Bot", "Essential Discord bot with basic commands and logging"),
            ("Research Assistant", "Advanced bot with SQLite database for note-taking"),
            ("Minimal Bot", "Simple ping/pong bot perfect for beginners"),
            ("Clean Enhanced", "Modular bot with plugin architecture")
        ]
        
        for name, desc in templates:
            template_widget = QFrame()
            template_widget.setFrameStyle(QFrame.StyledPanel)
            template_layout = QVBoxLayout(template_widget)
            
            name_label = QLabel(name)
            name_label.setStyleSheet("font-weight: bold;")
            template_layout.addWidget(name_label)
            
            desc_label = QLabel(desc)
            desc_label.setWordWrap(True)
            template_layout.addWidget(desc_label)
            
            templates_layout.addWidget(template_widget)
        
        templates_group.setLayout(templates_layout)
        layout.addWidget(templates_group)
        
        # Developer Tools section
        dev_tools_group = QGroupBox("🛠️ Developer Tools")
        dev_tools_layout = QHBoxLayout()
        
        # Discord CLI button
        discord_cli_creator_btn = QPushButton("💻 Discord CLI Terminal")
        discord_cli_creator_btn.clicked.connect(self.open_discord_cli_terminal)
        discord_cli_creator_btn.setToolTip("Open terminal with Discord development tools and CLI")
        discord_cli_creator_btn.setStyleSheet("QPushButton { background-color: #5865F2; color: white; padding: 10px; }")
        dev_tools_layout.addWidget(discord_cli_creator_btn)
        
        # Developer Portal button
        dev_portal_creator_btn = QPushButton("🌐 Developer Portal")
        dev_portal_creator_btn.clicked.connect(self.open_discord_developer_portal)
        dev_portal_creator_btn.setToolTip("Open Discord Developer Portal in your browser")
        dev_portal_creator_btn.setStyleSheet("QPushButton { background-color: #5865F2; color: white; padding: 10px; }")
        dev_tools_layout.addWidget(dev_portal_creator_btn)
        
        # Discord.py Documentation button
        docs_creator_btn = QPushButton("📚 Documentation")
        docs_creator_btn.clicked.connect(self.open_discordpy_docs)
        docs_creator_btn.setToolTip("Open Discord.py documentation in your browser")
        docs_creator_btn.setStyleSheet("QPushButton { background-color: #5865F2; color: white; padding: 10px; }")
        dev_tools_layout.addWidget(docs_creator_btn)
        
        # Credentials Manager button
        credentials_creator_btn = QPushButton("🔐 Credentials")
        credentials_creator_btn.clicked.connect(self.open_credentials_manager)
        credentials_creator_btn.setToolTip("Manage Discord tokens, webhooks, and API keys")
        credentials_creator_btn.setStyleSheet("QPushButton { background-color: #FF6B35; color: white; padding: 10px; }")
        dev_tools_layout.addWidget(credentials_creator_btn)
        
        dev_tools_group.setLayout(dev_tools_layout)
        layout.addWidget(dev_tools_group)
        
        layout.addStretch()
        
        self.tab_widget.addTab(creator_widget, "🛮️ Creator")
    
    def create_settings_tab(self):
        """Create the settings tab"""
        settings_widget = QWidget()
        layout = QVBoxLayout(settings_widget)
        
        # General settings
        general_group = QGroupBox("General Settings")
        general_layout = QFormLayout()
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark", "Light"])
        self.theme_combo.currentTextChanged.connect(self.change_theme)
        self.theme_combo.setToolTip("Switch between dark and light theme")
        general_layout.addRow("Theme:", self.theme_combo)
        
        self.auto_start_check = QCheckBox("Auto-start bots on launch")
        self.auto_start_check.setToolTip("Automatically start all bots when the launcher starts")
        general_layout.addRow(self.auto_start_check)
        
        general_group.setLayout(general_layout)
        layout.addWidget(general_group)
        
        # Workspace settings
        workspace_group = QGroupBox("Workspace Settings")
        workspace_layout = QFormLayout()
        
        workspace_label = QLabel(str(self.workspace_dir))
        workspace_layout.addRow("Workspace Directory:", workspace_label)
        
        workspace_group.setLayout(workspace_layout)
        layout.addWidget(workspace_group)
        
        layout.addStretch()
        
        self.tab_widget.addTab(settings_widget, "⚙️ Settings")
    
    def apply_dark_theme(self):
        """Apply dark theme to the application"""
        dark_stylesheet = """
        QMainWindow {
            background-color: #2b2b2b;
            color: #ffffff;
        }
        QTabWidget::pane {
            border: 1px solid #3d3d3d;
            background-color: #2b2b2b;
        }
        QTabBar::tab {
            background-color: #3d3d3d;
            color: #ffffff;
            padding: 8px 12px;
            margin: 2px;
            border-radius: 4px;
        }
        QTabBar::tab:selected {
            background-color: #4CAF50;
        }
        QPushButton {
            background-color: #4CAF50;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #45a049;
        }
        QPushButton:pressed {
            background-color: #3e8e41;
        }
        QTableWidget {
            background-color: #3d3d3d;
            alternate-background-color: #4d4d4d;
            color: #ffffff;
            gridline-color: #555555;
        }
        QHeaderView::section {
            background-color: #2b2b2b;
            color: #ffffff;
            padding: 8px;
            border: 1px solid #555555;
            font-weight: bold;
        }
        QGroupBox {
            font-weight: bold;
            border: 2px solid #555555;
            border-radius: 4px;
            margin-top: 10px;
            padding-top: 10px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
        }
        QLineEdit, QComboBox, QSpinBox {
            background-color: #3d3d3d;
            color: #ffffff;
            border: 1px solid #555555;
            padding: 4px;
            border-radius: 4px;
        }
        QTextEdit {
            background-color: #3d3d3d;
            color: #ffffff;
            border: 1px solid #555555;
        }
        """
        self.setStyleSheet(dark_stylesheet)
    
    def change_theme(self, theme):
        """Change application theme"""
        if theme == "Dark":
            self.apply_dark_theme()
        else:
            self.setStyleSheet("")  # Reset to default light theme
    
    def load_config(self) -> Dict[str, BotConfig]:
        """Load bot configurations from file"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    return {name: BotConfig(**config) for name, config in data.items()}
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error loading config: {e}")
                return {}
        return {}
    
    def save_config(self):
        """Save bot configurations to file"""
        try:
            data = {name: asdict(config) for name, config in self.bots.items()}
            with open(self.config_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error saving config: {e}")
    
    def refresh_bot_table(self):
        """Refresh the bot table display"""
        self.bot_table.setRowCount(len(self.bots))
        
        for row, (name, config) in enumerate(self.bots.items()):
            # Name
            self.bot_table.setItem(row, 0, QTableWidgetItem(name))
            
            # Status with color coding
            status_item = QTableWidgetItem(config.status)
            if config.status == "running":
                status_item.setBackground(QColor(76, 175, 80, 100))  # Green
            else:
                status_item.setBackground(QColor(244, 67, 54, 100))   # Red
            self.bot_table.setItem(row, 1, status_item)
            
            # PID
            pid_text = str(config.pid) if config.pid else "-"
            self.bot_table.setItem(row, 2, QTableWidgetItem(pid_text))
            
            # Port
            self.bot_table.setItem(row, 3, QTableWidgetItem(str(config.port)))
            
            # Created
            created_date = config.created_at[:10] if config.created_at else "-"
            self.bot_table.setItem(row, 4, QTableWidgetItem(created_date))
            
            # Actions column - we'll just show the description for now
            self.bot_table.setItem(row, 5, QTableWidgetItem(config.description[:50] + "..." if len(config.description) > 50 else config.description))
    
    def update_bot_status(self, bot_name: str, status: str, pid: int):
        """Update bot status from monitoring thread"""
        if bot_name in self.bots:
            self.bots[bot_name].status = status
            self.bots[bot_name].pid = pid if pid > 0 else None
            self.save_config()
            # The table will be refreshed by the timer
    
    def get_selected_bot(self) -> Optional[str]:
        """Get the name of the currently selected bot"""
        current_row = self.bot_table.currentRow()
        if current_row >= 0:
            name_item = self.bot_table.item(current_row, 0)
            if name_item:
                return name_item.text()
        return None
    
    def create_new_bot(self):
        """Show bot creation dialog"""
        dialog = BotCreatorDialog(self, self.workspace_dir)
        if dialog.exec_() == QDialog.Accepted and dialog.bot_config:
            config = dialog.bot_config
            
            # Check if bot already exists
            if config.name in self.bots:
                QMessageBox.warning(self, "Warning", 
                                  f"Bot '{config.name}' already exists!")
                return
            
            try:
                # Create bot file from template
                self.create_bot_from_template(config.name, 
                                            dialog.template_combo.currentText())
                
                # Add to configuration
                self.bots[config.name] = config
                self.save_config()
                
                # Refresh display
                self.refresh_bot_table()
                
                self.status_bar.showMessage(f"Bot '{config.name}' created successfully")
                QMessageBox.information(self, "Success", 
                                      f"Bot '{config.name}' created successfully!")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", 
                                   f"Failed to create bot: {e}")
    
    def create_bot_from_template(self, bot_name: str, template: str):
        """Create bot file from template"""
        if template == "basic":
            self.create_basic_bot_template(bot_name)
        elif template == "research_assistant":
            self.create_research_assistant_template(bot_name)
        elif template == "minimal":
            self.create_minimal_bot_template(bot_name)
        elif template == "clean_enhanced":
            self.create_clean_enhanced_template(bot_name)
    
    def create_basic_bot_template(self, bot_name: str):
        """Create a basic bot template"""
        template_code = f'''#!/usr/bin/env python3
"""
Basic Discord Bot - {bot_name}
Generated by Bot Launcher GUI
"""

import discord
from discord.ext import commands
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
    
    def create_minimal_bot_template(self, bot_name: str):
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
    
    def create_research_assistant_template(self, bot_name: str):
        """Create a research assistant template"""
        template_code = f'''#!/usr/bin/env python3
"""
Research Assistant Discord Bot - {bot_name}
Generated by Bot Launcher GUI
"""

import discord
from discord.ext import commands
import sqlite3
import logging
from datetime import datetime

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
    
    def create_clean_enhanced_template(self, bot_name: str):
        """Create a clean enhanced template"""
        template_code = f'''#!/usr/bin/env python3
"""
Clean Enhanced Discord Bot - {bot_name}
Generated by Bot Launcher GUI
"""

import discord
from discord.ext import commands
import logging
import json
from pathlib import Path
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        
        super().__init__(
            command_prefix='!',
            intents=intents,
            help_command=None
        )
        
        self.config_file = Path('config.json')
        self.config = self.load_config()

    def load_config(self):
        """Load bot configuration"""
        if self.config_file.exists():
            with open(self.config_file) as f:
                return json.load(f)
        return {{
            "name": "{bot_name}",
            "version": "1.0.0",
            "description": "Enhanced Discord bot with modular features"
        }}

    async def on_ready(self):
        logger.info(f'{{self.user}} ({{self.config["name"]}}) is ready!')
        await self.change_presence(
            activity=discord.Game(name=f"🚀 {{self.config['name']}} v{{self.config['version']}} | !help")
        )

# Create bot instance
bot = EnhancedBot()

# Enhanced commands
@bot.command(name='status')
async def status(ctx):
    """Show bot status"""
    embed = discord.Embed(
        title=f"{{bot.config['name']}} Status",
        description=bot.config['description'],
        color=0x00ff00,
        timestamp=datetime.now()
    )
    embed.add_field(name="Version", value=bot.config['version'], inline=True)
    embed.add_field(name="Guilds", value=len(bot.guilds), inline=True)
    embed.add_field(name="Users", value=len(bot.users), inline=True)
    await ctx.send(embed=embed)

@bot.command(name='ping')
async def ping(ctx):
    """Check bot latency"""
    latency = round(bot.latency * 1000)
    await ctx.send(f"🏓 Pong! Latency: {{latency}}ms")

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
            QTimer.singleShot(2000, lambda: self.start_bot(bot_name))
    
    def delete_selected_bot(self):
        """Delete the selected bot"""
        bot_name = self.get_selected_bot()
        if bot_name:
            reply = QMessageBox.question(
                self, 'Confirm Delete',
                f"Are you sure you want to delete '{bot_name}'?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.delete_bot(bot_name)
    
    def start_bot(self, bot_name: str):
        """Start a specific bot"""
        if bot_name not in self.bots:
            QMessageBox.warning(self, "Warning", f"Bot '{bot_name}' not found!")
            return
        
        config = self.bots[bot_name]
        bot_file = self.workspace_dir / config.main_file
        
        if not bot_file.exists():
            QMessageBox.warning(self, "Warning", 
                              f"Bot file '{config.main_file}' not found!")
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
            self.refresh_bot_table()
            
            self.status_bar.showMessage(f"Started bot '{bot_name}'")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", 
                               f"Failed to start bot '{bot_name}': {e}")
    
    def stop_bot(self, bot_name: str):
        """Stop a specific bot"""
        if bot_name not in self.bots:
            QMessageBox.warning(self, "Warning", f"Bot '{bot_name}' not found!")
            return
        
        config = self.bots[bot_name]
        
        if not config.pid:
            QMessageBox.information(self, "Information", 
                                  f"Bot '{bot_name}' is not running!")
            return
        
        try:
            # Terminate process
            os.kill(config.pid, 15)  # SIGTERM
            
            config.pid = None
            config.status = "stopped"
            config.last_modified = datetime.now().isoformat()
            
            self.save_config()
            self.refresh_bot_table()
            
            self.status_bar.showMessage(f"Stopped bot '{bot_name}'")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", 
                               f"Failed to stop bot '{bot_name}': {e}")
    
    def delete_bot(self, bot_name: str):
        """Delete a bot"""
        if bot_name not in self.bots:
            QMessageBox.warning(self, "Warning", f"Bot '{bot_name}' not found!")
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
        self.refresh_bot_table()
        
        self.status_bar.showMessage(f"Deleted bot '{bot_name}'")
    
    def start_all_bots(self):
        """Start all stopped bots"""
        for bot_name, config in self.bots.items():
            if config.status != "running":
                self.start_bot(bot_name)
    
    def stop_all_bots(self):
        """Stop all running bots"""
        for bot_name, config in self.bots.items():
            if config.status == "running":
                self.stop_bot(bot_name)
    
    def view_bot_logs(self):
        """View bot logs"""
        dialog = LogViewerDialog(self, self.log_file)
        dialog.exec_()
    
    def open_discord_cli_terminal(self):
        """Open terminal with Discord CLI and development tools"""
        try:
            # Check for various Discord CLI tools
            discord_cli_found = False
            cli_command = None
            
            # Check for common Discord CLI tools
            cli_tools = [
                ('discord-cli', 'Discord official CLI'),
                ('djs', 'Discord.js CLI'),
                ('discord-py', 'Discord.py CLI'),
                ('npm list -g @discord/cli', 'Discord CLI via npm')
            ]
            
            for cli_name, description in cli_tools:
                check_cli = subprocess.run(['which', cli_name.split()[0]], capture_output=True, text=True)
                if check_cli.returncode == 0:
                    discord_cli_found = True
                    cli_command = cli_name
                    break
            
            # Create a comprehensive terminal session script
            welcome_message = '''echo "=== 🚀 Discord Bot Development Terminal ==="
echo "Current Directory: $(pwd)"
echo "Python: $(python3 --version 2>/dev/null || echo 'Not available')"
echo "Node.js: $(node --version 2>/dev/null || echo 'Not available')"
echo ""
echo "📋 Available Commands:"
echo "  • Python Discord.py: python3 -m discord --help (if installed)"
echo "  • Discord.py docs: python3 -c 'import discord; help(discord)'"
echo "  • Bot status: ps aux | grep python | grep -v grep"
echo "  • Environment variables: env | grep DISCORD"
echo ""
if command -v discord-cli &> /dev/null; then
    echo "  • Discord CLI: discord-cli --help"
    discord-cli --version 2>/dev/null || echo "    (Available but may need setup)"
fi
if command -v djs &> /dev/null; then
    echo "  • Discord.js CLI: djs --help"
fi
if command -v npm &> /dev/null; then
    echo "  • NPM packages: npm list discord"
fi
echo ""
echo "💡 Quick Setup:"
echo "  • Install Discord.py: pip3 install discord.py"
echo "  • Install Discord CLI: npm install -g @discord/cli"
echo "  • Set token: export DISCORD_TOKEN='your_token_here'"
echo ""
echo "🌐 Useful URLs (use 'firefox URL' or 'google-chrome URL'):"
echo "  • Developer Portal: https://discord.com/developers/applications"
echo "  • Discord.py Docs: https://discordpy.readthedocs.io/"
echo "  • Discord.js Docs: https://discord.js.org/"
echo ""
'''
            
            if discord_cli_found:
                welcome_message += f'''echo "✅ Found Discord CLI: {cli_command}"
{cli_command.split()[0]} --help 2>/dev/null || echo "Run '{cli_command}' for help"
echo ""
'''
            else:
                welcome_message += '''echo "⚠️  No Discord CLI found. Install options:"
echo "  • npm install -g @discord/cli"
echo "  • pip install discord-cli"
echo ""
'''
            
            # Get the default terminal emulator
            terminal_commands = [
                ['gnome-terminal', '--title=Discord Development Terminal', '--', 'bash', '-c', f'{welcome_message}bash'],
                ['xterm', '-title', 'Discord Development Terminal', '-e', f'bash -c "{welcome_message}bash"'],
                ['konsole', '--title', 'Discord Development Terminal', '-e', f'bash -c "{welcome_message}bash"'],
                ['x-terminal-emulator', '-T', 'Discord Development Terminal', '-e', f'bash -c "{welcome_message}bash"'],
                ['tilix', '--title=Discord Development Terminal', '-e', f'bash -c "{welcome_message}bash"'],
                ['terminator', '--title=Discord Development Terminal', '-e', f'bash -c "{welcome_message}bash"']
            ]
            
            # Try to open terminal
            terminal_opened = False
            for cmd in terminal_commands:
                try:
                    subprocess.Popen(cmd, cwd=self.workspace_dir)
                    terminal_opened = True
                    self.status_bar.showMessage("Discord CLI terminal opened")
                    break
                except (subprocess.CalledProcessError, FileNotFoundError):
                    continue
            
            if not terminal_opened:
                # Fallback: Create a comprehensive development session script
                script_content = f'''#!/bin/bash
{welcome_message}bash
'''
                
                script_path = self.workspace_dir / "discord_dev_terminal.sh"
                with open(script_path, 'w') as f:
                    f.write(script_content)
                
                script_path.chmod(0o755)
                
                try:
                    subprocess.Popen(['bash', str(script_path)], cwd=self.workspace_dir)
                    self.status_bar.showMessage("Discord development terminal opened")
                except Exception as e:
                    QMessageBox.critical(self, "Error", 
                                       f"Failed to open terminal: {e}\n\n"
                                       f"Try running manually:\nbash {script_path}")
                    
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open Discord development terminal: {e}")
    
    def open_discord_developer_portal(self):
        """Open Discord Developer Portal in browser"""
        try:
            webbrowser.open('https://discord.com/developers/applications')
            self.status_bar.showMessage("Discord Developer Portal opened in browser")
        except Exception as e:
            QMessageBox.critical(self, "Error", 
                               f"Failed to open Discord Developer Portal: {e}")
    
    def open_discordpy_docs(self):
        """Open Discord.py documentation"""
        try:
            webbrowser.open('https://discordpy.readthedocs.io/en/stable/')
            self.status_bar.showMessage("Discord.py documentation opened in browser")
        except Exception as e:
            QMessageBox.critical(self, "Error", 
                               f"Failed to open Discord.py documentation: {e}")
    
    def open_credentials_manager(self):
        """Open the credentials manager dialog"""
        try:
            dialog = CredentialsManagerDialog(self)
            dialog.exec_()
        except Exception as e:
            QMessageBox.critical(self, "Error", 
                               f"Failed to open credentials manager: {e}")
    
    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self,
            "About Discord Bot Launcher",
            """
            <h3>🚀 Discord Bot Launcher - Native GUI</h3>
            <p><b>Version:</b> 2.0.0</p>
            <p><b>Author:</b> Bot Launcher System</p>
            
            <p>A professional native GUI application for managing,
            organizing, and extending Discord bots with modern
            tools and automation features.</p>
            
            <p><b>Features:</b></p>
            <ul>
            <li>Native GUI interface using PyQt5</li>
            <li>Real-time bot status monitoring</li>
            <li>Template-based bot creation</li>
            <li>Configuration management</li>
            <li>Log viewer and system monitoring</li>
            <li>Dark/Light theme support</li>
            </ul>
            """
        )
    
    def closeEvent(self, event):
        """Handle application close event"""
        # Stop monitoring thread
        if hasattr(self, 'monitor_thread'):
            self.monitor_thread.stop()
        
        # Stop refresh timer
        if hasattr(self, 'refresh_timer'):
            self.refresh_timer.stop()
        
        event.accept()

def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Discord Bot Launcher")
    app.setApplicationVersion("2.0.0")
    app.setOrganizationName("Bot Launcher System")
    
    # Create and show main window
    window = DiscordBotLauncherGUI()
    window.show()
    
    # Run application
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()