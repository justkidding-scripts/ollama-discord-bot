#!/bin/bash

# 🚀 Ultimate Research Bot Launch Script
# Modern Discord Bot Management System with GUI

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to print colored output
print_colored() {
    echo -e "${2}${1}${NC}"
}

# Function to print section headers
print_header() {
    echo -e "\n${CYAN}${1}${NC}"
}

# Function to check if GUI is available
check_gui() {
    if [ -z "$DISPLAY" ] && [ -z "$WAYLAND_DISPLAY" ]; then
        return 1
    fi
    return 0
}

# Function to check dependencies
check_dependencies() {
    print_header "ℹ️  Checking system dependencies..."
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_colored "❌ Python 3 is not installed!" $RED
        exit 1
    fi
    
    # Check tkinter for GUI
    if ! python3 -c "import tkinter" 2>/dev/null; then
        print_colored "⚠️  Tkinter not available, installing python3-tk..." $YELLOW
        sudo apt-get install -y python3-tk || true
    fi
    
    print_colored "✅ Dependencies verified!" $GREEN
}

# Function to setup virtual environment
setup_venv() {
    local venv_name="ultra-enhanced-env"
    
    if [ ! -d "$venv_name" ]; then
        print_header "⚙️  Creating virtual environment..."
        python3 -m venv "$venv_name"
    fi
    
    print_header "⚡ Activating virtual environment..."
    source "$venv_name/bin/activate"
    
    # Upgrade pip
    python -m pip install --upgrade pip > /dev/null 2>&1
    
    return 0
}

# Function to install dependencies
install_dependencies() {
    print_header "⬇️  Installing dependencies..."
    
    # Install requirements if file exists
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
    else
        # Install basic GUI dependencies
        pip install discord.py aiohttp aiofiles python-dotenv psutil requests
        pip install rich typer pyyaml orjson tenacity overrides click tqdm
    fi
}

# Function to launch GUI mode
launch_gui() {
    print_header "🎛️ Launching Native GUI Bot Management System..."
    
    # Check if GUI is available
    if ! check_gui; then
        print_colored "⚠️  No GUI environment detected! Use './launch_ultimate.sh cli' for terminal mode." $YELLOW
        return 1
    fi
    
    # Check PyQt5 availability
    if ! python3 -c "from PyQt5.QtWidgets import QApplication" 2>/dev/null; then
        print_colored "⚠️  PyQt5 not available, installing..." $YELLOW
        pip install PyQt5
    fi
    
    # Launch the native GUI application
    python bot_launcher.py
}

# Function to launch CLI mode
launch_cli() {
    print_header "🖥️  Launching CLI Bot Management System..."
    
    # Use the CLI version if available
    if [ -f "bot_launcher_cli.py" ]; then
        python bot_launcher_cli.py
    else
        print_colored "❌ CLI version not found!" $RED
        exit 1
    fi
}

# Main execution logic
main() {
    local command="${1:-gui}"
    
    case "$command" in
        "gui"|"launcher"|"")
            print_colored "🚀 Starting Ultimate Research Bot (GUI Mode)..." $PURPLE
            check_dependencies
            setup_venv
            install_dependencies
            launch_gui
            ;;
        "cli")
            print_colored "🚀 Starting Ultimate Research Bot (CLI Mode)..." $PURPLE
            check_dependencies
            setup_venv
            install_dependencies
            launch_cli
            ;;
        "setup")
            print_colored "⚙️  Setting up Ultimate Research Bot..." $PURPLE
            check_dependencies
            setup_venv
            install_dependencies
            print_colored "✅ Setup completed successfully!" $GREEN
            ;;
        "help"|"--help"|"-h")
            echo "🚀 Ultimate Discord Bot Launcher"
            echo ""
            echo "Usage: $0 [gui|cli|setup|help]"
            echo ""
            echo "Commands:"
            echo "  gui      Launch with graphical interface (default)"
            echo "  cli      Launch with command-line interface"
            echo "  setup    Setup environment only"
            echo "  help     Show this help message"
            ;;
        *)
            print_colored "❌ Unknown command: $command" $RED
            echo "Use '$0 help' for usage information."
            exit 1
            ;;
    esac
}

# Trap to handle interrupts
trap 'print_colored "\n⚠️  Operation interrupted by user" $YELLOW; exit 130' INT

# Run main function with all arguments
main "$@"
