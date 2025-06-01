#!/bin/bash

# GitHub Inbox Discord Bot Service Manager
# Usage: ./service-manager.sh [command] [options]

set -e

SERVICE_NAME="github-inbox-bot"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
SCRIPT_NAME=$(basename "$0")

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored output
print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
print_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }

# Show usage information
show_usage() {
    echo "🤖 GitHub Inbox Discord Bot Service Manager"
    echo "==========================================="
    echo
    echo "Usage: ./$SCRIPT_NAME [command] [options]"
    echo
    echo "Commands:"
    echo "  install     Install the bot as a systemd service"
    echo "  uninstall   Remove the systemd service"
    echo "  start       Start the service"
    echo "  stop        Stop the service"
    echo "  restart     Restart the service"
    echo "  status      Show service status"
    echo "  logs        Show service logs"
    echo "  enable      Enable service to start on boot"
    echo "  disable     Disable service from starting on boot"
    echo "  reload      Reload service configuration"
    echo
    echo "Options:"
    echo "  -f, --follow    Follow logs in real-time (for logs command)"
    echo "  -n, --lines N   Show last N lines of logs (default: 50)"
    echo "  -h, --help      Show this help message"
    echo
    echo "Examples:"
    echo "  ./$SCRIPT_NAME install"
    echo "  ./$SCRIPT_NAME start"
    echo "  ./$SCRIPT_NAME logs --follow"
    echo "  ./$SCRIPT_NAME logs --lines 100"
    echo "  ./$SCRIPT_NAME status"
}

# Check if service is installed
check_service_installed() {
    if ! systemctl list-unit-files | grep -q "$SERVICE_NAME"; then
        return 1
    fi
    return 0
}

# Check if running as root
check_not_root() {
    if [ "$EUID" -eq 0 ]; then
        print_error "This operation should not be run as root!"
        print_info "Please run as the user who will run the bot."
        exit 1
    fi
}

# Install service
install_service() {
    echo "🔧 Installing GitHub Inbox Discord Bot Service"
    echo "=============================================="
    echo

    check_not_root

    # Get current user and directory
    USER=$(whoami)
    CURRENT_DIR=$(pwd)

    echo "📋 Installation Details:"
    echo "   User: $USER"
    echo "   Directory: $CURRENT_DIR"
    echo "   Service: $SERVICE_NAME"
    echo

    # Check if service is already installed
    if check_service_installed; then
        print_warning "Service is already installed!"
        echo "   Use './$SCRIPT_NAME uninstall' to remove it first."
        exit 1
    fi

    # Check if virtual environment exists
    if [ ! -d "venv" ]; then
        print_error "Virtual environment not found!"
        print_info "Please run ./install.sh first to set up the environment."
        exit 1
    fi

    # Check if configuration exists
    if [ ! -f ".env" ]; then
        print_error "Configuration file (.env) not found!"
        print_info "Please run 'python setup.py' first to configure the bot."
        exit 1
    fi

    # Test configuration
    echo "🔍 Testing configuration..."
    if ! python test_config.py; then
        print_error "Configuration test failed!"
        print_info "Please fix configuration issues before installing service."
        exit 1
    fi

    print_success "Configuration test passed!"
    echo

    # Create systemd service file
    echo "📄 Creating systemd service file..."

    cat > "${SERVICE_NAME}.service" << EOF
[Unit]
Description=GitHub Inbox Discord Bot
After=network.target

[Service]
Type=simple
User=${USER}
WorkingDirectory=${CURRENT_DIR}
Environment=PATH=${CURRENT_DIR}/venv/bin
ExecStart=${CURRENT_DIR}/venv/bin/python bot.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

    # Copy service file to systemd directory (requires sudo)
    echo "🔐 Installing service file (requires sudo)..."
    sudo cp "${SERVICE_NAME}.service" "$SERVICE_FILE"
    sudo chmod 644 "$SERVICE_FILE"

    # Reload systemd and enable service
    echo "🔄 Reloading systemd and enabling service..."
    sudo systemctl daemon-reload
    sudo systemctl enable "$SERVICE_NAME"

    echo
    print_success "Service installed and enabled successfully!"
    echo
    echo "📋 Next Steps:"
    echo "   Start service: ./$SCRIPT_NAME start"
    echo "   Check status:  ./$SCRIPT_NAME status"
    echo "   View logs:     ./$SCRIPT_NAME logs"
}

# Uninstall service
uninstall_service() {
    echo "🗑️  Uninstalling GitHub Inbox Discord Bot Service"
    echo "==============================================="
    echo

    # Check if service file exists
    if [ ! -f "$SERVICE_FILE" ]; then
        print_error "Service not found: $SERVICE_FILE"
        print_info "The service may not be installed."
        exit 1
    fi

    # Stop and disable service
    echo "🛑 Stopping and disabling service..."
    sudo systemctl stop "$SERVICE_NAME" 2>/dev/null || echo "   Service was not running"
    sudo systemctl disable "$SERVICE_NAME"

    # Remove service file
    echo "🗑️  Removing service file..."
    sudo rm "$SERVICE_FILE"

    # Reload systemd
    echo "🔄 Reloading systemd..."
    sudo systemctl daemon-reload
    sudo systemctl reset-failed

    echo
    print_success "Service uninstalled successfully!"
    echo
    print_info "The bot files remain in the current directory."
    print_info "You can still run the bot manually with ./start.sh"
}

