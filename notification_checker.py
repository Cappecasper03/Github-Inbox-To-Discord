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
        
        # Debug output for GitHub Actions notifications
        if self._is_github_actions_notification(notification):
            print(f"DEBUG: GitHub Actions notification detected:")
            print(f"  Subject Type: {subject.get('type', 'Unknown')}")
            print(f"  Subject Title: {subject.get('title', 'No title')}")
            print(f"  Subject URL: {subject.get('url', 'No URL')}")
            print(f"  Reason: {notification.get('reason', 'Unknown')}")
            print(f"  Repository: {repository.get('full_name', 'Unknown')}")
        
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
        if self._is_github_actions_notification(notification):
            color = colors.get('WorkflowRun', 0xff6b35)
        elif 'workflow' in reason or 'ci' in reason or 'check' in reason:
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
                },
                {
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
        
        # Always try to get a URL - either from subject or construct one for GitHub Actions
        web_url = None
        if subject.get('url'):
            # Convert API URL to web URL
            api_url = subject['url']
            web_url = self._convert_api_url_to_web_url(api_url, repository, notification)
        elif self._is_github_actions_notification(notification):
            # GitHub Actions notifications often don't have URLs, so construct one
            web_url = self._get_github_actions_url(notification, repository)
        
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
        repo_full_name = repository.get('full_name', '')
        reason = notification.get('reason', '').lower()
        subject_type = notification.get('subject', {}).get('type', '').lower()
        
        # Handle GitHub Actions notifications specially since they often don't have URLs
        if self._is_github_actions_notification(notification):
            return self._get_github_actions_url(notification, repository)
        
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
        
        elif 'check-runs' in api_url:
            # GitHub Check Run: try to get the workflow run from the check run
            try:
                response = requests.get(api_url, headers=self.headers)
                if response.status_code == 200:
                    check_run_data = response.json()
                    # Check if this check run has an associated workflow run
                    check_suite_url = check_run_data.get('check_suite', {}).get('url', '')
                    if check_suite_url:
                        # Get the check suite to find the workflow run
                        suite_response = requests.get(check_suite_url, headers=self.headers)
                        if suite_response.status_code == 200:
                            suite_data = suite_response.json()
                            run_id = suite_data.get('id')
                            if run_id and repo_full_name:
                                return f"https://github.com/{repo_full_name}/actions/runs/{run_id}"
            except Exception as e:
                print(f"Error fetching check run data: {e}")
            
            # Fallback to actions page
            if repo_full_name:
                return f"https://github.com/{repo_full_name}/actions"
        
        elif 'check-suites' in api_url:
            # GitHub Check Suite: try to get the workflow run ID
            try:
                response = requests.get(api_url, headers=self.headers)
                if response.status_code == 200:
                    check_suite_data = response.json()
                    run_id = check_suite_data.get('id')
                    if run_id and repo_full_name:
                        return f"https://github.com/{repo_full_name}/actions/runs/{run_id}"
            except Exception as e:
                print(f"Error fetching check suite data: {e}")
            
            # Fallback to actions page
            if repo_full_name:
                return f"https://github.com/{repo_full_name}/actions"
        
        elif 'releases' in api_url:
            # Release: /repos/owner/repo/releases/123 -> /owner/repo/releases/tag/TAG_NAME
            # We'll need to fetch the release info to get the tag name
            try:
                response = requests.get(api_url, headers=self.headers)
                if response.status_code == 200:
                    release_data = response.json()
                    tag_name = release_data.get('tag_name', '')
                    if tag_name:
                        return f"https://github.com/{repo_full_name}/releases/tag/{tag_name}"
            except Exception as e:
                print(f"Error fetching release data: {e}")
            
            # Fallback to releases page
            return f"https://github.com/{repo_full_name}/releases"
        
        elif 'commits' in api_url:
            # Commit: /repos/owner/repo/commits/sha -> /owner/repo/commit/sha
            return api_url.replace('api.github.com/repos', 'github.com').replace('/commits/', '/commit/')
        
        elif 'discussions' in api_url:
            # Discussion: /repos/owner/repo/discussions/123 -> /owner/repo/discussions/123
            return api_url.replace('api.github.com/repos', 'github.com')
        
        else:
            # Default fallback to repository URL
            return repository.get('html_url', '')
    
    def _is_github_actions_notification(self, notification: Dict) -> bool:
        """Check if this is a GitHub Actions related notification"""
        reason = notification.get('reason', '').lower()
        subject_type = notification.get('subject', {}).get('type', '').lower()
        subject_title = notification.get('subject', {}).get('title', '').lower()
        
        # Check various indicators of GitHub Actions notifications
        actions_indicators = [
            'workflow' in reason,
            'ci' in reason,
            'check' in reason,
            subject_type in ['checksuite', 'checkrun', 'workflowrun'],
            'workflow' in subject_title,
            'build' in subject_title and ('failed' in subject_title or 'passed' in subject_title or 'success' in subject_title),
            'ci' in subject_title,
            'test' in subject_title and ('failed' in subject_title or 'passed' in subject_title),
        ]
        
        return any(actions_indicators)
    
    def _get_github_actions_url(self, notification: Dict, repository: Dict) -> str:
        """Get the appropriate GitHub Actions URL for a notification"""
        repo_full_name = repository.get('full_name', '')
        if not repo_full_name:
            return repository.get('html_url', '')
        
        subject = notification.get('subject', {})
        api_url = subject.get('url', '')
        
        # Try to extract run ID from various sources
        run_id = None
        
        # Method 1: If we have a direct actions/runs URL
        if api_url and 'actions/runs' in api_url:
            try:
                run_id = api_url.split('/runs/')[-1].split('?')[0]
                if run_id.isdigit():
                    return f"https://github.com/{repo_full_name}/actions/runs/{run_id}"
            except:
                pass
        
        # Method 2: Try to get run ID from check suite or check run
        if api_url:
            try:
                response = requests.get(api_url, headers=self.headers)
                if response.status_code == 200:
                    data = response.json()
                    
                    # If it's a check suite, the ID might be the run ID
                    if 'check-suites' in api_url:
                        run_id = data.get('id')
                        if run_id:
                            return f"https://github.com/{repo_full_name}/actions/runs/{run_id}"
                    
                    # If it's a check run, try to get the suite and then the run
                    elif 'check-runs' in api_url:
                        check_suite_url = data.get('check_suite', {}).get('url', '')
                        if check_suite_url:
                            suite_response = requests.get(check_suite_url, headers=self.headers)
                            if suite_response.status_code == 200:
                                suite_data = suite_response.json()
                                run_id = suite_data.get('id')
                                if run_id:
                                    return f"https://github.com/{repo_full_name}/actions/runs/{run_id}"
            except Exception as e:
                print(f"Error trying to get workflow run ID: {e}")
        
        # Method 3: Try to extract from notification thread URL or other fields
        thread_url = notification.get('url', '')
        if thread_url:
            # Sometimes the thread URL contains useful information
            # This is a fallback method that might work in some cases
            pass
          # Fallback: Return the general actions page for the repository
        return f"https://github.com/{repo_full_name}/actions"
    
    def _format_notification_type(self, subject_type: str, notification: Dict) -> str:
        """Format the notification type for display"""
        reason = notification.get('reason', '').lower()
        subject_title = notification.get('subject', {}).get('title', '').lower()
        
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
        
        # Enhanced GitHub Actions detection and formatting
        if self._is_github_actions_notification(notification):
            # Try to be more specific about the workflow status
            if 'failed' in subject_title or 'failure' in subject_title:
                return 'Workflow Failed ❌'
            elif 'passed' in subject_title or 'success' in subject_title:
                return 'Workflow Passed ✅'
            elif 'cancelled' in subject_title or 'canceled' in subject_title:
                return 'Workflow Cancelled ⏹️'
            elif 'in_progress' in subject_title or 'running' in subject_title:
                return 'Workflow Running 🔄'
            elif subject_type == 'CheckSuite':
                return 'Check Suite'
            elif subject_type == 'CheckRun':
                return 'Check Run'
            else:
                return 'Workflow'
        
        # Check if this is a workflow-related notification (legacy detection)
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
