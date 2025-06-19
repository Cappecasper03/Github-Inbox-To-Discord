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
    
    def get_check_suite_details(self, notification: Dict) -> Optional[Dict]:
        """Get CheckSuite details for GitHub Actions notifications"""
        print("\n--- FETCHING GITHUB ACTIONS DETAILS ---")
        
        subject = notification.get('subject', {})
        repository = notification.get('repository', {})
        
        print(f"Subject type: {subject.get('type')}")
        print(f"Repository: {repository.get('full_name')}")
        
        if subject.get('type') != 'CheckSuite' or not repository.get('full_name'):
            print("Not a CheckSuite notification or missing repository - skipping GitHub Actions lookup")
            return None
        
        # Extract check suite ID from the notification thread URL
        thread_url = notification.get('url', '')
        print(f"Thread URL: {thread_url}")
        
        if not thread_url:
            print("No thread URL found - cannot fetch CheckSuite details")
            return None
        
        try:
            print("Step 1: Fetching notification thread details...")
            print(f"Making request to: {thread_url}")
            
            # Get the thread details to find the CheckSuite API URL
            response = requests.get(thread_url, headers=self.headers)
            print(f"Thread API Response Status: {response.status_code}")
            print(f"Thread API Response Headers: {dict(response.headers)}")
            
            response.raise_for_status()
            thread_data = response.json()
            
            print("Thread data received:")
            pprint.pprint(thread_data, width=100, depth=2)
            
            # Look for CheckSuite URL in the thread subject
            check_suite_url = thread_data.get('subject', {}).get('url')
            print(f"CheckSuite URL from thread: {check_suite_url}")
            
            if not check_suite_url:
                print("CheckSuite URL is None - trying alternative approach...")
                
                # Alternative approach: Try to find recent check suites for this repo
                # and match by title/timing
                repo_full_name = repository.get('full_name')
                check_suites_url = f"https://api.github.com/repos/{repo_full_name}/check-suites"
                
                print(f"Step 2: Fetching recent check suites from: {check_suites_url}")
                
                # Get recent check suites
                response = requests.get(check_suites_url, headers=self.headers, params={'per_page': 10})
                print(f"Check Suites API Response Status: {response.status_code}")
                
                response.raise_for_status()
                check_suites_data = response.json()
                
                print(f"Found {len(check_suites_data.get('check_suites', []))} recent check suites")
                
                # Try to match by title and timing
                subject_title = subject.get('title', '')
                notification_updated = notification.get('updated_at', '')
                
                print(f"Looking for check suite matching title: '{subject_title}'")
                print(f"Notification updated at: {notification_updated}")
                
                for check_suite in check_suites_data.get('check_suites', []):
                    suite_updated = check_suite.get('updated_at', '')
                    suite_conclusion = check_suite.get('conclusion', '')
                    suite_status = check_suite.get('status', '')
                    
                    print(f"Checking suite: updated={suite_updated}, status={suite_status}, conclusion={suite_conclusion}")
                    
                    # Match by timing (within reasonable window) and failed status
                    if (suite_conclusion in ['failure', 'timed_out', 'cancelled'] or 
                        suite_status == 'completed' or suite_status == 'in_progress'):
                        
                        # Check if the timing is close (within 10 minutes)
                        try:
                            from datetime import datetime
                            notif_time = datetime.fromisoformat(notification_updated.replace('Z', '+00:00'))
                            suite_time = datetime.fromisoformat(suite_updated.replace('Z', '+00:00'))
                            time_diff = abs((notif_time - suite_time).total_seconds())
                            
                            print(f"Time difference: {time_diff} seconds")
                            
                            if time_diff <= 600:  # Within 10 minutes
                                print(f"Found matching check suite by timing!")
                                print("CheckSuite data from list:")
                                pprint.pprint(check_suite, width=100, depth=2)
                                
                                print(f"CheckSuite HTML URL: {check_suite.get('html_url')}")
                                print(f"CheckSuite Status: {check_suite.get('status')}")
                                print(f"CheckSuite Conclusion: {check_suite.get('conclusion')}")
                                
                                return check_suite
                        except Exception as e:
                            print(f"Error parsing dates: {e}")
                            continue
                
                print("No matching check suite found by timing")
                return None
            
            print("Step 2: Fetching CheckSuite details...")
            print(f"Making request to: {check_suite_url}")
            
            # Fetch CheckSuite details
            response = requests.get(check_suite_url, headers=self.headers)
            print(f"CheckSuite API Response Status: {response.status_code}")
            print(f"CheckSuite API Response Headers: {dict(response.headers)}")
            
            response.raise_for_status()
            check_suite_data = response.json()
            
            print("CheckSuite data received:")
            pprint.pprint(check_suite_data, width=100, depth=2)
            
            print(f"CheckSuite HTML URL: {check_suite_data.get('html_url')}")
            print(f"CheckSuite Status: {check_suite_data.get('status')}")
            print(f"CheckSuite Conclusion: {check_suite_data.get('conclusion')}")
            
            return check_suite_data
            
        except requests.exceptions.RequestException as e:
            print(f"FAILED to fetch CheckSuite details: {e}")
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
            print("CheckSuite notification detected - fetching GitHub Actions details...")
            # Handle GitHub Actions CheckSuite notifications
            check_suite_details = self.get_check_suite_details(notification)
            if check_suite_details:
                print("CheckSuite details retrieved successfully")
                # Get the HTML URL from CheckSuite details
                web_url = check_suite_details.get('html_url')
                print(f"GitHub Actions URL: {web_url}")
                
                # Update color based on CheckSuite status
                status = check_suite_details.get('status')
                conclusion = check_suite_details.get('conclusion')
                
                print(f"Updating embed color based on status: {status}, conclusion: {conclusion}")
                
                if status == 'completed':
                    if conclusion == 'success':
                        embed['color'] = 0x28a745  # Green for success
                        print("Set color to GREEN (success)")
                    elif conclusion in ['failure', 'timed_out', 'action_required']:
                        embed['color'] = 0xdc3545  # Red for failure
                        print("Set color to RED (failure)")
                    elif conclusion == 'cancelled':
                        embed['color'] = 0x6c757d  # Gray for cancelled
                        print("Set color to GRAY (cancelled)")
                    else:
                        embed['color'] = 0xffc107  # Yellow for other completed states
                        print("Set color to YELLOW (other completed)")
                else:
                    embed['color'] = 0x0366d6  # Blue for in progress
                    print("Set color to BLUE (in progress)")
                
                # Add additional fields for CheckSuite
                if conclusion:
                    status_field = {
                        "name": "Status",
                        "value": f"{status.title()} ({conclusion.replace('_', ' ').title()})",
                        "inline": True
                    }
                    embed['fields'].append(status_field)
                    print(f"Added status field: {status_field}")
                elif status:
                    status_field = {
                        "name": "Status", 
                        "value": status.title(),
                        "inline": True
                    }
                    embed['fields'].append(status_field)
                    print(f"Added status field: {status_field}")
            else:
                print("Failed to retrieve CheckSuite details")
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
