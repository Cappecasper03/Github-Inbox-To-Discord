# GitHub Notifications to Discord

> **🤖 AI-Generated Project:** This GitHub Action was created with AI assistance (GitHub Copilot) to automatically fetch GitHub notifications and send them to Discord. The project includes Python scripts, GitHub workflows, and documentation to help you set up automated notification forwarding between GitHub and Discord.

This GitHub Action automatically fetches your GitHub notifications and sends new ones to a Discord channel via webhook.

## Features

- 🔔 Fetches GitHub notifications every 15 minutes
- 📬 Sends new notifications to Discord with rich embeds
- 🎨 Color-coded embeds based on notification type (Issues, Pull Requests, etc.)
- 🔄 Tracks last check time to avoid duplicates
- 📊 Supports manual triggering via GitHub Actions UI
- 🚀 Easy setup with environment variables

## Setup Instructions

### 1. Fork or Clone This Repository

### 2. Set Up Discord Webhook

1. Go to your Discord server
2. Navigate to Server Settings → Integrations → Webhooks
3. Click "New Webhook"
4. Choose the channel where you want notifications
5. Copy the webhook URL

### 3. Configure GitHub Repository Secrets

Go to your repository → Settings → Secrets and variables → Actions

Add the following **Repository Secret**:

- `DISCORD_WEBHOOK_URL`: Your Discord webhook URL

### 4. Set Up GitHub Token (Optional but Recommended)

The action uses the default `PRIVATE_GITHUB_TOKEN` which has access to the repository it's running in. For personal notifications, you might want to create a Personal Access Token:

1. Go to GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Generate a new token with `notifications` scope
3. Add it as a repository secret named `PRIVATE_GITHUB_TOKEN` (this will override the default)

### 5. Initialize Repository Variable

The action uses a repository variable to track the last check time. You can initialize it manually:

1. Go to your repository → Settings → Secrets and variables → Actions
2. Go to the "Variables" tab
3. Add a new repository variable:
   - Name: `LAST_CHECK_TIME`
   - Value: Leave empty (it will be set automatically on first run)

### 6. Test the Action

1. Go to Actions tab in your repository
2. Select "Check GitHub Notifications and Send to Discord"
3. Click "Run workflow" to test manually
4. Check your Discord channel for notifications

## Configuration

### Notification Schedule

The action runs every 15 minutes by default. You can modify the schedule in `.github/workflows/check-notifications.yml`:

```yaml
on:
  schedule:
    - cron: '*/15 * * * *'  # Every 15 minutes
    # - cron: '0 * * * *'   # Every hour
    # - cron: '0 9 * * *'   # Every day at 9 AM
```

### Notification Types

The bot handles various GitHub notification types:

- 🟢 **Issues** (Green)
- 🔵 **Pull Requests** (Blue)  
- 🟣 **Releases** (Purple)
- 🟡 **Discussions** (Yellow)
- ⚪ **Commits** (Gray)

### Rate Limits

- Discord: The bot respects Discord webhook rate limits by batching notifications (max 10 per message)
- GitHub: Uses the standard GitHub API rate limits (5000 requests per hour for authenticated requests)

## Troubleshooting

### No Notifications Appearing

1. Check if you have unread GitHub notifications
2. Verify the Discord webhook URL is correct
3. Check the Actions logs for any errors
4. Ensure the `LAST_CHECK_TIME` variable is set correctly

### Action Failing

1. Check the Actions logs in GitHub
2. Verify all secrets are set correctly
3. Ensure the Discord webhook URL is valid and the channel exists

### Too Many/Too Few Notifications

- The bot only sends **unread** notifications
- Notifications are filtered by the `since` parameter based on last check time
- Mark notifications as read in GitHub to stop receiving them

## File Structure

```text
├── .github/
│   └── workflows/
│       └── check-notifications.yml  # GitHub Action workflow
├── notification_checker.py          # Main Python script
├── requirements.txt                 # Python dependencies
└── README.md                       # This file
```

## Contributing

Feel free to open issues or submit pull requests to improve this bot!

## License

This project is open source and available under the MIT License.
