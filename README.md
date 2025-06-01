# GitHub Inbox Discord Bot

> **🤖 AI-Generated Project:** This entire Discord bot project was created by AI (GitHub Copilot) - including all code, documentation, scripts, and configuration files. No human coding was involved in the creation of this project.

A Discord bot that reads your personal GitHub notifications and sends them to a Discord channel.

## 🎉 Project Complete!

You now have a fully functional Discord bot that monitors your GitHub notifications and sends them to a Discord channel.

## ✨ Key Features

- ✅ **Real-time GitHub notifications** - Monitors your GitHub inbox
- ✅ **Rich Discord embeds** - Beautiful formatting with colors and thumbnails  
- ✅ **Multiple notification types** - Issues, PRs, releases, discussions, security advisories, etc.
- ✅ **Smart filtering** - Only shows new notifications since last check
- ✅ **Configurable intervals** - Set how often to check for updates
- ✅ **Discord commands** - Manual check and status commands (`!check`, `!status`)
- ✅ **Background service** - Can run as systemd service
- ✅ **Development mode** - Debug logging for troubleshooting
- ✅ **Easy management** - Simple start/stop/status scripts

## 📁 Project Structure

```
github-inbox-bot/
├── bot.py                     # Main bot application
├── requirements.txt           # Python dependencies
├── .env.example              # Environment template
├── .gitignore                # Git ignore rules
├── README.md                 # Comprehensive documentation
├── setup.py                  # Interactive configuration setup
├── test_config.py            # Configuration validation
├── dev.py                    # Development runner with debug logging
├── install.sh                # Complete installation script
├── start.sh                  # Start bot in background
├── stop.sh                   # Stop running bot
├── status.sh                 # Check bot status
├── logs.sh                   # View real-time logs
└── github-inbox-bot.service  # Systemd service file
```

## 🚀 Quick Start

1. **Run the installation script:**
   ```bash
   ./install.sh
   ```
   This will:
   - Automatically install Python 3 and pip3 if missing
   - Create a virtual environment
   - Install all dependencies
   - Run the configuration setup
   - Test the configuration

2. **Start the bot:**
   ```bash
   ./start.sh
   ```

3. **Check bot status:**
   ```bash
   ./status.sh
   ```

4. **View logs:**
   ```bash
   ./logs.sh
   ```

5. **Stop the bot:**
   ```bash
   ./stop.sh
   ```

## 🔧 Configuration Required

Before running, you'll need:

1. **Discord Bot Token** - Create at https://discord.com/developers/applications
2. **GitHub Personal Access Token** - Create at https://github.com/settings/tokens
   - Required scopes: `notifications`, `repo`
3. **Discord Channel ID** - Enable Developer Mode and copy channel ID
4. **Bot permissions** - Invite bot to server with "Send Messages" permission

## ⚙️ Manual Setup (Alternative to Quick Start)

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Create a `.env` file with your credentials:**
   ```env
   DISCORD_BOT_TOKEN=your_discord_bot_token_here
   GITHUB_TOKEN=your_github_personal_access_token_here
   DISCORD_CHANNEL_ID=your_discord_channel_id_here
   CHECK_INTERVAL=300
   ```

3. **GitHub Personal Access Token:**
   - Go to GitHub Settings → Developer settings → Personal access tokens
   - Create a new token with `notifications` and `repo` scopes

4. **Discord Bot Setup:**
   - Go to Discord Developer Portal
   - Create a new application and bot
   - Copy the bot token
   - Invite the bot to your server with "Send Messages" permissions

5. **Get Discord Channel ID:**
   - Enable Developer Mode in Discord
   - Right-click on the channel and copy ID

6. **Run the bot:**
   ```bash
   python bot.py
   ```

## 📋 Configuration

- `CHECK_INTERVAL`: How often to check for notifications (in seconds, default: 300 = 5 minutes)
- The bot will only send new notifications since the last check
- Notifications are automatically marked as read after being sent to Discord

## 🛠️ Available Scripts

- `install.sh` - Complete installation and setup (installs Python/pip if needed)
- `start.sh` - Start the bot in the background
- `stop.sh` - Stop the running bot
- `status.sh` - Check if the bot is running and show status
- `logs.sh` - View bot logs in real-time
- `setup.py` - Interactive configuration setup
- `test_config.py` - Test the current configuration
- `dev.py` - Run bot in development mode with debug logging

## 🚀 Running as a Service

To run the bot as a systemd service:

```bash
sudo cp github-inbox-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable github-inbox-bot
sudo systemctl start github-inbox-bot
```

Check service status:
```bash
sudo systemctl status github-inbox-bot
```

View service logs:
```bash
sudo journalctl -u github-inbox-bot -f
```

## 🔧 Development

Run in development mode with debug logging:
```bash
python dev.py
```

This enables detailed logging to both console and `bot_debug.log` file.

## 🆘 Troubleshooting

1. **Bot not responding**: Check if it's running with `./status.sh`
2. **Configuration errors**: Run `python test_config.py` to verify setup
3. **Permission issues**: Ensure bot has "Send Messages" permission in Discord
4. **GitHub API errors**: Verify your GitHub token has correct scopes
5. **Channel not found**: Verify the Discord channel ID is correct

## 🎮 Bot Commands

Use these commands in the configured Discord channel:

- `!check` - Manually check for new GitHub notifications
- `!status` - Show bot status and configuration information

## 📝 Next Steps

1. Run `./install.sh` to set everything up
2. Follow the interactive configuration prompts  
3. Start the bot with `./start.sh`
4. Enjoy automated GitHub notifications in Discord!

## 🆘 Need Help?

- Run `python test_config.py` to verify configuration
- Check `./status.sh` to see if bot is running
- View logs with `./logs.sh`
- See troubleshooting section above for common issues

## 📋 Notification Types Supported

- Issues
- Pull Requests
- Releases
- Security Advisories
- Discussions
- And more GitHub notification types

---

**Happy coding! 🚀** Your GitHub notifications will now appear beautifully formatted in your Discord channel.
