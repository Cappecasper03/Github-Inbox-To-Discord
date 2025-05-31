#!/bin/bash

# GitHub Inbox Discord Bot Startup Script
# This script handles starting the bot with proper error handling

BOT_DIR="/home/cappo/github-inbox-bot"
LOG_FILE="$BOT_DIR/bot.log"

echo "Starting GitHub Inbox Discord Bot..."
echo "Log file: $LOG_FILE"
echo "Working directory: $BOT_DIR"

# Check if .env file exists
if [ ! -f "$BOT_DIR/.env" ]; then
    echo "❌ Error: .env file not found!"
    echo "Please copy .env.example to .env and configure your tokens:"
    echo "  cp .env.example .env"
    echo "  nano .env"
    exit 1
fi

# Check if node_modules exists
if [ ! -d "$BOT_DIR/node_modules" ]; then
    echo "❌ Error: Dependencies not installed!"
    echo "Please run: npm install"
    exit 1
fi

# Check if dist directory exists
if [ ! -d "$BOT_DIR/dist" ]; then
    echo "❌ Error: Project not built!"
    echo "Please run: npm run build"
    exit 1
fi

# Change to bot directory
cd "$BOT_DIR"

# Start the bot
echo "🚀 Starting bot..."
exec npm start 2>&1 | tee -a "$LOG_FILE"
