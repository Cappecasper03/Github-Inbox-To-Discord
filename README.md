# GitHub Inbox Discord Bot

> **🤖 AI-Generated Project:** This entire Discord bot project was created by AI (GitHub Copilot) - including all code, documentation, scripts, and configuration files. No human coding was involved in the creation of this project.

A Discord bot that reads your personal GitHub notifications and sends them to a Discord channel with comprehensive management scripts for both development and production environments.

## ✨ Key Features

- ✅ **Real-time GitHub notifications** - Monitors your GitHub inbox
- ✅ **Rich Discord embeds** - Beautiful formatting with colors and thumbnails  
- ✅ **Multiple notification types** - Issues, PRs, releases, discussions, security advisories, etc.
- ✅ **Smart filtering** - Only shows new notifications since last check
- ✅ **Configurable intervals** - Set how often to check for updates
- ✅ **Discord commands** - Manual check and status commands (`!check`, `!status`)
- ✅ **Unified service management** - Single script for all systemd operations
- ✅ **Development mode** - Debug logging for troubleshooting
- ✅ **Production ready** - Systemd service with auto-restart
- ✅ **Easy management** - Comprehensive script suite

## 🔑 Required Credentials Setup

Before you can run the bot, you need to obtain several tokens and IDs. Here's how to get each one:

### 🤖 Discord Bot Token

1. **Go to Discord Developer Portal:**
   - Visit: https://discord.com/developers/applications
   - Log in with your Discord account

2. **Create a new application:**
   - Click "New Application"
   - Give it a name (e.g., "GitHub Inbox Bot")
   - Click "Create"

3. **Create a bot:**
   - Go to the "Bot" section in the left sidebar
   - Click "Add Bot" → "Yes, do it!"
   - Under "Token" section, click "Copy" to get your `DISCORD_BOT_TOKEN`

4. **Set bot permissions:**
   - In "Bot" section, enable these permissions:
     - ✅ Send Messages
     - ✅ Use Slash Commands
     - ✅ Embed Links
     - ✅ Read Message History

### 🔗 Discord Channel ID

1. **Enable Developer Mode in Discord:**
   - Open Discord → User Settings (gear icon)
   - Go to "Advanced" → Enable "Developer Mode"

2. **Get Channel ID:**
   - Right-click on the channel where you want notifications
   - Click "Copy Channel ID"
   - This is your `DISCORD_CHANNEL_ID`

### 🐙 GitHub Personal Access Token

1. **Go to GitHub Settings:**
   - Visit: https://github.com/settings/tokens
   - Log in to your GitHub account

2. **Create a new token:**
   - Click "Generate new token" → "Generate new token (classic)"
   - Give it a note (e.g., "Discord Bot Notifications")

3. **Select scopes:**
   - ✅ `notifications` - To read your notifications
   - ✅ `repo` - To get private repository notifications

