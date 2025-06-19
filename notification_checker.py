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
    
    def get_github_actions_url(self, notification: Dict) -> Optional[str]:
        """Get the actual GitHub Actions URL from a CheckSuite notification"""
        print("\n--- FETCHING GITHUB ACTIONS URL ---")
        
        subject = notification.get('subject', {})
        repository = notification.get('repository', {})
        
        print(f"Subject type: {subject.get('type')}")
        print(f"Repository: {repository.get('full_name')}")
        
        if subject.get('type') != 'CheckSuite' or not repository.get('full_name'):
            print("Not a CheckSuite notification - skipping GitHub Actions URL lookup")
            return None
        
        thread_url = notification.get('url', '')
        print(f"Thread URL: {thread_url}")
        
        if not thread_url:
            print("No thread URL found")
            return None
        
        try:
            print("Fetching notification thread to find target URL...")
            
            # The key insight: we need to check the 'latest_comment_url' or construct the URL
            # from the notification data. For CheckSuite notifications, we can often construct
            # the GitHub Actions URL from the repository and notification metadata.
            
            # First, try to get additional details from the thread
            response = requests.get(thread_url, headers=self.headers)
            print(f"Thread API Response Status: {response.status_code}")
            
            response.raise_for_status()
            thread_data = response.json()
            
            # Look for the target URL in various places
            target_url = None
            
            # Check if there's a latest_comment_url that might lead us to the right place
            latest_comment_url = thread_data.get('subject', {}).get('latest_comment_url')
            print(f"Latest comment URL: {latest_comment_url}")
            
            # For CheckSuite notifications, try to construct the Actions URL
            # GitHub Actions URLs typically follow the pattern:
            # https://github.com/{owner}/{repo}/actions/runs/{run_id}
            
            # We can try to find recent workflow runs for this repo
            repo_full_name = repository.get('full_name')
            workflow_runs_url = f"https://api.github.com/repos/{repo_full_name}/actions/runs"
            
            print(f"Fetching recent workflow runs from: {workflow_runs_url}")
            
            response = requests.get(workflow_runs_url, headers=self.headers, params={
                'per_page': 20,
                'status': 'completed'  # Focus on completed runs which are more likely to match notifications
            })
            print(f"Workflow runs API Response Status: {response.status_code}")
            
            if response.status_code == 200:
                runs_data = response.json()
                workflow_runs = runs_data.get('workflow_runs', [])
                
                print(f"Found {len(workflow_runs)} recent workflow runs")
                
                # Try to match by timing and title
                subject_title = subject.get('title', '').lower()
                notification_updated = notification.get('updated_at', '')
                
                print(f"Looking for workflow run matching notification:")
                print(f"  Title contains: {subject_title}")
                print(f"  Updated around: {notification_updated}")
                
                for run in workflow_runs:
                    run_updated = run.get('updated_at', '')
                    run_conclusion = run.get('conclusion', '')
                    run_name = run.get('name', '').lower()
                    run_display_title = run.get('display_title', '').lower()
                    
                    print(f"Checking run: {run.get('html_url')}")
                    print(f"  Name: {run_name}")
                    print(f"  Display title: {run_display_title}")
                    print(f"  Conclusion: {run_conclusion}")
                    print(f"  Updated: {run_updated}")
                    
                    # Try to match by title keywords and timing
                    title_matches = False
                    if 'workflow run failed' in subject_title:
                        # Extract the workflow name from the title
                        # "Windows workflow run failed for slang branch" -> look for "windows"
                        title_parts = subject_title.replace('workflow run failed', '').strip().split()
                        for part in title_parts:
                            if part in run_name or part in run_display_title:
                                title_matches = True
                                print(f"  Title match found: '{part}' in run name/title")
                                break
                    
                    # Check timing (within 15 minutes)
                    timing_matches = False
                    try:
                        from datetime import datetime
                        notif_time = datetime.fromisoformat(notification_updated.replace('Z', '+00:00'))
                        run_time = datetime.fromisoformat(run_updated.replace('Z', '+00:00'))
                        time_diff = abs((notif_time - run_time).total_seconds())
                        
                        print(f"  Time difference: {time_diff} seconds")
                        
                        if time_diff <= 900:  # Within 15 minutes
                            timing_matches = True
                            print(f"  Timing match found!")
                        
                    except Exception as e:
                        print(f"  Error parsing dates: {e}")
                    
                    # If we have both title and timing match, or just timing for failed runs
                    if (title_matches and timing_matches) or (timing_matches and run_conclusion in ['failure', 'cancelled', 'timed_out']):
                        target_url = run.get('html_url')
                        print(f"FOUND MATCHING WORKFLOW RUN: {target_url}")
                        break
                
                if not target_url and workflow_runs:
                    # Fallback: use the most recent failed run
                    for run in workflow_runs:
                        if run.get('conclusion') in ['failure', 'cancelled', 'timed_out']:
                            target_url = run.get('html_url')
                            print(f"FALLBACK: Using most recent failed run: {target_url}")
                            break
            
            return target_url
            
        except requests.exceptions.RequestException as e:
            print(f"FAILED to fetch GitHub Actions URL: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Error response status: {e.response.status_code}")
                print(f"Error response body: {e.response.text}")
            return None

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
            'CheckSuite': 0xdc3545,  # Red for failed CI
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
          # Handle URL generation based on notification type
        web_url = None
        
        print(f"Processing notification type: {subject_type}")
        
        if subject.get('url'):
            print(f"Standard notification with URL: {subject.get('url')}")
            # Convert API URL to web URL for standard notifications
            api_url = subject['url']
            if 'pulls' in api_url:
                web_url = api_url.replace('api.github.com/repos', 'github.com').replace('/pulls/', '/pull/')
            elif 'issues' in api_url:
                web_url = api_url.replace('api.github.com/repos', 'github.com').replace('/issues/', '/issues/')
            else:
                web_url = repository.get('html_url', '')
            print(f"Converted to web URL: {web_url}")
        elif subject_type == 'CheckSuite':
            print("CheckSuite notification detected - fetching GitHub Actions URL...")
            # Handle GitHub Actions CheckSuite notifications
            actions_url = self.get_github_actions_url(notification)
            if actions_url:
                print("GitHub Actions URL retrieved successfully")
                web_url = actions_url
                print(f"GitHub Actions URL: {web_url}")
                
                # Set color to red for failed CI by default
                embed['color'] = 0xdc3545  # Red for failure
                print("Set color to RED (GitHub Actions failure)")
            else:
                print("Failed to retrieve GitHub Actions URL")
        else:
            print(f"No URL handling for notification type: {subject_type}")
          # Add URL to embed if we found one
        if web_url:
            embed["url"] = web_url
            print(f"Final embed URL set to: {web_url}")
        else:
            print("No URL to add to embed")
        
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
