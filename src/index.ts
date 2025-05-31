import * as cron from 'node-cron';
import { config, validateConfig } from './config';
import { GitHubService } from './github-service';
import { DiscordService } from './discord-service';
import { GitHubNotification } from './types';

class GitHubDiscordBot {
  private githubService: GitHubService;
  private discordService: DiscordService;
  private processedNotifications: Set<string> = new Set();

  constructor() {
    validateConfig();
    
    this.githubService = new GitHubService(config.githubToken);
    this.discordService = new DiscordService(config.discordToken, config.channelId);
  }

  async start(): Promise<void> {
    console.log('Starting GitHub Discord Bot...');
    
    // Wait for Discord client to be ready
    await this.discordService.waitForReady();
    console.log('Discord client is ready!');

    // Initial check
    console.log('Performing initial notification check...');
    await this.checkNotifications();

    // Schedule periodic checks
    const cronExpression = `*/${config.checkIntervalMinutes} * * * *`;
    console.log(`Scheduling checks every ${config.checkIntervalMinutes} minutes...`);
    
    cron.schedule(cronExpression, async () => {
      console.log('Checking for new GitHub notifications...');
      await this.checkNotifications();
    });

    console.log('Bot is now running! Press Ctrl+C to stop.');
  }

  private async checkNotifications(): Promise<void> {
    try {
      const notifications = await this.githubService.getNotifications(config.onlyUnread);
      console.log(`Found ${notifications.length} notifications`);

      // Filter out notifications we've already processed
      const newNotifications = notifications.filter(notification => 
        !this.processedNotifications.has(notification.id)
      );

      if (newNotifications.length === 0) {
        console.log('No new notifications to process');
        return;
      }

      console.log(`Processing ${newNotifications.length} new notifications`);

      for (const notification of newNotifications) {
        await this.processNotification(notification);
        this.processedNotifications.add(notification.id);
        
        // Add a small delay between messages to avoid rate limiting
        await this.sleep(1000);
      }

      // Clean up old processed notifications to prevent memory growth
      if (this.processedNotifications.size > 1000) {
        const notificationIds = Array.from(this.processedNotifications);
        const toKeep = notificationIds.slice(-500); // Keep last 500
        this.processedNotifications = new Set(toKeep);
      }

    } catch (error) {
      console.error('Error checking notifications:', error);
    }
  }

  private async processNotification(notification: GitHubNotification): Promise<void> {
    try {
      const notificationUrl = this.githubService.getNotificationUrl(notification);
      
      console.log(`Sending notification: ${notification.subject.title} from ${notification.repository.full_name}`);
      await this.discordService.sendNotification(notification, notificationUrl);
      
    } catch (error) {
      console.error(`Error processing notification ${notification.id}:`, error);
    }
  }

  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  async stop(): Promise<void> {
    console.log('Stopping bot...');
    await this.discordService.destroy();
    process.exit(0);
  }
}

// Handle graceful shutdown
process.on('SIGINT', async () => {
  console.log('\nReceived SIGINT. Gracefully shutting down...');
  process.exit(0);
});

process.on('SIGTERM', async () => {
  console.log('\nReceived SIGTERM. Gracefully shutting down...');
  process.exit(0);
});

// Start the bot
const bot = new GitHubDiscordBot();
bot.start().catch(error => {
  console.error('Failed to start bot:', error);
  process.exit(1);
});
