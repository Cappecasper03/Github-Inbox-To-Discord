#!/bin/bash

# Stop the GitHub Inbox Discord Bot

echo "🛑 Stopping GitHub Inbox Discord Bot..."

if [ ! -f "bot.pid" ]; then
    echo "❌ Bot PID file not found. Bot may not be running."
    exit 1
fi

PID=$(cat bot.pid)

if kill -0 $PID 2>/dev/null; then
    kill $PID
    echo "✅ Bot stopped (PID: $PID)"
    rm bot.pid
else
    echo "❌ Bot process not found (PID: $PID)"
    rm bot.pid
    exit 1
fi
