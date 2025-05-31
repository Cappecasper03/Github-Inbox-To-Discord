#!/bin/bash

# GitHub Inbox Discord Bot Configuration Validator

BOT_DIR="/home/cappo/github-inbox-bot"
ENV_FILE="$BOT_DIR/.env"

echo "GitHub Inbox Discord Bot - Configuration Validator"
echo "=================================================="

# Check if .env file exists
if [ ! -f "$ENV_FILE" ]; then
    echo "❌ .env file not found!"
    echo "Please copy .env.example to .env and configure it:"
    echo "  cp .env.example .env"
    echo "  nano .env"
    exit 1
fi

echo "✅ .env file found"

# Source the .env file
source "$ENV_FILE"

# Check required variables
ERRORS=0

check_var() {
    local var_name="$1"
    local var_value="${!var_name}"
    
    if [ -z "$var_value" ]; then
        echo "❌ $var_name is not set or empty"
        ((ERRORS++))
    else
        echo "✅ $var_name is set"
    fi
}

echo ""
echo "Checking required environment variables..."
check_var "DISCORD_TOKEN"
check_var "GITHUB_TOKEN"
check_var "DISCORD_CHANNEL_ID"

echo ""
echo "Checking optional environment variables..."
if [ -n "$CHECK_INTERVAL_MINUTES" ]; then
    echo "✅ CHECK_INTERVAL_MINUTES is set to: $CHECK_INTERVAL_MINUTES"
else
    echo "ℹ️  CHECK_INTERVAL_MINUTES not set (will use default: 5)"
fi

if [ -n "$ONLY_UNREAD" ]; then
    echo "✅ ONLY_UNREAD is set to: $ONLY_UNREAD"
else
    echo "ℹ️  ONLY_UNREAD not set (will use default: true)"
fi

echo ""
echo "Checking project setup..."

# Check if node_modules exists
if [ -d "$BOT_DIR/node_modules" ]; then
    echo "✅ Dependencies installed (node_modules found)"
else
    echo "❌ Dependencies not installed"
    echo "Please run: npm install"
    ((ERRORS++))
fi

# Check if dist directory exists
if [ -d "$BOT_DIR/dist" ]; then
    echo "✅ Project built (dist directory found)"
else
    echo "❌ Project not built"
    echo "Please run: npm run build"
    ((ERRORS++))
fi

echo ""
if [ $ERRORS -eq 0 ]; then
    echo "🎉 Configuration looks good! You can start the bot with:"
    echo "  ./start-bot.sh"
    echo ""
    echo "Or install as a service:"
    echo "  ./service-manager.sh install"
    echo "  ./service-manager.sh start"
else
    echo "⚠️  Found $ERRORS issue(s). Please fix them before starting the bot."
fi
