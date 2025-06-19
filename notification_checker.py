#!/usr/bin/env python3
"""
GitHub Notifications to Discord Bot

This script fetches GitHub notifications and sends new ones to a Discord channel.
"""

import os
import sys
import json
import requests
from datetime import datetime, timezone
from typing import List, Dict, Optional
import hashlib


class GitHubNotificationBot:
    def __init__(self):
        self.github_token = os.getenv('PRIVATE_GITHUB_TOKEN')
        self.discord_webhook_url = os.getenv('DISCORD_WEBHOOK_URL')
        self.last_check_time = os.getenv('LAST_CHECK_TIME')
        
        if not self.github_token:
            raise ValueError("PRIVATE_GITHUB_TOKEN environment variable is required")
        if not self.discord_webhook_url:
            raise ValueError("DISCORD_WEBHOOK_URL environment variable is required")
        
        self.headers = {
            'Authorization': f'token {self.github_token}',
            'Accept': 'application/vnd.github+json',
            'X-GitHub-Api-Version': '2022-11-28'
        }
        
    def get_notifications(self) -> List[Dict]:
        """Fetch GitHub notifications"""
        url = 'https://api.github.com/notifications'
        params = {
            'all': 'false',  # Only unread notifications
            'participating': 'false'  # Include all notifications, not just participating
        }
        
        # If we have a last check time, only get notifications since then
        if self.last_check_time:
            # Validate that last_check_time is a proper ISO 8601 datetime
            # If it's just "0" or invalid, skip the since parameter
            try:
                # Try to parse as ISO 8601 datetime
                datetime.fromisoformat(self.last_check_time.replace('Z', '+00:00'))
                params['since'] = self.last_check_time
            except (ValueError, AttributeError):
                print(f"Invalid LAST_CHECK_TIME format: {self.last_check_time}. Fetching all notifications.")
                # Don't add since parameter, will fetch all unread notifications
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching notifications: {e}")
            return []
    
    def format_notification_for_discord(self, notification: Dict) -> Dict:
        """Format a GitHub notification for Discord embed"""
        subject = notification.get('subject', {})
        repository = notification.get('repository', {})
        
        # Determine notification type and color
        subject_type = subject.get('type', 'Unknown')
        colors = {
            'Issue': 0x28a745,      # Green
            'PullRequest': 0x0366d6, # Blue
            'Release': 0x6f42c1,     # Purple
            'Discussion': 0xffc107,  # Yellow
            'Commit': 0x6c757d,      # Gray
        }
        color = colors.get(subject_type, 0x586069)
        
        # Create Discord embed
        embed = {
            "title": subject.get('title', 'No title'),
            "color": color,
            "timestamp": notification.get('updated_at'),
            "fields": [
                {
                    "name": "Repository",
                    "value": repository.get('full_name', 'Unknown'),
                    "inline": True
                },
                {
                    "name": "Type",
                    "value": subject_type,
                    "inline": True
                },
                {
                    "name": "Reason",
                    "value": notification.get('reason', 'Unknown').replace('_', ' ').title(),
                    "inline": True
                }
            ]
        }
        
        # Add URL if available
        if subject.get('url'):
            # Convert API URL to web URL
            api_url = subject['url']
            if 'pulls' in api_url:
                web_url = api_url.replace('api.github.com/repos', 'github.com').replace('/pulls/', '/pull/')
            elif 'issues' in api_url:
                web_url = api_url.replace('api.github.com/repos', 'github.com').replace('/issues/', '/issues/')
            else:
                web_url = repository.get('html_url', '')
            
            if web_url:
                embed["url"] = web_url
        
        # Add author info if available
        if repository.get('owner'):
            embed["author"] = {
                "name": repository['owner']['login'],
                "icon_url": repository['owner'].get('avatar_url', ''),
                "url": repository['owner'].get('html_url', '')
            }
        
        return embed
    
    def send_to_discord(self, notifications: List[Dict]) -> bool:
        """Send notifications to Discord"""
        if not notifications:
            print("No new notifications to send")
            return True
        
        # Group notifications to avoid hitting Discord's rate limits
        # Send up to 10 embeds per message
        for i in range(0, len(notifications), 10):
            batch = notifications[i:i+10]
            embeds = [self.format_notification_for_discord(notif) for notif in batch]
            
            discord_payload = {
                "content": f"📬 **{len(batch)} new GitHub notification{'s' if len(batch) > 1 else ''}**",
                "embeds": embeds
            }
            
            try:
                response = requests.post(
                    self.discord_webhook_url,
                    json=discord_payload,
                    headers={'Content-Type': 'application/json'}
                )
                response.raise_for_status()
                print(f"Successfully sent {len(batch)} notifications to Discord")
                
                # Add a small delay between batches to respect rate limits
                if i + 10 < len(notifications):
                    import time
                    time.sleep(1)
                    
            except requests.exceptions.RequestException as e:
                print(f"Error sending to Discord: {e}")
                return False
        
        return True

    def run(self):
        """Main execution function"""
        print(f"Checking GitHub notifications...")
        print(f"Last check time: {self.last_check_time or 'Never'}")
        
        # Fetch notifications
        notifications = self.get_notifications()
        print(f"Found {len(notifications)} notifications")
        
        if notifications:
            # Send all notifications to Discord without filtering
            success = self.send_to_discord(notifications)
            if success:
                print("✅ Successfully processed all notifications")
            else:
                print("❌ Some notifications failed to send")
                sys.exit(1)
        else:
            print("No new notifications found")


if __name__ == "__main__":
    try:
        bot = GitHubNotificationBot()
        bot.run()
    except Exception as e:
        print(f"Error running notification bot: {e}")
        sys.exit(1)
