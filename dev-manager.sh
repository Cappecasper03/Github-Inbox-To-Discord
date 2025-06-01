#!/bin/bash

# GitHub Inbox Discord Bot Development Manager
# Usage: ./dev-manager.sh [command] [options]

set -e

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
    echo "🔧 GitHub Inbox Discord Bot Development Manager"
    echo "==============================================="
    echo
    echo "Usage: ./$SCRIPT_NAME [command] [options]"
    echo
    echo "Commands:"
    echo "  start       Start bot in development mode (background)"
    echo "  stop        Stop the development bot"
    echo "  restart     Restart the development bot"
    echo "  status      Show bot status and process info"
    echo "  logs        Show bot logs"
    echo "  debug       Run bot in foreground with debug logging"
    echo "  test        Test configuration and dependencies"
    echo "  clean       Clean up log files and temporary data"
    echo
    echo "Options:"
    echo "  -f, --follow    Follow logs in real-time (for logs command)"
    echo "  -n, --lines N   Show last N lines of logs (default: 50)"
    echo "  -h, --help      Show this help message"
    echo
    echo "Examples:"
    echo "  ./$SCRIPT_NAME start"
    echo "  ./$SCRIPT_NAME logs --follow"
    echo "  ./$SCRIPT_NAME logs --lines 100"
    echo "  ./$SCRIPT_NAME debug"
    echo "  ./$SCRIPT_NAME test"
}

# Check if bot is running (development mode)
check_bot_running() {
    if [ -f "bot.pid" ]; then
        PID=$(cat bot.pid)
        if kill -0 $PID 2>/dev/null; then
            return 0
        else
            rm bot.pid
            return 1
        fi
    fi
    return 1
}

# Start bot in development mode
start_bot() {
    echo "🚀 Starting GitHub Inbox Discord Bot (Development Mode)..."

    # Check if virtual environment exists
    if [ ! -d "venv" ]; then
        print_error "Virtual environment not found!"
        print_info "Run ./install.sh first to set up the environment."
        exit 1
    fi

    # Check if configuration exists
    if [ ! -f ".env" ]; then
        print_error "Configuration file (.env) not found!"
        print_info "Run 'python setup.py' first to configure the bot."
        exit 1
    fi

    # Check if bot is already running
    if check_bot_running; then
        PID=$(cat bot.pid)
        print_warning "Bot is already running (PID: $PID)"
        print_info "Use './$SCRIPT_NAME stop' to stop it first."
        exit 1
    fi

    # Activate virtual environment and start bot
    source venv/bin/activate

    # Start bot in background
    nohup python bot.py > bot.log 2>&1 &
    echo $! > bot.pid

    print_success "Bot started successfully!"
    echo "   PID: $(cat bot.pid)"
    echo
    echo "📋 Quick Commands:"
    echo "   Status: ./$SCRIPT_NAME status"
    echo "   Logs:   ./$SCRIPT_NAME logs"
    echo "   Stop:   ./$SCRIPT_NAME stop"
}

# Stop bot
stop_bot() {
    echo "🛑 Stopping GitHub Inbox Discord Bot..."

    if ! check_bot_running; then
        print_error "Bot is not running (no PID file found)."
        exit 1
    fi

    PID=$(cat bot.pid)

    if kill $PID 2>/dev/null; then
        print_success "Bot stopped (PID: $PID)"
        rm bot.pid
    else
        print_error "Failed to stop bot process (PID: $PID)"
        rm bot.pid
        exit 1
    fi
}

# Restart bot
restart_bot() {
    echo "🔄 Restarting GitHub Inbox Discord Bot..."

    if check_bot_running; then
        stop_bot
        sleep 2
    fi
    
    start_bot
}

# Show bot status
show_status() {
    echo "📊 GitHub Inbox Discord Bot Development Status"
    echo "============================================="
    echo

    if check_bot_running; then
        PID=$(cat bot.pid)
        print_success "Bot is running (PID: $PID)"
        
        # Show process info
        echo
        echo "Process Information:"
        ps -p $PID -o pid,ppid,cmd,etime,cpu,mem 2>/dev/null || echo "Process details not available"
        
        # Show recent logs
        echo
        echo "Recent Log Output:"
        echo "------------------"
        if [ -f "bot.log" ]; then
            tail -10 bot.log
        else
            echo "No log file found."
        fi
    else
        print_error "Bot is not running"
    fi

    echo
    echo "📋 Quick Commands:"
    echo "   Start:   ./$SCRIPT_NAME start"
    echo "   Stop:    ./$SCRIPT_NAME stop"
    echo "   Restart: ./$SCRIPT_NAME restart"
    echo "   Logs:    ./$SCRIPT_NAME logs"
    echo "   Debug:   ./$SCRIPT_NAME debug"
}

