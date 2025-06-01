#!/bin/bash

# View logs of the GitHub Inbox Discord Bot

echo "📋 GitHub Inbox Discord Bot Logs"
echo "==============================="

if [ ! -f "bot.log" ]; then
    echo "❌ Log file not found. Bot may not have been started yet."
    exit 1
fi

echo "Latest logs (press Ctrl+C to exit):"
echo "-----------------------------------"

# Follow the log file
tail -f bot.log
