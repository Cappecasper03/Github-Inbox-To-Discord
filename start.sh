#!/bin/bash

# Start the GitHub Inbox Discord Bot

echo "🚀 Starting GitHub Inbox Discord Bot..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Run ./install.sh first."
    exit 1
fi

# Check if configuration exists
if [ ! -f ".env" ]; then
    echo "❌ Configuration file (.env) not found. Run python setup.py first."
    exit 1
fi

# Activate virtual environment and start bot
source venv/bin/activate

# Check if bot is already running
if [ -f "bot.pid" ]; then
    PID=$(cat bot.pid)
    if kill -0 $PID 2>/dev/null; then
        echo "⚠️  Bot is already running (PID: $PID)"
        echo "   Use ./dev-manager.sh stop to stop it."
        exit 1
    else
        rm bot.pid
    fi
fi

# Start bot in background
nohup python bot.py > bot.log 2>&1 &
echo $! > bot.pid

echo "✅ Bot started successfully!"
echo "   PID: $(cat bot.pid)"
echo "   Logs: ./dev-manager.sh logs"
echo "   Stop: ./dev-manager.sh stop"
