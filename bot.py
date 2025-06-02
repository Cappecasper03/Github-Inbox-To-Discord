import discord
from discord.ext import commands, tasks
import asyncio
import os
import json
import re
from datetime import datetime, timezone
from dotenv import load_dotenv
from github import Github
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GitHubNotificationBot:
    def __init__(self):
        # Discord bot setup
        intents = discord.Intents.default()
        intents.message_content = True
        self.bot = commands.Bot(command_prefix='!', intents=intents)
        
        # GitHub setup
        self.github_token = os.getenv('GITHUB_TOKEN')
        if not self.github_token:
            raise ValueError("GITHUB_TOKEN environment variable is required")
        
        logger.info("Initializing GitHub API client...")
        self.github = Github(self.github_token)
        
        # Test GitHub connection and permissions
        try:
            user = self.github.get_user()
            logger.info(f"GitHub API connection successful for user: {user.login}")
            
            # Test notification access
            # Note: Just getting notifications to test API access
            notifications = user.get_notifications(all=False)
            notifications_list = list(notifications)
            logger.info(f"GitHub notifications API access confirmed (found {len(notifications_list)} recent notifications)")
        except Exception as e:
            logger.warning(f"GitHub API test failed: {e}")
            # Don't raise here, let it fail later with better error handling
        
        # Discord setup
        self.discord_token = os.getenv('DISCORD_BOT_TOKEN')
        if not self.discord_token:
            raise ValueError("DISCORD_BOT_TOKEN environment variable is required")
        
        self.channel_id = os.getenv('DISCORD_CHANNEL_ID')
        if not self.channel_id:
            raise ValueError("DISCORD_CHANNEL_ID environment variable is required")
        
        try:
            self.channel_id = int(self.channel_id)
        except ValueError:
            raise ValueError("DISCORD_CHANNEL_ID must be a valid integer")
        
        # Configuration
        self.check_interval = int(os.getenv('CHECK_INTERVAL', 300))  # Default: 5 minutes
        self.last_check_file = 'last_check.json'
        
        # Setup bot events
        self.setup_events()
        
    def setup_events(self):
        @self.bot.event
        async def on_ready():
            logger.info(f'{self.bot.user} has connected to Discord!')
            
            # Verify channel exists
            channel = self.bot.get_channel(self.channel_id)
            if not channel:
                logger.error(f"Cannot find Discord channel with ID: {self.channel_id}")
                return
            
            logger.info(f"Will send notifications to channel: #{channel.name}")
            
            # Start the notification checker
            if not self.check_notifications.is_running():
                self.check_notifications.start()
                
        @self.bot.command(name='check')
        async def manual_check(ctx):
            """Manually check for GitHub notifications"""
            if ctx.channel.id != self.channel_id:
                await ctx.send("This command can only be used in the configured notifications channel.")
                return
                
            # Send initial checking message
            checking_msg = await ctx.send("🔍 Checking for GitHub notifications...")
            
            try:
                count = await self.fetch_and_send_notifications()
                if count > 0:
                    # Update the message with success info
                    embed = discord.Embed(
                        title="✅ Manual Check Complete",
                        description=f"Found and sent **{count}** new notification{'s' if count != 1 else ''}!",
                        color=discord.Color.green()
                    )
                    embed.add_field(
                        name="📬 What's new?", 
                        value="Check the messages above for details about each notification.", 
                        inline=False
                    )
                    embed.set_footer(text="GitHub Notification Bot")
                    await checking_msg.edit(content="", embed=embed)
                else:
                    # Update with no notifications found
                    embed = discord.Embed(
                        title="📭 Manual Check Complete",
                        description="No new notifications found at this time.",
                        color=discord.Color.blue()
                    )
                    embed.add_field(
                        name="💡 This means", 
                        value="• All your notifications have been seen\n• No new activity since last check\n• Your GitHub repos are quiet right now", 
                        inline=False
                    )
                    embed.set_footer(text="GitHub Notification Bot")
                    await checking_msg.edit(content="", embed=embed)
            except Exception as e:
                logger.error(f"Error during manual check: {e}")
                error_embed = discord.Embed(
                    title="❌ Check Failed",
                    description="Something went wrong while checking for notifications.",
                    color=discord.Color.red()
                )
                error_embed.add_field(
                    name="Error Details", 
                    value=f"```{str(e)[:1000]}```", 
                    inline=False
                )
                error_embed.set_footer(text="GitHub Notification Bot")
                await checking_msg.edit(content="", embed=error_embed)
                
        @self.bot.command(name='status')
        async def bot_status(ctx):
            """Show bot status and configuration"""
            if ctx.channel.id != self.channel_id:
                await ctx.send("This command can only be used in the configured notifications channel.")
                return
                
            try:
                user = self.github.get_user()
                embed = discord.Embed(
                    title="🤖 GitHub Notification Bot Status",
                    color=discord.Color.blue()
                )
                embed.add_field(name="GitHub User", value=user.login, inline=True)
                embed.add_field(name="Check Interval", value=f"{self.check_interval} seconds", inline=True)
                embed.add_field(name="Channel", value=f"<#{self.channel_id}>", inline=True)
                embed.add_field(name="Bot Status", value="🟢 Online", inline=True)
                
                # Get last check time
                last_check = self.load_last_check()
                if last_check:
                    embed.add_field(
                        name="Last Check", 
                        value=f"<t:{int(last_check.timestamp())}:R>", 
                        inline=True
                    )
                
                await ctx.send(embed=embed)
            except Exception as e:
                logger.error(f"Error getting status: {e}")
                await ctx.send(f"❌ Error getting status: {str(e)}")

    def load_last_check(self):
        """Load the timestamp of the last notification check"""
        try:
            if os.path.exists(self.last_check_file):
                with open(self.last_check_file, 'r') as f:
                    data = json.load(f)
                    return datetime.fromisoformat(data['last_check'])
        except Exception as e:
            logger.warning(f"Could not load last check time: {e}")
        return None

    def save_last_check(self, timestamp):
        """Save the timestamp of the current check"""
        try:
            with open(self.last_check_file, 'w') as f:
                json.dump({'last_check': timestamp.isoformat()}, f)
        except Exception as e:
            logger.error(f"Could not save last check time: {e}")

    def format_notification_embed(self, notification):
        """Format a GitHub notification as a Discord embed"""
        subject = notification.subject
        repo = notification.repository
        
        # Determine notification type and color
        notification_types = {
            'Issue': {'emoji': '🐛', 'color': discord.Color.red()},
            'PullRequest': {'emoji': '🔀', 'color': discord.Color.green()},
            'Release': {'emoji': '🚀', 'color': discord.Color.gold()},
            'Discussion': {'emoji': '💬', 'color': discord.Color.blue()},
            'SecurityAdvisory': {'emoji': '🔒', 'color': discord.Color.dark_red()},
        }
        
        notification_info = notification_types.get(subject.type, {'emoji': '📢', 'color': discord.Color.blue()})
        
        # Create more meaningful reason descriptions
        reason_descriptions = {
            'assign': 'You were assigned to this',
            'author': 'You created this',
            'comment': 'New comment on this',
            'invitation': 'You were invited to collaborate',
            'manual': 'You subscribed to this',
            'mention': 'You were mentioned in this',
            'review_requested': 'Your review was requested',
            'security_alert': 'Security alert for this repository',
            'state_change': 'Status changed on this',
            'subscribed': 'You are watching this',
            'team_mention': 'Your team was mentioned'
        }
        
        reason_text = reason_descriptions.get(notification.reason, notification.reason.replace('_', ' ').title())
        
        # Build a more descriptive title
        action_context = f"{reason_text} {subject.type.lower()}"
        
        # Fix URL conversion for different types
        display_url = subject.url
        if subject.url:
            display_url = subject.url.replace('api.github.com/repos', 'github.com')
            if '/pulls/' in display_url:
                display_url = display_url.replace('/pulls/', '/pull/')
            elif '/issues/' in display_url:
                display_url = display_url.replace('/issues/', '/issues/')
        
        embed = discord.Embed(
            title=f"{notification_info['emoji']} {subject.title}",
            description=f"**{action_context}**",
            url=display_url,
            color=notification_info['color']
        )
        
        # Add repository info with more context
        embed.add_field(
            name="📁 Repository", 
            value=f"[{repo.full_name}]({repo.html_url})", 
            inline=True
        )
        
        # Add type with more description
        type_descriptions = {
            'Issue': 'Bug report or feature request',
            'PullRequest': 'Code contribution',
            'Release': 'New version release',
            'Discussion': 'Community discussion',
            'SecurityAdvisory': 'Security vulnerability notice'
        }
        type_desc = type_descriptions.get(subject.type, subject.type)
        embed.add_field(
            name="📋 Type", 
            value=f"{subject.type}\n*{type_desc}*", 
            inline=True
        )
        
        # Add reason with emoji and description
        reason_emojis = {
            'assign': '👤',
            'author': '✍️',
            'comment': '💬',
            'mention': '📢',
            'review_requested': '👀',
            'security_alert': '🔒',
            'state_change': '🔄',
            'subscribed': '👁️'
        }
        reason_emoji = reason_emojis.get(notification.reason, '📌')
        embed.add_field(
            name="🔔 Why you got this", 
            value=f"{reason_emoji} {reason_text}", 
            inline=True
        )
        
        # Add timing information
        if notification.updated_at:
            embed.add_field(
                name="⏰ Last Activity", 
                value=f"<t:{int(notification.updated_at.timestamp())}:R>", 
                inline=True
            )
        
        # Add unread status and detailed state information
        status_info = "🔵 Unread" if notification.unread else "✅ Read"
        
        # Get detailed status information based on notification type
        detailed_status = None
        try:
            if subject.type == 'PullRequest':
                # Extract PR number from URL
                import re
                pr_match = re.search(r'/pulls/(\d+)', subject.url)
                if pr_match:
                    pr_number = int(pr_match.group(1))
                    pr = repo.get_pull(pr_number)
                    state_emoji = {
                        'open': '🟢 Open',
                        'closed': '🔴 Closed',
                        'merged': '🟣 Merged'
                    }
                    pr_state = 'merged' if pr.merged else pr.state
                    detailed_status = f"{state_emoji.get(pr_state, pr_state.title())}"
                    if pr.draft:
                        detailed_status += " (Draft)"
                    
            elif subject.type == 'Issue':
                # Extract issue number from URL
                issue_match = re.search(r'/issues/(\d+)', subject.url)
                if issue_match:
                    issue_number = int(issue_match.group(1))
                    issue = repo.get_issue(issue_number)
                    state_emoji = {
                        'open': '🟢 Open',
                        'closed': '🔴 Closed'
                    }
                    detailed_status = f"{state_emoji.get(issue.state, issue.state.title())}"
                    
            elif subject.type == 'Release':
                # For releases, show if it's a prerelease or latest
                releases = list(repo.get_releases())
                if releases:
                    latest_release = releases[0]
                    if subject.title == latest_release.title:
                        detailed_status = "🚀 Latest Release"
                        if latest_release.prerelease:
                            detailed_status += " (Pre-release)"
                    else:
                        detailed_status = "📦 Release"
                        
        except Exception as e:
            logger.debug(f"Could not get detailed status for {subject.type}: {e}")
            
        embed.add_field(
            name="📬 Status", 
            value=f"{status_info}\n{detailed_status}" if detailed_status else status_info, 
            inline=True
        )
        
        # Add quick action hint with more context
        action_hints = {
            'Issue': 'Click to view issue details and comments',
            'PullRequest': 'Click to review code changes',
            'Release': 'Click to see what\'s new in this release',
            'Discussion': 'Click to join the conversation',
            'SecurityAdvisory': 'Click to view security details'
        }
        
        # Customize action hint based on detailed status and reason
        action_hint = action_hints.get(subject.type, 'Click to view on GitHub')
        
        if subject.type == 'PullRequest' and detailed_status:
            if 'Open' in detailed_status:
                if notification.reason == 'review_requested':
                    action_hint = "Click to review and approve/request changes"
                elif notification.reason == 'mention':
                    action_hint = "Click to see where you were mentioned"
                else:
                    action_hint = "Click to review the code changes"
            elif 'Merged' in detailed_status:
                action_hint = "Click to see the merged changes"
            elif 'Closed' in detailed_status:
                action_hint = "Click to see why it was closed"
                
        elif subject.type == 'Issue' and detailed_status:
            if 'Open' in detailed_status:
                if notification.reason == 'assign':
                    action_hint = "Click to work on this assigned issue"
                elif notification.reason == 'mention':
                    action_hint = "Click to see where you were mentioned"
                else:
                    action_hint = "Click to view issue details and help resolve"
            elif 'Closed' in detailed_status:
                action_hint = "Click to see how it was resolved"
        
        embed.add_field(
            name="💡 Next Step", 
            value=action_hint, 
            inline=False
        )
        
        # Add repository owner avatar as thumbnail
        if repo.owner and repo.owner.avatar_url:
            embed.set_thumbnail(url=repo.owner.avatar_url)
        
        return embed

    async def fetch_and_send_notifications(self):
        """Fetch new GitHub notifications and send them to Discord"""
        try:
            channel = self.bot.get_channel(self.channel_id)
            if not channel:
                logger.error(f"Cannot find Discord channel with ID: {self.channel_id}")
                return 0
            
            # Get last check time
            last_check = self.load_last_check()
            logger.debug(f"Last check time: {last_check}")
            
            # Verify GitHub connection
            try:
                user = self.github.get_user()
                logger.debug(f"GitHub API connection successful for user: {user.login}")
            except Exception as e:
                logger.error(f"GitHub API connection failed: {e}")
                raise
            
            # Fetch notifications
            logger.debug("Fetching GitHub notifications...")
            if last_check:
                notifications = user.get_notifications(
                    all=False,  # Only unread notifications
                    participating=False,  # Include all notifications, not just participating
                    since=last_check
                )
            else:
                notifications = user.get_notifications(
                    all=False,  # Only unread notifications
                    participating=False  # Include all notifications, not just participating
                )
            
            # Convert to list and sort by updated time (newest first)
            notifications_list = list(notifications)
            notifications_list.sort(key=lambda x: x.updated_at, reverse=True)
            
            # Filter out notifications we've already seen
            new_notifications = []
            if last_check:
                new_notifications = [n for n in notifications_list if n.updated_at > last_check]
            else:
                # If no last check, limit to recent notifications to avoid spam
                new_notifications = notifications_list[:10]
            
            logger.info(f"Found {len(new_notifications)} new notifications")
            
            # Log details about what we found
            if new_notifications:
                notification_summary = []
                for notification in new_notifications:
                    summary = f"{notification.subject.type}: {notification.subject.title[:50]}... ({notification.reason})"
                    notification_summary.append(summary)
                logger.info(f"New notifications: {'; '.join(notification_summary[:3])}")
                if len(notification_summary) > 3:
                    logger.info(f"... and {len(notification_summary) - 3} more")
            
            # Send notifications to Discord
            sent_count = 0
            for notification in reversed(new_notifications):  # Send oldest first
                try:
                    embed = self.format_notification_embed(notification)
                    await channel.send(embed=embed)
                    sent_count += 1
                    
                    # Log what we sent
                    logger.info(f"Sent notification: {notification.subject.type} '{notification.subject.title}' from {notification.repository.full_name} (reason: {notification.reason})")
                    
                    # Small delay to avoid rate limiting
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Error sending notification for {notification.subject.title}: {e}")
            
            # Save current time as last check
            self.save_last_check(datetime.now(timezone.utc))
            
            return sent_count
            
        except Exception as e:
            logger.error(f"Error fetching notifications: {e}")
            # Log the full traceback for debugging
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            raise

    @tasks.loop(seconds=300)  # Default interval, will be updated
    async def check_notifications(self):
        """Periodic task to check for new GitHub notifications"""
        try:
            logger.info("Checking for GitHub notifications...")
            count = await self.fetch_and_send_notifications()
            if count > 0:
                logger.info(f"Sent {count} new notifications to Discord")
            else:
                logger.info("No new notifications found")
        except Exception as e:
            logger.error(f"Error in periodic notification check: {e}")
            # Log the full traceback for debugging
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")

    @check_notifications.before_loop
    async def before_check_notifications(self):
        """Wait for bot to be ready before starting the task"""
        await self.bot.wait_until_ready()
        # Update the task interval based on configuration
        self.check_notifications.change_interval(seconds=self.check_interval)
        logger.info(f"Started notification checker with {self.check_interval} second interval")

    def run(self):
        """Start the Discord bot"""
        try:
            self.bot.run(self.discord_token)
        except discord.LoginFailure:
            logger.error("Invalid Discord bot token")
            raise
        except Exception as e:
            logger.error(f"Error starting bot: {e}")
            raise

if __name__ == "__main__":
    try:
        bot = GitHubNotificationBot()
        bot.run()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        raise
