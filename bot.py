import discord
from discord.ext import commands, tasks
import asyncio
import os
import json
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
        
        self.github = Github(self.github_token)
        
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
                
            await ctx.send("🔍 Checking for GitHub notifications...")
            try:
                count = await self.fetch_and_send_notifications()
                if count > 0:
                    await ctx.send(f"✅ Sent {count} new notifications!")
                else:
                    await ctx.send("📭 No new notifications found.")
            except Exception as e:
                logger.error(f"Error during manual check: {e}")
                await ctx.send(f"❌ Error checking notifications: {str(e)}")
                
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
                    color=discord.Color.blue(),
                    timestamp=datetime.now(timezone.utc)
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
        
        embed = discord.Embed(
            title=f"{notification_info['emoji']} {subject.title}",
            url=subject.url.replace('api.github.com/repos', 'github.com').replace('/pulls/', '/pull/'),
            color=notification_info['color'],
            timestamp=datetime.now(timezone.utc)
        )
        
        embed.add_field(name="Repository", value=f"[{repo.full_name}]({repo.html_url})", inline=True)
        embed.add_field(name="Type", value=subject.type, inline=True)
        embed.add_field(name="Reason", value=notification.reason.replace('_', ' ').title(), inline=True)
        
        if notification.updated_at:
            embed.add_field(
                name="Updated", 
                value=f"<t:{int(notification.updated_at.timestamp())}:R>", 
                inline=True
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
            
            # Fetch notifications
            notifications = self.github.get_user().get_notifications(
                all=False,  # Only unread notifications
                participating=False,  # Include all notifications, not just participating
                since=last_check if last_check else None
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
            
            # Send notifications to Discord
            sent_count = 0
            for notification in reversed(new_notifications):  # Send oldest first
                try:
                    embed = self.format_notification_embed(notification)
                    await channel.send(embed=embed)
                    sent_count += 1
                    
                    # Small delay to avoid rate limiting
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Error sending notification for {notification.subject.title}: {e}")
            
            # Save current time as last check
            self.save_last_check(datetime.now(timezone.utc))
            
            return sent_count
            
        except Exception as e:
            logger.error(f"Error fetching notifications: {e}")
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