4. **Generate and copy:**
   - Click "Generate token"
   - Copy the token immediately (you won't see it again!)
   - This is your `GITHUB_TOKEN`

### ⚙️ Additional Configuration

- **`CHECK_INTERVAL`**: How often to check for notifications (in seconds)
  - Default: `300` (5 minutes)
  - Minimum recommended: `60` (1 minute)
  - For testing: `30` (30 seconds)

## 🚀 Quick Start Guide

### Method 1: Automated Setup (Recommended)

1. **Run the installation script:**
   ```bash
   ./install.sh
   ```
   This automatically:
   - Installs Python 3 and pip3 if missing
   - Creates a virtual environment
   - Installs all dependencies
   - Runs the configuration setup
   - Tests the configuration

2. **Choose your deployment method:**

   **For Development/Testing:**
   ```bash
   ./dev-manager.sh start      # Start bot for development
   ./dev-manager.sh debug      # Run with debug logging  
   ./dev-manager.sh status     # Check development status
   ./dev-manager.sh logs       # View development logs
   ./dev-manager.sh --help     # Show all development commands
   ```

   **For Production (Recommended):**
   ```bash
   ./service-manager.sh install    # Install as systemd service
   ./service-manager.sh start      # Start the service
   ./service-manager.sh status     # Check service status
   ./service-manager.sh logs       # View service logs
   ```

### Method 2: Manual Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure the bot:**
   ```bash
   python setup.py     # Interactive setup
   python test_config.py   # Verify configuration
   ```

3. **Run the bot:**
   ```bash
   # For Development
   ./dev-manager.sh start       # Background execution
   ./dev-manager.sh debug       # Foreground with debug logging
   
   # For Production  
   ./service-manager.sh install # Install as service
   ./service-manager.sh start   # Start the service
   ```

## 🛠️ Comprehensive Script Reference

### 🚀 Setup & Configuration Scripts

#### `setup.py` - Interactive Configuration
Interactive setup script to configure the bot with necessary credentials.
```bash
python setup.py
```
Prompts for:
- Discord Bot Token
- GitHub Personal Access Token  
- Discord Channel ID
- Check Interval (optional)

#### `install.sh` - Complete Installation
Comprehensive installation script that handles everything automatically.
```bash
./install.sh
```
Features:
- Auto-detects and installs Python 3 if missing
- Creates virtual environment
- Installs all dependencies
- Runs configuration setup
- Tests configuration
- Works on Ubuntu/Debian, RHEL/CentOS, Fedora, and macOS

#### `test_config.py` - Configuration Validation
Tests the bot configuration to ensure everything is set up correctly.
```bash
python test_config.py
```
Validates:
- Environment variables
- GitHub API connection
- Discord token format
- Check interval format

### 🌟 Service Management (Production)

#### `service-manager.sh` - Unified Service Controller
**The main script for production deployments!** Handles all systemd service operations with a single command.

```bash
# Installation & Setup
./service-manager.sh install     # Install as systemd service
./service-manager.sh uninstall   # Remove the service completely

# Service Control
./service-manager.sh start       # Start the service
./service-manager.sh stop        # Stop the service  
./service-manager.sh restart     # Restart the service
./service-manager.sh status      # Show detailed service status

# Boot Management
./service-manager.sh enable      # Enable auto-start on boot
./service-manager.sh disable     # Disable auto-start on boot

# Log Management
./service-manager.sh logs                    # Show last 50 lines
./service-manager.sh logs --lines 100       # Show last 100 lines
./service-manager.sh logs --follow          # Follow logs in real-time

# Maintenance
./service-manager.sh reload      # Reload service configuration

# Help
./service-manager.sh --help      # Show complete command reference
```

**Features:**
- ✅ Color-coded output for success/error/warning messages
- ✅ Comprehensive error checking and validation
- ✅ Tests configuration before installing service
- ✅ Flexible log viewing with line count options
- ✅ Safety checks (prevents running as root, validates dependencies)
- ✅ Auto-restart on failure with 10-second delay
- ✅ Logs to systemd journal for centralized logging

### 🔧 Development & Testing Manager

#### `dev-manager.sh` - Development Environment Controller
**The main script for development and testing!** Handles all development operations with a single command.

```bash
# Development Control
./dev-manager.sh start       # Start bot in development mode (background)
./dev-manager.sh stop        # Stop the development bot
./dev-manager.sh restart     # Restart the development bot
./dev-manager.sh status      # Show bot status and process info

# Development Tools
./dev-manager.sh debug       # Run bot in foreground with debug logging
./dev-manager.sh test        # Test configuration and dependencies
./dev-manager.sh clean       # Clean up log files and temporary data

# Log Management
./dev-manager.sh logs                    # Show last 50 lines
./dev-manager.sh logs --lines 100       # Show last 100 lines
./dev-manager.sh logs --follow          # Follow logs in real-time

# Help
./dev-manager.sh --help      # Show complete command reference
```

**Features:**
- ✅ Color-coded output for success/error/warning messages
- ✅ Comprehensive error checking and validation
- ✅ Debug mode with enhanced logging
- ✅ Flexible log viewing with line count options
- ✅ Development environment testing and cleanup
- ✅ Background process management with PID tracking

### 🐛 Development & Debugging

#### `dev.py` - Development Mode
```bash
python dev.py
```
- Enhanced debug logging
- Console output with timestamps
- Logs to `bot_debug.log`
- Useful for troubleshooting

## 💡 Pro Tips

### For Developers
- Use **Development Manager** (`./dev-manager.sh`) for development and testing
- Run `./dev-manager.sh debug` for enhanced debugging with console output
- Test configuration changes with `./dev-manager.sh test`
- Monitor logs in real-time during development with `./dev-manager.sh logs --follow`

### For Production
- Use **Service Manager** (`./service-manager.sh`) for production deployments
- Enable auto-start: `./service-manager.sh enable`
- Set up log monitoring: `./service-manager.sh logs --follow`
- The service automatically restarts if it crashes (10-second delay)

### Performance Optimization
- Adjust `CHECK_INTERVAL` based on your notification volume
- Lower intervals = more real-time, higher API usage
- Higher intervals = less API usage, delayed notifications

## 📈 Example Workflows

### First-Time Setup
```bash
# Complete setup in one go
./install.sh                    # Handles everything automatically
./service-manager.sh install    # Set up as service
./service-manager.sh start      # Start running
./service-manager.sh logs       # Verify it's working
```

### Daily Development
```bash
# Start development session
./dev-manager.sh start          # Start bot in development mode
./dev-manager.sh logs --follow  # Monitor in terminal

# Make changes to bot.py
./dev-manager.sh restart        # Restart with changes
# OR
./dev-manager.sh stop           # Stop bot  
./dev-manager.sh start          # Start with changes
```

### Production Deployment
```bash
# Deploy to server
git clone <your-repo>
cd github-inbox-bot
./install.sh                    # Setup everything
./service-manager.sh install    # Install as service
./service-manager.sh enable     # Auto-start on boot
./service-manager.sh start      # Start immediately

# Ongoing maintenance
./service-manager.sh status     # Check health
./service-manager.sh logs       # Check logs
./service-manager.sh restart    # Apply updates
```

### Updating the Bot
```bash
# Service mode (Production)
./service-manager.sh stop       # Stop service
git pull                        # Get updates
pip install -r requirements.txt # Update dependencies  
./service-manager.sh start      # Restart service

# Development mode
./dev-manager.sh stop           # Stop bot
git pull                        # Get updates
pip install -r requirements.txt # Update dependencies
./dev-manager.sh start          # Restart bot
```

## 🤝 Getting Help

### Self-Help Resources
1. **Configuration Issues:**
   ```bash
   python test_config.py       # Validate setup
   ```

2. **Runtime Issues:**
   ```bash
   ./service-manager.sh status  # Check service health (production)
   ./dev-manager.sh status      # Check development status  
   ./service-manager.sh logs    # View recent logs (production)
   ./dev-manager.sh logs        # View recent logs (development)
   ```

3. **Script Help:**
   ```bash
   ./service-manager.sh --help  # Complete service command reference
   ./dev-manager.sh --help      # Complete development command reference
   ```

### Common Solutions
- **"Service not found"** → Run `./service-manager.sh install`
- **"Configuration invalid"** → Run `python setup.py` again
- **"Permission denied"** → Don't run as root, use regular user
- **"Bot not responding"** → Check Discord permissions and token

### Debug Information
When seeking help, include:
```bash
# System information
uname -a
python3 --version

# Configuration test
python test_config.py

# Service status  
./service-manager.sh status

# Recent logs
./service-manager.sh logs --lines 20
```

## 🎉 Success! 

You now have a fully functional GitHub notifications bot with:

✅ **Complete automation** - Set it and forget it  
✅ **Professional deployment** - Production-ready systemd service  
✅ **Developer-friendly** - Easy testing and debugging tools  
✅ **Comprehensive management** - Unified script for all operations  
✅ **Rich notifications** - Beautiful Discord embeds with full GitHub context  
✅ **Reliable operation** - Auto-restart on failures, centralized logging  

## 📚 Additional Resources

- **Discord.py Docs:** https://discordpy.readthedocs.io/
- **GitHub API Docs:** https://docs.github.com/en/rest/activity/notifications
- **Systemd Service Guide:** `man systemd.service`

---

**🚀 Happy coding!** Your GitHub notifications will now appear beautifully formatted in your Discord channel with professional-grade reliability and management tools.

**Created by AI** *(GitHub Copilot)* - A complete, production-ready solution with zero human coding required!
