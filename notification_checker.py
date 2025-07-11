#!/usr/bin/env python3
"""
GitHub Notifications to Discord Bot

This script fetches GitHub notifications and sends new, richly formatted ones 
to a Discord channel via a webhook.
"""

import os
import sys
import json
import re
import requests
from datetime import datetime, timezone
from typing import List, Dict, Optional
import hashlib
import pprint
import time

class GitHubNotificationBot:
    # Constants for formatting - Base type colors
    TYPE_COLORS = {
        'Issue': 0xdb2777,          # Pink
        'PullRequest': 0x8b5cf6,    # Violet
        'Release': 0xf59e0b,        # Amber
        'Discussion': 0x3b82f6,     # Blue
        'Commit': 0x6b7280,         # Gray
        'SecurityAdvisory': 0xff6b35 # Orange
    }
    
    # State-specific colors (override base colors when applicable)
    STATE_COLORS = {
        'open': 0x10b981,          # Green - for open issues/PRs
        'closed': 0xef4444,        # Red - for closed issues/PRs
        'merged': 0x8b5cf6,        # Purple - for merged PRs
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
    
    def get_comment_content(self, notification: Dict) -> Optional[Dict]:
        """Fetch the actual comment content that triggered the notification"""
        try:
            subject = notification.get('subject', {})
            reason = notification.get('reason', '')
            
            # Only fetch comments for relevant notification reasons
            if reason not in ['comment', 'mention']:
                return None
            
            # Get notification timestamp for comparison
            notification_time_str = notification.get('updated_at')
            if not notification_time_str:
                return None
                
            notification_time = datetime.fromisoformat(notification_time_str.replace('Z', '+00:00'))
            
            subject_type = subject.get('type')
            subject_url = subject.get('url')
            
            if not subject_url:
                return None
            
            comment_content = None
            comment_author = None
            comment_url = None
            matching_comment = None
            
            if subject_type == 'Issue':
                # Extract issue number from URL
                import re
                issue_match = re.search(r'/issues/(\d+)', subject_url)
                if issue_match:
                    issue_number = issue_match.group(1)
                    repo_match = re.search(r'/repos/([^/]+/[^/]+)/', subject_url)
                    if repo_match:
                        repo_name = repo_match.group(1)
                        comments_url = f"https://api.github.com/repos/{repo_name}/issues/{issue_number}/comments"
                        
                        print(f"    Fetching issue comments from: {comments_url}")
                        response = requests.get(comments_url, headers=self.headers, timeout=10)
                        response.raise_for_status()
                        comments = response.json()
                        
                        if comments:
                            # Find comment closest to notification time
                            time_tolerance_seconds = 300  # 5 minutes
                            
                            for comment in reversed(comments):  # Start from newest
                                comment_time = datetime.fromisoformat(comment['created_at'].replace('Z', '+00:00'))
                                time_diff = abs((notification_time - comment_time).total_seconds())
                                
                                if time_diff <= time_tolerance_seconds:
                                    matching_comment = comment
                                    break
                            
                            # If no exact match, use the most recent comment before notification
                            if not matching_comment:
                                for comment in reversed(comments):
                                    comment_time = datetime.fromisoformat(comment['created_at'].replace('Z', '+00:00'))
                                    if comment_time <= notification_time:
                                        matching_comment = comment
                                        break
                            
                            # Fallback to latest comment
                            if not matching_comment and comments:
                                matching_comment = comments[-1]
                            
                            if matching_comment:
                                comment_content = matching_comment.get('body', '')
                                comment_author = matching_comment.get('user', {}).get('login', 'Unknown')
                                comment_url = matching_comment.get('html_url', '')
                        
            elif subject_type == 'PullRequest':
                # Extract PR number from URL
                pr_match = re.search(r'/pulls/(\d+)', subject_url)
                if pr_match:
                    pr_number = pr_match.group(1)
                    repo_match = re.search(r'/repos/([^/]+/[^/]+)/', subject_url)
                    if repo_match:
                        repo_name = repo_match.group(1)
                        
                        # Get both issue comments and review comments for PRs
                        issue_comments_url = f"https://api.github.com/repos/{repo_name}/issues/{pr_number}/comments"
                        review_comments_url = f"https://api.github.com/repos/{repo_name}/pulls/{pr_number}/comments"
                        
                        all_comments = []
                        
                        # Fetch issue comments
                        try:
                            print(f"    Fetching PR issue comments from: {issue_comments_url}")
                            response = requests.get(issue_comments_url, headers=self.headers, timeout=10)
                            response.raise_for_status()
                            issue_comments = response.json()
                            
                            for comment in issue_comments:
                                comment_time = datetime.fromisoformat(comment['created_at'].replace('Z', '+00:00'))
                                all_comments.append({
                                    'created_at': comment_time,
                                    'body': comment.get('body', ''),
                                    'author': comment.get('user', {}).get('login', 'Unknown'),
                                    'url': comment.get('html_url', ''),
                                    'type': 'issue_comment'
                                })
                        except requests.exceptions.RequestException as e:
                            print(f"    Could not fetch issue comments: {e}")
                        
                        # Fetch review comments
                        try:
                            print(f"    Fetching PR review comments from: {review_comments_url}")
                            response = requests.get(review_comments_url, headers=self.headers, timeout=10)
                            response.raise_for_status()
                            review_comments = response.json()
                            
                            for comment in review_comments:
                                comment_time = datetime.fromisoformat(comment['created_at'].replace('Z', '+00:00'))
                                all_comments.append({
                                    'created_at': comment_time,
                                    'body': comment.get('body', ''),
                                    'author': comment.get('user', {}).get('login', 'Unknown'),
                                    'url': comment.get('html_url', ''),
                                    'type': 'review_comment'
                                })
                        except requests.exceptions.RequestException as e:
                            print(f"    Could not fetch review comments: {e}")
                        
                        if all_comments:
                            # Sort by creation time (newest first)
                            all_comments.sort(key=lambda x: x['created_at'], reverse=True)
                            
                            # Find comment that matches the notification time
                            time_tolerance_seconds = 300  # 5 minutes
                            
                            for comment_data in all_comments:
                                time_diff = abs((notification_time - comment_data['created_at']).total_seconds())
                                if time_diff <= time_tolerance_seconds:
                                    matching_comment = comment_data
                                    break
                            
                            # If no exact match, use the most recent comment before notification
                            if not matching_comment:
                                for comment_data in all_comments:
                                    if comment_data['created_at'] <= notification_time:
                                        matching_comment = comment_data
                                        break
                            
                            # Fallback to latest comment
                            if not matching_comment and all_comments:
                                matching_comment = all_comments[0]
                            
                            if matching_comment:
                                comment_content = matching_comment['body']
                                comment_author = matching_comment['author']
                                comment_url = matching_comment['url']
            
            if comment_content:
                # Truncate long comments for Discord embed limits
                max_length = 1000  # Leave room for other embed content
                if len(comment_content) > max_length:
                    comment_content = comment_content[:max_length-3] + "..."
                
                return {
                    'content': comment_content,
                    'author': comment_author,
                    'url': comment_url
                }
                
        except Exception as e:
            print(f"    Could not fetch comment content for notification: {e}")
            
        return None

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

        # Get detailed status information first to determine color
        status_value = "Unavailable"
        embed_color = self.TYPE_COLORS.get(subject_type, 0x586069)  # Default color
        details = self._get_subject_details(subject.get('url'))
        
        if details:
            state = details.get('state', 'unknown').lower()
            
            # Filter out cancelled/skipped workflows based on type, title, and status/conclusion
            is_workflow_notification = subject_type in ['CheckSuite', 'CheckRun']
            title_lower = subject.get('title', '').lower()
            
            if is_workflow_notification:
                # Check for common cancellation/skipped phrases in title
                if any(phrase in title_lower for phrase in ["workflow run cancelled", "workflow run skipped", "cancelled workflow", "skipped workflow"]):
                    print(f"    Skipping workflow due to title match: {subject.get('title', 'No title')}")
                    return None
                
                # Check for status/conclusion in details for CheckSuite/CheckRun
                if details:
                    status = details.get('status')
                    conclusion = details.get('conclusion')
                    
                    if status == 'completed' and conclusion in ['cancelled', 'skipped', 'failure']:
                        print(f"    Skipping workflow due to status/conclusion: {subject.get('title', 'No title')} (Status: {status}, Conclusion: {conclusion})")
                        return None
            
            if subject_type == 'PullRequest':
                if details.get('merged'):
                    status_value = "Merged"
                    embed_color = self.STATE_COLORS['merged']
                elif state == 'open':
                    status_value = "Open"
                    embed_color = self.STATE_COLORS['open']
                elif state == 'closed':
                    status_value = "Closed"
                    embed_color = self.STATE_COLORS['closed']
                else:
                    status_value = state.title()
                
                if details.get('draft') and state == 'open':
                    status_value += " (Draft)"
                    # Keep the open color but could add a draft-specific color if desired

            elif subject_type == 'Issue':
                if state == 'open':
                    status_value = "Open"
                    embed_color = self.STATE_COLORS['open']
                elif state == 'closed':
                    status_value = "Closed"
                    embed_color = self.STATE_COLORS['closed']
                else:
                    status_value = state.title()
            
            else: # For Release, Discussion, etc. - use base type colors
                status_value = state.title()
                # Keep the base type color for these
        
        # Basic embed structure with dynamic color
        embed = {
            "title": subject.get('title', 'No title'),
            "color": embed_color,
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

        # Field: Type
        embed["fields"].append({
            "name": "Type",
            "value": subject_type,
            "inline": True
        })

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
            "value": reason,
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

        # Add status field (status_value was determined above during color selection)
        embed["fields"].append({
            "name": "Status",
            "value": status_value,
            "inline": True
        })

        # --- Add comment content if available ---
        comment_data = self.get_comment_content(notification)
        if comment_data:
            comment_text = comment_data['content']
            comment_author = comment_data['author']
            comment_url = comment_data['url']
            
            # Format the comment content
            embed["fields"].append({
                "name": f"💬 Latest Comment by @{comment_author}",
                "value": f"```\n{comment_text}\n```\n[View Comment]({comment_url})",
                "inline": False
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
                if embed: # Only add if embed is not None
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