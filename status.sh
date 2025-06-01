#!/bin/bash

# Check the status of the GitHub Inbox Discord Bot

echo "📊 GitHub Inbox Discord Bot Status"
echo "=================================="

if [ -f "bot.pid" ]; then
    PID=$(cat bot.pid)
    if kill -0 $PID 2>/dev/null; then
        echo "✅ Bot is running (PID: $PID)"
        
        # Show process info
        echo
        echo "Process Information:"
        ps -p $PID -o pid,ppid,cmd,etime,cpu,mem
        
        # Show recent logs
        echo
        echo "Recent Log Output:"
        echo "------------------"
        if [ -f "bot.log" ]; then
            tail -10 bot.log
        else
            echo "No log file found."
        fi
    else
        echo "❌ Bot is not running (stale PID file found)"
        rm bot.pid
    fi
else
    echo "❌ Bot is not running (no PID file found)"
fi

echo
echo "Commands:"
echo "  Start bot:  ./start.sh"
echo "  Stop bot:   ./stop.sh"
echo "  View logs:  ./logs.sh"
