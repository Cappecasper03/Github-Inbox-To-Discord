#!/usr/bin/env python3
"""
Development runner for the GitHub Inbox Discord Bot
This script runs the bot with additional debugging and development features.
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup detailed logging for development
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot_debug.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

# Import and run the bot
try:
    from bot import GitHubNotificationBot
    
    print("🔧 Starting GitHub Inbox Discord Bot in development mode...")
    print("📋 Debug logging enabled (see bot_debug.log)")
    print("⏹️  Press Ctrl+C to stop")
    print("-" * 50)
    
    bot = GitHubNotificationBot()
    bot.run()
    
except KeyboardInterrupt:
    print("\n\n⏹️  Bot stopped by user")
except Exception as e:
    print(f"\n❌ Error: {e}")
    logging.exception("Bot crashed with exception:")
    sys.exit(1)
