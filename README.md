# GitHub Inbox Discord Bot

A Discord bot that monitors your GitHub notifications and sends them to a Discord channel. Perfect for staying updated on issues, pull requests, commits, and other GitHub activities without constantly checking your inbox.

## Quick Start

1. **Setup the project:**
   ```bash
   ./setup.sh
   ```

2. **Configure your tokens:**
   ```bash
   cp .env.example .env
   nano .env  # Add your Discord and GitHub tokens
   ```

3. **Validate and start:**
   ```bash
   ./validate-config.sh  # Check your configuration
   ./start-bot.sh        # Start the bot
   ```

That's it! Your bot should now be monitoring your GitHub notifications.

## Features

- 🔔 **Real-time GitHub notifications** - Monitors your GitHub inbox automatically
- 📨 **Rich Discord embeds** - Beautiful, informative messages with colors and formatting
- ⚙️ **Configurable checking interval** - Set how often to check for new notifications
- 🎯 **Filtered notifications** - Option to only show unread notifications
- 🔗 **Direct links** - Click to go straight to the GitHub issue, PR, or commit
- 🏷️ **Smart categorization** - Different colors and icons for different notification types
- 🛡️ **Error handling** - Robust error handling and logging

## Notification Types Supported

- 🐛 Issues
- 🔀 Pull Requests
- 📝 Commits
- 🚀 Releases
- And more!

## Setup Instructions

### 1. Prerequisites

- Node.js 18+ installed
- A GitHub account with notifications
- A Discord server where you have permission to add bots

### 2. Navigate to Project Directory

```bash
cd /home/cappo/github-inbox-bot
```

### 3. Install Dependencies

```bash
npm install
```

### 4. Create a Discord Bot

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application" and give it a name
3. Go to the "Bot" tab and click "Add Bot"
4. Copy the bot token (you'll need this for the `.env` file)
5. Under "Privileged Gateway Intents", enable:
   - Server Members Intent
   - Message Content Intent (if needed)

### 5. Invite Bot to Your Server

1. In the Discord Developer Portal, go to "OAuth2" > "URL Generator"
2. Select scopes: `bot`
3. Select bot permissions:
   - Send Messages
   - Use Slash Commands
   - Embed Links
   - Read Message History
4. Copy the generated URL and visit it to invite the bot to your server

### 6. Get Discord Channel ID

1. Enable Developer Mode in Discord (User Settings > Advanced > Developer Mode)
2. Right-click on the channel where you want notifications
3. Click "Copy ID"

### 7. Create GitHub Personal Access Token

1. Go to [GitHub Settings > Developer settings > Personal access tokens](https://github.com/settings/tokens)
2. Click "Generate new token (classic)"
3. Give it a name like "Discord Bot"
4. Select scopes:
   - `notifications` (required)
   - `repo` (if you want private repository notifications)
5. Copy the generated token

### 8. Configure Environment Variables

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` with your values:
   ```bash
   nano .env
   ```
   
   Add your tokens:
   ```env
   DISCORD_TOKEN=your_discord_bot_token_here
   GITHUB_TOKEN=your_github_personal_access_token_here
   DISCORD_CHANNEL_ID=your_discord_channel_id_here
   
   # Optional settings
   CHECK_INTERVAL_MINUTES=5
   ONLY_UNREAD=true
   ```

### 9. Build and Run

You have several options to build and run the bot:

#### Option 1: Quick Setup (Recommended for first-time setup)
```bash
# Run the setup script (installs Node.js if needed, installs dependencies, and builds)
./setup.sh
```

#### Option 2: Manual Setup
```bash
# Install dependencies
npm install

# Build the TypeScript code
npm run build

# Start the bot
npm start

# Or run in development mode with auto-reload
npm run dev
```

#### Option 3: Using Helper Scripts
```bash
# Validate your configuration
./validate-config.sh

# Start the bot with the startup script
./start-bot.sh
```

#### Option 4: Run as a System Service
```bash
# Install as a systemd service
./service-manager.sh install

# Start the service
./service-manager.sh start

# Check service status
./service-manager.sh status

# View live logs
./service-manager.sh logs
```

## Configuration Options

| Environment Variable | Description | Default | Required |
|---------------------|-------------|---------|----------|
| `DISCORD_TOKEN` | Your Discord bot token | - | ✅ |
| `GITHUB_TOKEN` | Your GitHub personal access token | - | ✅ |
| `DISCORD_CHANNEL_ID` | Discord channel ID for notifications | - | ✅ |
| `CHECK_INTERVAL_MINUTES` | How often to check for notifications (minutes) | 5 | ❌ |
| `ONLY_UNREAD` | Only send unread notifications | true | ❌ |

## Usage

Once the bot is running, it will:

1. Check your GitHub notifications every few minutes (configurable)
2. Send new notifications to your Discord channel as rich embeds
3. Provide direct links to the GitHub items
4. Show notification type, reason, and status

## Example Discord Message

The bot sends rich embeds that look like this:

```
🔀 Add new feature for user authentication
Repository: username/my-awesome-project

Type: 🔀 Pull Request
Reason: 👀 Review Requested  
Status: 🔴 Unread

Repository Description: An awesome project that does cool things

GitHub Notification • Today at 2:30 PM
```

## Helper Scripts

The project includes several helper scripts to make setup and management easier:

- `setup.sh` - Automated setup script that installs dependencies and builds the project
- `validate-config.sh` - Validates your configuration and checks for common issues
- `start-bot.sh` - Starts the bot with proper error handling and logging
- `service-manager.sh` - Manages the bot as a systemd service (install, start, stop, etc.)
- `test-github-api.sh` - Tests your GitHub API connection and token validity

## Troubleshooting

### Bot doesn't start
- Run `./validate-config.sh` to check your configuration
- Check that all required environment variables are set
- Verify your Discord token and GitHub token are valid
- Make sure the Discord channel ID is correct

### No notifications received
- Check that you have GitHub notifications in your inbox
- Verify the GitHub token has the correct scopes (`notifications` and optionally `repo`)
- Check the bot logs for error messages: `./service-manager.sh logs` or check `bot.log`
- Test your GitHub API connection: `./test-github-api.sh`

### Discord messages not sending
- Ensure the bot has permission to send messages in the channel
- Verify the channel ID is correct
- Check that the bot is in the server and has the required permissions

### Permission Issues
- Make sure scripts are executable: `chmod +x *.sh`
- For systemd service, ensure you have sudo privileges

### Installing Node.js
If you don't have Node.js installed, the `setup.sh` script will guide you. You can also install it manually:

```bash
# Using NodeSource repository (recommended)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Or using snap
sudo snap install node --classic

# Or using nvm
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
source ~/.bashrc
nvm install 18
nvm use 18
```

## Development

```bash
# Install dependencies
npm install

# Run in development mode with auto-reload
npm run dev

# Build TypeScript
npm run build

# Build and watch for changes
npm run watch

# Test GitHub API connection
npm run test:github

# Validate configuration
npm run validate
```

## Local Usage Notes

This bot is designed for local use on your machine. To get started:

1. Make sure you have Node.js installed
2. Run the setup script: `./setup.sh`
3. Configure your tokens in the `.env` file
4. Start the bot with `./start-bot.sh`

The bot will run continuously, checking for GitHub notifications and sending them to your Discord channel.

## License

MIT License

## Support

If you encounter any issues, check the troubleshooting section above or run the diagnostic scripts:
- `./validate-config.sh` - Check configuration
- `./test-github-api.sh` - Test GitHub connectivity

---

*This project was created with AI assistance.*