# Show logs
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

    echo "📋 GitHub Inbox Discord Bot Development Logs"
    echo "==========================================="

    if [ ! -f "bot.log" ]; then
        print_error "Log file not found!"
        print_info "Bot may not have been started yet or logs were cleaned."
        exit 1
    fi

    if [ "$follow_logs" = true ]; then
        echo "Following logs (press Ctrl+C to exit):"
        echo "-------------------------------------"
        tail -f bot.log
    else
        echo "Last $lines lines:"
        echo "-----------------"
        tail -n "$lines" bot.log
    fi
}

# Run in debug mode
debug_bot() {
    echo "🐛 Running GitHub Inbox Discord Bot in Debug Mode..."
    echo "================================================="

    # Check if virtual environment exists
    if [ ! -d "venv" ]; then
        print_error "Virtual environment not found!"
        print_info "Run ./install.sh first to set up the environment."
        exit 1
    fi

    # Check if configuration exists
    if [ ! -f ".env" ]; then
        print_error "Configuration file (.env) not found!"
        print_info "Run 'python setup.py' first to configure the bot."
        exit 1
    fi

    # Check if bot is already running in background
    if check_bot_running; then
        PID=$(cat bot.pid)
        print_warning "Bot is already running in background (PID: $PID)"
        print_info "Stop it first with './$SCRIPT_NAME stop' or run both modes simultaneously."
        echo
    fi

    # Activate virtual environment
    source venv/bin/activate

    print_info "Starting bot in foreground with enhanced debug logging..."
    print_info "Press Ctrl+C to stop the bot."
    echo
    echo "Debug output will also be saved to 'bot_debug.log'"
    echo "=================================================="

    # Run debug version
    python dev.py
}

# Test configuration and dependencies
test_configuration() {
    echo "🔍 Testing GitHub Inbox Discord Bot Configuration"
    echo "==============================================="
    echo

    # Check if virtual environment exists
    if [ ! -d "venv" ]; then
        print_error "Virtual environment not found!"
        print_info "Run ./install.sh first to set up the environment."
        return 1
    fi

    # Activate virtual environment
    source venv/bin/activate

    # Test configuration
    print_info "Testing configuration..."
    if python test_config.py; then
        print_success "Configuration test passed!"
    else
        print_error "Configuration test failed!"
        return 1
    fi

    # Check dependencies
    print_info "Checking dependencies..."
    if pip check > /dev/null 2>&1; then
        print_success "All dependencies are satisfied!"
    else
        print_warning "Some dependency issues found:"
        pip check
    fi

    echo
    print_success "Development environment is ready!"
    echo
    echo "📋 Next Steps:"
    echo "   Start bot: ./$SCRIPT_NAME start"
    echo "   Debug mode: ./$SCRIPT_NAME debug" 
    echo "   View logs: ./$SCRIPT_NAME logs"

    return 0
}

# Clean up logs and temporary files
clean_environment() {
    echo "🧹 Cleaning up development environment..."

    local cleaned=false

    # Remove log files
    if [ -f "bot.log" ]; then
        rm bot.log
        echo "✓ Removed bot.log"
        cleaned=true
    fi

    if [ -f "bot_debug.log" ]; then
        rm bot_debug.log
        echo "✓ Removed bot_debug.log"
        cleaned=true
    fi

    # Remove stale PID files (if bot not running)
    if [ -f "bot.pid" ]; then
        if ! check_bot_running; then
            rm bot.pid
            echo "✓ Removed stale bot.pid"
            cleaned=true
        else
            print_warning "Bot is running, keeping bot.pid file"
        fi
    fi

    # Clean Python cache
    if [ -d "__pycache__" ]; then
        rm -rf __pycache__
        echo "✓ Removed Python cache"
        cleaned=true
    fi

    if [ -f "*.pyc" ]; then
        rm -f *.pyc
        echo "✓ Removed compiled Python files"
        cleaned=true
    fi

    if [ "$cleaned" = true ]; then
        print_success "Development environment cleaned!"
    else
        print_info "Development environment is already clean."
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
        start)
            start_bot
            ;;
        stop)
            stop_bot
            ;;
        restart)
            restart_bot
            ;;
        status)
            show_status
            ;;
        logs)
            shift
            show_logs "$@"
            ;;
        debug)
            debug_bot
            ;;
        test)
            test_configuration
            ;;
        clean)
            clean_environment
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
