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
        reason = notification.get('reason', '').lower()
        
        colors = {
            'Issue': 0x28a745,      # Green
            'PullRequest': 0x0366d6, # Blue
            'Release': 0x6f42c1,     # Purple
            'Discussion': 0xffc107,  # Yellow
            'Commit': 0x6c757d,      # Gray
            'WorkflowRun': 0xff6b35, # Orange
            'CheckSuite': 0xff6b35,  # Orange
            'CheckRun': 0xff6b35,    # Orange
        }
        
        # Special handling for workflow-related notifications
        if 'workflow' in reason or 'ci' in reason or 'check' in reason:
            color = colors.get('WorkflowRun', 0xff6b35)
        else:
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
                },                {
                    "name": "Type",
                    "value": self._format_notification_type(subject_type, notification),
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
            web_url = self._convert_api_url_to_web_url(api_url, repository, notification)
            
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
    
    def _convert_api_url_to_web_url(self, api_url: str, repository: Dict, notification: Dict) -> str:
        """Convert GitHub API URL to web URL"""
        if not api_url:
            return repository.get('html_url', '')
        
        # Handle different types of GitHub URLs
        if 'pulls' in api_url:
            # Pull request: /repos/owner/repo/pulls/123 -> /owner/repo/pull/123
            return api_url.replace('api.github.com/repos', 'github.com').replace('/pulls/', '/pull/')
        
        elif 'issues' in api_url:
            # Issue: /repos/owner/repo/issues/123 -> /owner/repo/issues/123
            return api_url.replace('api.github.com/repos', 'github.com').replace('/issues/', '/issues/')
        
        elif 'actions/runs' in api_url:
            # GitHub Actions workflow run: /repos/owner/repo/actions/runs/123 -> /owner/repo/actions/runs/123
            return api_url.replace('api.github.com/repos', 'github.com')
        
        elif 'releases' in api_url:
            # Release: /repos/owner/repo/releases/123 -> /owner/repo/releases/tag/TAG_NAME
            # We'll need to fetch the release info to get the tag name
            try:
                response = requests.get(api_url, headers=self.headers)
                if response.status_code == 200:
                    release_data = response.json()
                    tag_name = release_data.get('tag_name', '')
                    if tag_name:
                        repo_full_name = repository.get('full_name', '')
                        return f"https://github.com/{repo_full_name}/releases/tag/{tag_name}"
            except Exception as e:
                print(f"Error fetching release data: {e}")
            
            # Fallback to releases page
            repo_full_name = repository.get('full_name', '')
            return f"https://github.com/{repo_full_name}/releases"
        
        elif 'commits' in api_url:
            # Commit: /repos/owner/repo/commits/sha -> /owner/repo/commit/sha
            return api_url.replace('api.github.com/repos', 'github.com').replace('/commits/', '/commit/')
        
        elif 'discussions' in api_url:
            # Discussion: /repos/owner/repo/discussions/123 -> /owner/repo/discussions/123
            return api_url.replace('api.github.com/repos', 'github.com')
        
        else:
            # For any other type, try to detect if it's a workflow-related notification
            # by checking the notification reason or subject type
            reason = notification.get('reason', '').lower()
            subject_type = notification.get('subject', {}).get('type', '').lower()
            
            if 'workflow' in reason or 'action' in reason or 'ci' in reason:
                # This might be a workflow notification, try to construct actions URL
                repo_full_name = repository.get('full_name', '')
                if repo_full_name:
                    return f"https://github.com/{repo_full_name}/actions"
            
            # Default fallback to repository URL
            return repository.get('html_url', '')

    def _format_notification_type(self, subject_type: str, notification: Dict) -> str:
        """Format the notification type for display"""
        reason = notification.get('reason', '').lower()
        
        # Map common notification types to more readable names
        type_mapping = {
            'PullRequest': 'Pull Request',
            'Issue': 'Issue',
            'Release': 'Release',
            'Discussion': 'Discussion',
            'Commit': 'Commit',
            'WorkflowRun': 'Workflow Run',
            'CheckSuite': 'Check Suite',
            'CheckRun': 'Check Run'
        }
        
        # Check if this is a workflow-related notification
        if 'workflow' in reason or 'ci' in reason or 'check' in reason:
            if subject_type == 'CheckSuite':
                return type_mapping.get('CheckSuite', 'Workflow')
            elif subject_type == 'CheckRun':
                return type_mapping.get('CheckRun', 'Workflow')
            else:
                return 'Workflow'
        
        return type_mapping.get(subject_type, subject_type)


if __name__ == "__main__":
    try:
        bot = GitHubNotificationBot()
        bot.run()
    except Exception as e:
        print(f"Error running notification bot: {e}")
        sys.exit(1)
