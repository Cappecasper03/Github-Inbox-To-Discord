#!/usr/bin/env python3
"""
Test script to verify the GitHub Inbox Discord Bot configuration
"""

import os
import sys
from dotenv import load_dotenv

def test_configuration():
    print("🔍 Testing GitHub Inbox Discord Bot Configuration")
    print("=" * 50)
    print()
    
    # Load environment variables
    if not os.path.exists('.env'):
        print("❌ .env file not found!")
        print("Run 'python setup.py' to create the configuration file.")
        return False
    
    load_dotenv()
    
    # Check required environment variables
    required_vars = [
        'DISCORD_BOT_TOKEN',
        'GITHUB_TOKEN', 
        'DISCORD_CHANNEL_ID',
        'CHECK_INTERVAL'
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
        else:
            if var == 'DISCORD_BOT_TOKEN':
                print(f"✅ {var}: {'*' * (len(value) - 4)}{value[-4:]}")
            elif var == 'GITHUB_TOKEN':
                print(f"✅ {var}: {'*' * (len(value) - 4)}{value[-4:]}")
            else:
                print(f"✅ {var}: {value}")
    
    if missing_vars:
        print()
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        return False
    
    print()
    
    # Test GitHub connection
    try:
        from github import Github
        github_token = os.getenv('GITHUB_TOKEN')
        github = Github(github_token)
        user = github.get_user()
        print(f"✅ GitHub connection successful! Logged in as: {user.login}")
        
        # Test notifications access
        notifications = list(github.get_user().get_notifications())
        print(f"✅ GitHub notifications access successful! Found {len(notifications)} notifications")
        
    except Exception as e:
        print(f"❌ GitHub connection failed: {e}")
        return False
    
    # Test Discord channel ID format
    try:
        channel_id = int(os.getenv('DISCORD_CHANNEL_ID'))
        print(f"✅ Discord Channel ID format is valid: {channel_id}")
    except ValueError:
        print("❌ Discord Channel ID must be a valid integer")
        return False
    
    # Test check interval
    try:
        interval = int(os.getenv('CHECK_INTERVAL'))
        print(f"✅ Check interval is valid: {interval} seconds")
    except ValueError:
        print("❌ Check interval must be a valid integer")
        return False
    
    print()
    print("🎉 All configuration tests passed!")
    print()
    print("You can now run the bot with: python bot.py")
    
    return True

if __name__ == "__main__":
    try:
        success = test_configuration()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
