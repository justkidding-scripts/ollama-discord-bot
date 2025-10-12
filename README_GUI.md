# 🚀 Advanced Discord Bot Launcher - GUI Version

A modern, comprehensive graphical user interface for managing, organizing, and extending Discord bots with powerful automation and monitoring features.

![Bot Launcher](https://img.shields.io/badge/Bot%20Launcher-GUI%20v2.0-blue)
![Python](https://img.shields.io/badge/Python-3.8+-green)
![Platform](https://img.shields.io/badge/Platform-Linux%20%7C%20Windows%20%7C%20macOS-lightgrey)
![License](https://img.shields.io/badge/License-MIT-yellow)

## ✨ Features

### 🎨 Modern GUI Interface
- **Clean, intuitive design** with dark/light theme support
- **Tabbed interface** for organized functionality
- **Real-time status monitoring** with visual indicators
- **Responsive layout** that adapts to different screen sizes
- **Keyboard shortcuts** for power users

### 🤖 Bot Management
- **Visual bot lifecycle management** (start/stop/restart)
- **Template-based bot creation** with preview
- **Real-time process monitoring** with PID tracking
- **Bot configuration editor** with validation
- **Bulk operations** (start all, stop all)
- **Import/export** bot configurations

### 🛠️ Development Tools
- **Code templates** for different bot types:
  - Basic Discord bot with essential commands
  - Research assistant with SQLite integration
  - Minimal ping/pong bot
  - Enhanced modular architecture
- **Live code preview** in template creator
- **Syntax highlighting** and validation
- **Integrated logs viewer** with filtering

### 📊 Monitoring & Analytics
- **Real-time status dashboard** with visual indicators
- **Process monitoring** and resource usage
- **Error tracking** and log analysis
- **Performance metrics** and statistics
- **Health checks** and automated alerts

### 🧩 Module System
- **Plugin architecture** for extensibility
- **Module marketplace** integration
- **Dependency management** and version control
- **Auto-updates** for installed modules
- **Custom module creation** tools

### 🔗 GitHub Integration
- **Repository cloning** and synchronization
- **Branch management** and switching
- **Automated deployment** workflows
- **Version control** integration
- **Collaborative development** features

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- tkinter (usually included with Python)
- Virtual environment support
- Git (for GitHub integration)

### Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd ollama-discord-bot
   ```

2. **Launch the GUI:**
   ```bash
   ./launch_ultimate.sh gui
   ```

3. **Or use the setup command first:**
   ```bash
   ./launch_ultimate.sh setup
   ./launch_ultimate.sh gui
   ```

### Alternative Launch Methods

```bash
# Launch GUI mode (default)
./launch_ultimate.sh
./launch_ultimate.sh gui

# Launch CLI mode
./launch_ultimate.sh cli

# Setup environment only
./launch_ultimate.sh setup

# Show help
./launch_ultimate.sh help
```

## 🎮 Usage Guide

### Creating Your First Bot

1. **Open the Bot Creator tab**
2. **Fill in bot details:**
   - Bot name (required)
   - Description (optional)
   - Select template (basic, research_assistant, minimal, clean_enhanced)
   - Set port number
3. **Preview the template** in the preview pane
4. **Click "Create Bot"** to generate the bot files
5. **Switch to Dashboard** to see your new bot

### Managing Bots

#### Dashboard Operations
- **View all bots** in the main dashboard table
- **Select a bot** and use control buttons:
  - ▶️ Start - Launch the bot process
  - ⏹️ Stop - Terminate the bot process
  - 🔄 Restart - Stop and start the bot
  - ⚙️ Configure - Edit bot settings
  - 📊 Logs - View bot logs
  - 🗑️ Delete - Remove the bot

#### Context Menu
- **Right-click any bot** for quick actions
- **Keyboard shortcuts** for common operations

### Module Management

1. **Open the Modules tab**
2. **Install new modules** from the marketplace
3. **Update existing modules** with one click
4. **Manage dependencies** automatically
5. **Create custom modules** using the builder

### Settings & Configuration

#### General Settings
- **Theme selection** (Dark/Light mode)
- **Auto-start options** for bots
- **Monitoring intervals** and alerts
- **Workspace directory** management

#### Advanced Configuration
- **Custom templates** and snippets
- **Environment variables** management
- **Network and security** settings
- **Backup and restore** options

## 🎨 GUI Components

### Main Window
- **Menu bar** with File, Bots, Tools, View, Help menus
- **Tabbed interface** with Dashboard, Creator, Modules, Settings
- **Status bar** with current operation and progress
- **Toolbar** with quick action buttons

### Bot Dashboard
- **Table view** with sortable columns
- **Status indicators** (🟢 running, 🔴 stopped)
- **Process information** (PID, port, modules)
- **Action buttons** for bot control
- **Search and filter** functionality

### Bot Creator
- **Form interface** with validation
- **Template selection** dropdown
- **Live preview** of selected template
- **Code syntax** highlighting
- **Creation wizard** for advanced setups

### Module Manager
- **Available modules** browser
- **Installed modules** list
- **Update notifications** and management
- **Module details** and documentation
- **Custom module** creation tools

### Settings Panel
- **Tabbed settings** for different categories
- **Form validation** and error handling
- **Import/export** configuration
- **Reset to defaults** option
- **Live preview** of changes

## ⌨️ Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+N` | Create new bot |
| `Ctrl+I` | Import bot |
| `Ctrl+S` | Save configuration |
| `Ctrl+Q` | Quit application |
| `F11` | Toggle fullscreen |
| `F5` | Refresh bot status |
| `Ctrl+T` | New tab |
| `Ctrl+W` | Close tab |

## 🔧 Configuration

### Environment Variables

```bash
# Discord bot token for testing
export DISCORD_TOKEN="your_bot_token_here"

# GUI display (for remote connections)
export DISPLAY=:0

# Custom workspace directory
export BOT_WORKSPACE="/path/to/your/workspace"

# Enable debug mode
export DEBUG=1
```

### Configuration Files

- `launcher_config.json` - Bot configurations
- `launcher_settings.json` - Application settings
- `launcher.db` - SQLite database for tracking
- `launcher.log` - Application logs

## 🐛 Troubleshooting

### Common Issues

#### GUI Won't Start
```bash
# Check if tkinter is installed
python3 -c "import tkinter"

# Install tkinter on Ubuntu/Debian
sudo apt-get install python3-tk

# Install tkinter on CentOS/RHEL
sudo yum install tkinter
```

#### Display Issues on Remote Systems
```bash
# Enable X11 forwarding
ssh -X username@hostname

# Or use VNC/RDP for full desktop
```

#### Bot Creation Fails
- Check workspace permissions
- Verify Python path and version
- Check available disk space
- Review error logs in the GUI

### Debug Mode

Enable debug mode for detailed logging:

```bash
DEBUG=1 ./launch_ultimate.sh gui
```

## 🤝 Contributing

### Development Setup

```bash
# Clone the repository
git clone <repository-url>
cd ollama-discord-bot

# Create development environment
python3 -m venv dev-env
source dev-env/bin/activate

# Install development dependencies
pip install -r requirements-dev.txt
```

### Code Style

- Follow PEP 8 guidelines
- Use type hints where appropriate
- Document all public methods
- Write unit tests for new features
- Use meaningful commit messages

### Pull Request Process

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Update documentation
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Discord.py** community for the excellent library
- **Tkinter** developers for the GUI framework
- **Python** community for the amazing ecosystem
- **Contributors** who help improve this project

## 📞 Support

- **GitHub Issues**: Report bugs and request features
- **Discussions**: Ask questions and share ideas
- **Wiki**: Find detailed documentation and tutorials
- **Discord**: Join our community server

---

**Made with ❤️ for the Discord bot development community**
