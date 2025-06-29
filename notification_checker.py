#!/usr/bin/env python3
"""
GitHub Notifications to Discord Bot

This script fetches GitHub notifications and sends new, richly formatted ones 
to a Discord channel via a webhook.
"""

import os
import sys
import json
import requests
from datetime import datetime, timezone
from typing import List, Dict, Optional
import hashlib
import pprint
import time

class GitHubNotificationBot:
    # Constants for formatting, inspired by the old script
    TYPE_COLORS = {
        'Issue': 0xdb2777,          # Pink
        'PullRequest': 0x8b5cf6,    # Violet
        'Release': 0xf59e0b,        # Amber
        'Discussion': 0x3b82f6,     # Blue
        'Commit': 0x6b7280,         # Gray
        'SecurityAdvisory': 0xef4444 # Red
    }
    TYPE_EMOJIS = {
        'Issue': 'Issue:',
        'PullRequest': 'Pull Request:',
        'Release': 'Release:',
        'Discussion': 'Discussion:',
        'SecurityAdvisory': 'Security Advisory:',
        'Commit': 'Commit: '
    }
    REASON_DESCRIPTIONS = {
        'assign': 'You were assigned',
        'author': 'You created this thread',
        'comment': 'New comment',
        'invitation': 'You were invited to a repository',
        'manual': 'You subscribed manually',
        'mention': 'You were mentioned',
        'review_requested': 'Your review was requested',
        'security_alert': 'A security alert was triggered',
        'state_change': 'The state was changed',
        'subscribed': 'You are watching this repository',
        'team_mention': 'Your team was mentioned'
    }

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
    
    def _get_subject_details(self, url: str) -> Optional[Dict]:
        """Helper to fetch details for a PR or Issue from its API URL."""
        if not url:
            return None
        try:
            print(f"    Fetching details from: {url}")
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"    Could not fetch details for {url}. Error: {e}")
            return None

    def get_notifications(self) -> List[Dict]:
        """Fetch GitHub notifications"""
        print("\n" + "="*50)
        print("STEP 1: FETCHING GITHUB NOTIFICATIONS")
        print("="*50)
        
        url = 'https://api.github.com/notifications'
        params = {
            'all': 'false',
            'participating': 'false'
        }
        if self.last_check_time:
            try:
                datetime.fromisoformat(self.last_check_time.replace('Z', '+00:00'))
                params['since'] = self.last_check_time
                print(f"Using 'since' parameter: {self.last_check_time}")
            except (ValueError, AttributeError):
                print(f"Invalid LAST_CHECK_TIME format: {self.last_check_time}. Fetching all notifications.")
        else:
            print("No last check time found - fetching all unread notifications")
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            notifications = response.json()
            print(f"Total notifications received: {len(notifications)}")
            return notifications
            
        except requests.exceptions.RequestException as e:
            print(f"API REQUEST FAILED: {e}")
            return []

    def format_notification_for_discord(self, notification: Dict) -> Dict:
        """Format a GitHub notification for a rich Discord embed."""
        subject = notification.get('subject', {})
        repo = notification.get('repository', {})
        subject_type = subject.get('type', 'Unknown')

        # Basic embed structure
        emoji = self.TYPE_EMOJIS.get(subject_type, '📢')
        embed = {
            "title": f"{emoji} {subject.get('title', 'No title')}",
            "color": self.TYPE_COLORS.get(subject_type, 0x586069),
            "timestamp": notification.get('updated_at'),
            "fields": []
        }

        # Set thumbnail to repo owner's avatar
        if repo.get('owner', {}).get('avatar_url'):
            embed["thumbnail"] = {"url": repo['owner']['avatar_url']}

        # Convert API URL to a user-friendly web URL
        if subject.get('url'):
            api_url = subject['url']
            web_url = api_url.replace('api.github.com/repos', 'github.com')
            if '/pulls/' in web_url:
                web_url = web_url.replace('/pulls/', '/pull/')
            # No change needed for /issues/
            embed["url"] = web_url

        # Field: Repository
        embed["fields"].append({
            "name": "Repository",
            "value": f"[{repo.get('full_name', 'Unknown')}]({repo.get('html_url', '#')})",
            "inline": True
        })

        # Field: Reason for notification
        reason = notification.get('reason', 'unknown')
        embed["fields"].append({
            "name": "Reason",
            "value": self.REASON_DESCRIPTIONS.get(reason, reason.replace('_', ' ').title()),
            "inline": True
        })
        
        # Field: Last Activity Time (relative)
        if notification.get('updated_at'):
            dt_obj = datetime.fromisoformat(notification['updated_at'].replace('Z', '+00:00'))
            timestamp = int(dt_obj.timestamp())
            embed["fields"].append({
                "name": "Last Activity",
                "value": f"<t:{timestamp}:R>",
                "inline": True
            })

        # --- Detailed Status Field (with extra API call) ---
        status_value = "Unavailable"
        details = self._get_subject_details(subject.get('url'))
        
        if details:
            state = details.get('state', 'unknown').title()
            
            if subject_type == 'PullRequest':
                if details.get('merged'):
                    status_value = f"Merged"
                elif state == 'Open':
                    status_value = f"{state}"
                else: # Closed
                    status_value = f"{state}"
                
                if details.get('draft'):
                    status_value += " (Draft)"

            elif subject_type == 'Issue':
                if state == 'Open':
                    status_value = f"{state}"
                else: # Closed
                    status_value = f"{state}"
            
            else: # For Release, Discussion, etc.
                status_value = state
        
        embed["fields"].append({
            "name": "Status",
            "value": status_value,
            "inline": True
        })

        return embed

    def send_to_discord(self, notifications: List[Dict]) -> bool:
        """Send notifications to Discord, formatting each one."""
        print("\n" + "="*50)
        print("STEP 2: FORMATTING AND SENDING TO DISCORD")
        print("="*50)
        
        if not notifications:
            print("No new notifications to send")
            return True
        
        print(f"Processing {len(notifications)} notifications for Discord...")
        
        # Sort notifications by time (oldest first) to send in chronological order
        notifications.sort(key=lambda n: n['updated_at'])
        
        for i in range(0, len(notifications), 10):
            batch = notifications[i:i+10]
            print(f"\nProcessing batch {i//10 + 1} ({len(batch)} notifications)...")
            
            embeds = []
            for j, notif in enumerate(batch):
                print(f"\n--- Formatting notification {i+j+1} for Discord ---")
                pprint.pprint(notif, depth=2)
                embed = self.format_notification_for_discord(notif)
                embeds.append(embed)
            
            discord_payload = {
                "content": f"**{len(batch)} new GitHub notification{'s' if len(batch) > 1 else ''}**",
                "embeds": embeds
            }
            
            print(f"\nSending batch {i//10 + 1} to Discord...")
            try:
                response = requests.post(
                    self.discord_webhook_url,
                    json=discord_payload,
                    headers={'Content-Type': 'application/json'}
                )
                response.raise_for_status()
                print(f"SUCCESS: Sent {len(batch)} notifications to Discord (Status: {response.status_code})")
                if i + 10 < len(notifications):
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
        
        notifications = self.get_notifications()
        
        if notifications:
            success = self.send_to_discord(notifications)
            if success:
                print("\n" + "="*60)
                print("FINAL RESULT: Successfully processed all notifications.")
            else:
                print("\n" + "="*60)
                print("FINAL RESULT: Some notifications failed to send.")
                sys.exit(1)
        else:
            print("\n" + "="*60)
            print("FINAL RESULT: No new notifications found.")

if __name__ == "__main__":
    try:
        bot = GitHubNotificationBot()
        bot.run()
    except Exception as e:
        print(f"FATAL ERROR running notification bot: {e}")
        sys.exit(1)