# Start service
start_service() {
    echo "🚀 Starting GitHub Inbox Discord Bot Service..."

    if ! check_service_installed; then
        print_error "Service not installed!"
        print_info "Run './$SCRIPT_NAME install' to install the service first."
        exit 1
    fi

    if sudo systemctl start "$SERVICE_NAME"; then
        print_success "Service started successfully!"
        echo
        echo "📋 Quick Commands:"
        echo "   Status: ./$SCRIPT_NAME status"
        echo "   Logs:   ./$SCRIPT_NAME logs"
        echo "   Stop:   ./$SCRIPT_NAME stop"
    else
        print_error "Failed to start service!"
        print_info "Check logs: ./$SCRIPT_NAME logs"
        exit 1
    fi
}

# Stop service
stop_service() {
    echo "🛑 Stopping GitHub Inbox Discord Bot Service..."

    if ! check_service_installed; then
        print_error "Service not installed!"
        exit 1
    fi

    if sudo systemctl stop "$SERVICE_NAME"; then
        print_success "Service stopped successfully!"
        echo
        echo "📋 Quick Commands:"
        echo "   Status: ./$SCRIPT_NAME status"
        echo "   Start:  ./$SCRIPT_NAME start"
    else
        print_error "Failed to stop service!"
        print_info "Check status: ./$SCRIPT_NAME status"
        exit 1
    fi
}

# Restart service
restart_service() {
    echo "🔄 Restarting GitHub Inbox Discord Bot Service..."

    if ! check_service_installed; then
        print_error "Service not installed!"
        print_info "Run './$SCRIPT_NAME install' to install the service first."
        exit 1
    fi

    if sudo systemctl restart "$SERVICE_NAME"; then
        print_success "Service restarted successfully!"
        echo
        echo "📋 Quick Commands:"
        echo "   Status: ./$SCRIPT_NAME status"
        echo "   Logs:   ./$SCRIPT_NAME logs"
    else
        print_error "Failed to restart service!"
        print_info "Check logs: ./$SCRIPT_NAME logs"
        exit 1
    fi
}

# Show service status
show_status() {
    echo "📊 GitHub Inbox Discord Bot Service Status"
    echo "========================================="
    echo

    if ! check_service_installed; then
        print_error "Service not installed!"
        print_info "Run './$SCRIPT_NAME install' to install the service first."
        exit 1
    fi

    # Show systemctl status
    sudo systemctl status "$SERVICE_NAME" --no-pager -l

    echo
    echo "📋 Quick Commands:"
    echo "   Start:   ./$SCRIPT_NAME start"
    echo "   Stop:    ./$SCRIPT_NAME stop"
    echo "   Restart: ./$SCRIPT_NAME restart"
    echo "   Logs:    ./$SCRIPT_NAME logs"
}

# Show service logs
show_logs() {
    local follow_logs=false
    local lines=50

    # Parse options
    while [[ $# -gt 0 ]]; do
        case $1 in
            -f|--follow)
                follow_logs=true
                shift
                ;;
            -n|--lines)
                lines="$2"
                shift 2
                ;;
            *)
                print_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done

    echo "📋 GitHub Inbox Discord Bot Service Logs"
    echo "======================================="

    if ! check_service_installed; then
        print_error "Service not installed!"
        print_info "Run './$SCRIPT_NAME install' to install the service first."
        exit 1
    fi

    if [ "$follow_logs" = true ]; then
        echo "Following logs (press Ctrl+C to exit):"
        echo "-------------------------------------"
        sudo journalctl -u "$SERVICE_NAME" -f
    else
        echo "Last $lines lines:"
        echo "-----------------"
        sudo journalctl -u "$SERVICE_NAME" -n "$lines" --no-pager
    fi
}

# Enable service
enable_service() {
    echo "🔄 Enabling GitHub Inbox Discord Bot Service..."

    if ! check_service_installed; then
        print_error "Service not installed!"
        print_info "Run './$SCRIPT_NAME install' to install the service first."
        exit 1
    fi

    if sudo systemctl enable "$SERVICE_NAME"; then
        print_success "Service enabled successfully!"
        print_info "Service will now start automatically on boot."
    else
        print_error "Failed to enable service!"
        exit 1
    fi
}

# Disable service
disable_service() {
    echo "🛑 Disabling GitHub Inbox Discord Bot Service..."

    if ! check_service_installed; then
        print_error "Service not installed!"
        exit 1
    fi

    if sudo systemctl disable "$SERVICE_NAME"; then
        print_success "Service disabled successfully!"
        print_info "Service will no longer start automatically on boot."
    else
        print_error "Failed to disable service!"
        exit 1
    fi
}

# Reload service configuration
reload_service() {
    echo "🔄 Reloading systemd configuration..."

    sudo systemctl daemon-reload

    if check_service_installed; then
        print_success "Systemd configuration reloaded!"
        print_info "If you modified the service file, restart the service to apply changes:"
        print_info "./$SCRIPT_NAME restart"
    else
        print_success "Systemd configuration reloaded!"
    fi
}

# Main script logic
main() {
    # Check if no arguments provided
    if [ $# -eq 0 ]; then
        show_usage
        exit 1
    fi

    # Parse command
    case $1 in
        install)
            install_service
            ;;
        uninstall)
            uninstall_service
            ;;
        start)
            start_service
            ;;
        stop)
            stop_service
            ;;
        restart)
            restart_service
            ;;
        status)
            show_status
            ;;
        logs)
            shift
            show_logs "$@"
            ;;
        enable)
            enable_service
            ;;
        disable)
            disable_service
            ;;
        reload)
            reload_service
            ;;
        -h|--help|help)
            show_usage
            ;;
        *)
            print_error "Unknown command: $1"
            echo
            show_usage
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"
