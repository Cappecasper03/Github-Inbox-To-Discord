#!/usr/bin/env python3
"""
Setup script for GitHub Inbox Discord Bot
This script helps you configure the bot with the necessary credentials.
"""

import os
import sys

def main():
    print("🤖 GitHub Inbox Discord Bot Setup")
    print("=" * 40)
    print()
    
    # Check if .env file exists
    env_file = ".env"
    if os.path.exists(env_file):
        print(f"⚠️  {env_file} already exists. This will overwrite it.")
        response = input("Continue? (y/N): ").strip().lower()
        if response != 'y':
            print("Setup cancelled.")
            return
    
    print("Please provide the following information:")
    print()
    
    # Discord Bot Token
    print("1. Discord Bot Token:")
    print("   - Go to https://discord.com/developers/applications")
    print("   - Create a new application and bot")
    print("   - Copy the bot token")
    discord_token = input("   Enter Discord Bot Token: ").strip()
    
    if not discord_token:
        print("❌ Discord Bot Token is required!")
        return
    
    print()
    
    # GitHub Token
    print("2. GitHub Personal Access Token:")
    print("   - Go to https://github.com/settings/tokens")
    print("   - Required scope: 'notifications'")
    print("   - Optional scope: 'repo' (only needed for private repository notifications)")
    github_token = input("   Enter GitHub Token: ").strip()
    
    if not github_token:
        print("❌ GitHub Token is required!")
        return
    
    print()
    
    # Discord Channel ID
    print("3. Discord Channel ID:")
    print("   - Enable Developer Mode in Discord")
    print("   - Right-click on the channel and copy ID")
    channel_id = input("   Enter Discord Channel ID: ").strip()
    
    if not channel_id:
        print("❌ Discord Channel ID is required!")
        return
    
    # Validate channel ID is numeric
    try:
        int(channel_id)
    except ValueError:
        print("❌ Discord Channel ID must be a number!")
        return
    
    print()
    
    # Check interval (optional)
    print("4. Check Interval (optional):")
    print("   - How often to check for notifications (in seconds)")
    print("   - Default: 300 seconds (5 minutes)")
    interval = input("   Enter check interval (press Enter for default): ").strip()
    
    if not interval:
        interval = "300"
    
    try:
        int(interval)
    except ValueError:
        print("❌ Check interval must be a number!")
        return
    
    # Write .env file
    try:
        with open(env_file, 'w') as f:
            f.write(f"DISCORD_BOT_TOKEN={discord_token}\n")
            f.write(f"GITHUB_TOKEN={github_token}\n")
            f.write(f"DISCORD_CHANNEL_ID={channel_id}\n")
            f.write(f"CHECK_INTERVAL={interval}\n")
        
        print()
        print("✅ Configuration saved to .env file!")
        print()
        print("Next steps:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Invite your Discord bot to your server with 'Send Messages' permission")
        print("3. Choose how to run the bot:")
        print()
        print("Development Mode:")
        print("  ./dev-manager.sh start      - Start bot for development")
        print("  ./dev-manager.sh debug      - Run with debug logging")
        print("  ./dev-manager.sh status     - Check development status")
        print("  ./dev-manager.sh logs       - View development logs")
        print("  ./dev-manager.sh test       - Test configuration")
        print("  ./dev-manager.sh --help     - Show all development commands")
        print()
        print("Production Mode (recommended for servers):")
        print("  ./service-manager.sh install  - Install as systemd service")
        print("  ./service-manager.sh start    - Start service")
        print("  ./service-manager.sh status   - Check service status")
        print("  ./service-manager.sh logs     - View service logs")
        print("  ./service-manager.sh --help   - Show all service commands")
        print()
        print("Bot Commands (use in the configured Discord channel):")
        print("  !check  - Manually check for notifications")
        print("  !status - Show bot status and configuration")
        
    except Exception as e:
        print(f"❌ Error writing configuration file: {e}")
        return

if __name__ == "__main__":
    main()
