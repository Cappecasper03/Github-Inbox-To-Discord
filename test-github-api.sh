#!/bin/bash

# GitHub API Test Script
# This script tests your GitHub token and API connectivity

ENV_FILE="/home/cappo/github-inbox-bot/.env"

echo "GitHub API Test Script"
echo "======================"

# Check if .env file exists
if [ ! -f "$ENV_FILE" ]; then
    echo "❌ .env file not found!"
    echo "Please copy .env.example to .env and configure it:"
    echo "  cp .env.example .env"
    exit 1
fi

# Source the .env file
source "$ENV_FILE"

# Check if GitHub token is set
if [ -z "$GITHUB_TOKEN" ]; then
    echo "❌ GITHUB_TOKEN is not set in .env file"
    exit 1
fi

echo "✅ GitHub token found"
echo "🔍 Testing GitHub API connectivity..."

# Test GitHub API
RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}" \
    -H "Authorization: token $GITHUB_TOKEN" \
    -H "Accept: application/vnd.github.v3+json" \
    -H "User-Agent: GitHub-Discord-Bot-Test" \
    "https://api.github.com/user")

HTTP_STATUS=$(echo "$RESPONSE" | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
BODY=$(echo "$RESPONSE" | sed -e 's/HTTPSTATUS\:.*//g')

if [ "$HTTP_STATUS" -eq 200 ]; then
    USERNAME=$(echo "$BODY" | grep -o '"login":"[^"]*"' | cut -d'"' -f4)
    echo "✅ GitHub API connection successful!"
    echo "👤 Authenticated as: $USERNAME"
    
    echo ""
    echo "🔍 Testing notifications endpoint..."
    
    NOTIF_RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}" \
        -H "Authorization: token $GITHUB_TOKEN" \
        -H "Accept: application/vnd.github.v3+json" \
        -H "User-Agent: GitHub-Discord-Bot-Test" \
        "https://api.github.com/notifications?per_page=1")
    
    NOTIF_HTTP_STATUS=$(echo "$NOTIF_RESPONSE" | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
    
    if [ "$NOTIF_HTTP_STATUS" -eq 200 ]; then
        echo "✅ Notifications endpoint accessible!"
        echo ""
        echo "🎉 GitHub API setup is working correctly!"
        echo "Your bot should be able to fetch notifications."
    else
        echo "❌ Notifications endpoint returned status: $NOTIF_HTTP_STATUS"
        echo "Please check that your token has 'notifications' scope."
    fi
    
else
    echo "❌ GitHub API connection failed!"
    echo "HTTP Status: $HTTP_STATUS"
    echo "Response: $BODY"
    echo ""
    echo "Common issues:"
    echo "- Invalid token"
    echo "- Token expired"
    echo "- Network connectivity issues"
fi
