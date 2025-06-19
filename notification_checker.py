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
import pprint


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
            'X-GitHub-Api-Version': '2022-11-28'        }
        
    def get_notifications(self) -> List[Dict]:
        """Fetch GitHub notifications"""
        print("\n" + "="*50)
        print("STEP 1: FETCHING GITHUB NOTIFICATIONS")
        print("="*50)
        
        url = 'https://api.github.com/notifications'
        params = {
            'all': 'false',  # Only unread notifications
            'participating': 'false'  # Include all notifications, not just participating
        }        
        print(f"API Endpoint: {url}")
        print(f"Initial Parameters: {json.dumps(params, indent=2)}")
        
        # If we have a last check time, only get notifications since then
        if self.last_check_time:
            print(f"Last check time found: {self.last_check_time}")
            # Validate that last_check_time is a proper ISO 8601 datetime
            # If it's just "0" or invalid, skip the since parameter
            try:
                # Try to parse as ISO 8601 datetime
                datetime.fromisoformat(self.last_check_time.replace('Z', '+00:00'))
                params['since'] = self.last_check_time
                print(f"Using 'since' parameter: {self.last_check_time}")
            except (ValueError, AttributeError):
                print(f"Invalid LAST_CHECK_TIME format: {self.last_check_time}. Fetching all notifications.")                # Don't add since parameter, will fetch all unread notifications
        else:
            print("No last check time found - fetching all unread notifications")
        
        print(f"Final Parameters: {json.dumps(params, indent=2)}")
        print(f"Headers: {json.dumps({k: v if k != 'Authorization' else 'token [REDACTED]' for k, v in self.headers.items()}, indent=2)}")
        
        try:
            print("\nMaking API request...")
            response = requests.get(url, headers=self.headers, params=params)
            print(f"Response Status: {response.status_code}")
            print(f"Response Headers: {dict(response.headers)}")
            
            response.raise_for_status()
            notifications = response.json()
            
            print(f"\nGITHUB API RESPONSE:")
            print(f"Total notifications received: {len(notifications)}")
            
            if notifications:
                print("\nDETAILED NOTIFICATION DATA:")
                for i, notification in enumerate(notifications, 1):
                    print(f"\n--- Notification #{i} ---")
                    print("Raw JSON data:")
                    pprint.pprint(notification, width=100, depth=3)
                    print("-" * 30)
            else:
                print("No notifications returned from API")
            
            return notifications
            
        except requests.exceptions.RequestException as e:
            print(f"API REQUEST FAILED: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Error response status: {e.response.status_code}")
                print(f"Error response body: {e.response.text}")
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
                "url": repository['owner'].get('html_url', '')            }
        
        return embed
    
    def send_to_discord(self, notifications: List[Dict]) -> bool:
        """Send notifications to Discord"""
        print("\n" + "="*50)
        print("STEP 2: FORMATTING AND SENDING TO DISCORD")
        print("="*50)
        
        if not notifications:
            print("No new notifications to send")
            return True
        
        print(f"Processing {len(notifications)} notifications for Discord...")
        
        # Group notifications to avoid hitting Discord's rate limits
        # Send up to 10 embeds per message
        for i in range(0, len(notifications), 10):
            batch = notifications[i:i+10]
            print(f"\nProcessing batch {i//10 + 1} ({len(batch)} notifications)...")
            
            # Format each notification for Discord
            embeds = []
            for j, notif in enumerate(batch):
                print(f"\n--- Formatting notification {i+j+1} for Discord ---")
                embed = self.format_notification_for_discord(notif)
                print("Discord embed data:")
                pprint.pprint(embed, width=100, depth=3)
                embeds.append(embed)
            
            discord_payload = {
                "content": f"**{len(batch)} new GitHub notification{'s' if len(batch) > 1 else ''}**",
                "embeds": embeds
            }
            
            print(f"\nFINAL DISCORD PAYLOAD FOR BATCH {i//10 + 1}:")
            print("Full payload being sent to Discord:")
            pprint.pprint(discord_payload, width=100, depth=4)
            
            print(f"\nSending to Discord webhook: {self.discord_webhook_url[:50]}...")
            
            try:
                response = requests.post(
                    self.discord_webhook_url,
                    json=discord_payload,
                    headers={'Content-Type': 'application/json'}
                )
                print(f"Discord API Response Status: {response.status_code}")
                print(f"Discord API Response Headers: {dict(response.headers)}")
                if response.text:
                    print(f"Discord API Response Body: {response.text}")
                
                response.raise_for_status()
                print(f"SUCCESS: Sent {len(batch)} notifications to Discord")
                
                # Add a small delay between batches to respect rate limits
                if i + 10 < len(notifications):
                    import time
                    print("Waiting 1 second before next batch...")
                    time.sleep(1)
                    
            except requests.exceptions.RequestException as e:
                print(f"ERROR sending to Discord: {e}")
                if hasattr(e, 'response') and e.response is not None:
                    print(f"Error response status: {e.response.status_code}")
                    print(f"Error response body: {e.response.text}")
                return False
        
        return True

    def run(self):
        """Main execution function"""
        print("\n" + "="*60)
        print("GITHUB NOTIFICATIONS TO DISCORD BOT - STARTING")
        print("="*60)
        
        print(f"Checking GitHub notifications...")
        print(f"Last check time: {self.last_check_time or 'Never'}")
        
        # Fetch notifications
        notifications = self.get_notifications()
        print(f"\nFound {len(notifications)} notifications")
        
        if notifications:
            # Send all notifications to Discord without filtering
            success = self.send_to_discord(notifications)
            if success:
                print("\n" + "="*60)
                print("FINAL RESULT: Successfully processed all notifications")
                print("="*60)
            else:
                print("\n" + "="*60)
                print("FINAL RESULT: Some notifications failed to send")
                print("="*60)
                sys.exit(1)
        else:
            print("\n" + "="*60)
            print("FINAL RESULT: No new notifications found")
            print("="*60)


if __name__ == "__main__":
    try:
        bot = GitHubNotificationBot()
        bot.run()
    except Exception as e:
        print(f"Error running notification bot: {e}")
        sys.exit(1)
