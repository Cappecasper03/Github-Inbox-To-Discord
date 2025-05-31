import { Client, GatewayIntentBits, TextChannel, EmbedBuilder } from 'discord.js';
import { GitHubNotification } from './types';

export class DiscordService {
  private client: Client;
  private channelId: string;

  constructor(token: string, channelId: string) {
    this.channelId = channelId;
    this.client = new Client({
      intents: [
        GatewayIntentBits.Guilds,
        GatewayIntentBits.GuildMessages
      ]
    });

    this.client.login(token);
  }

  async waitForReady(): Promise<void> {
    return new Promise((resolve) => {
      if (this.client.isReady()) {
        resolve();
      } else {
        this.client.once('ready', () => {
          console.log(`Discord bot logged in as ${this.client.user?.tag}`);
          resolve();
        });
      }
    });
  }

  async sendNotification(notification: GitHubNotification, notificationUrl: string): Promise<void> {
    try {
      const channel = await this.client.channels.fetch(this.channelId) as TextChannel;
      
      if (!channel) {
        throw new Error(`Channel with ID ${this.channelId} not found`);
      }

      const embed = this.createNotificationEmbed(notification, notificationUrl);
      await channel.send({ embeds: [embed] });
    } catch (error) {
      console.error('Error sending Discord message:', error);
      throw error;
    }
  }

  private createNotificationEmbed(notification: GitHubNotification, notificationUrl: string): EmbedBuilder {
    const embed = new EmbedBuilder()
      .setTitle(notification.subject.title)
      .setURL(notificationUrl)
      .setDescription(`**Repository:** ${notification.repository.full_name}`)
      .setColor(this.getColorForType(notification.subject.type))
      .addFields([
        {
          name: 'Type',
          value: this.formatNotificationType(notification.subject.type),
          inline: true
        },
        {
          name: 'Reason',
          value: this.formatReason(notification.reason),
          inline: true
        },
        {
          name: 'Status',
          value: notification.unread ? '🔴 Unread' : '✅ Read',
          inline: true
        }
      ])
      .setTimestamp(new Date(notification.updated_at))
      .setFooter({
        text: 'GitHub Notification',
        iconURL: 'https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png'
      });

    // Add repository description if available
    if (notification.repository.description) {
      embed.addFields([{
        name: 'Repository Description',
        value: notification.repository.description.length > 100 
          ? notification.repository.description.substring(0, 97) + '...'
          : notification.repository.description,
        inline: false
      }]);
    }

    return embed;
  }

  private getColorForType(type: string): number {
    switch (type.toLowerCase()) {
      case 'issue':
        return 0x28a745; // Green
      case 'pullrequest':
        return 0x0366d6; // Blue
      case 'commit':
        return 0x6f42c1; // Purple
      case 'release':
        return 0xfd7e14; // Orange
      default:
        return 0x6c757d; // Gray
    }
  }

  private formatNotificationType(type: string): string {
    switch (type.toLowerCase()) {
      case 'issue':
        return '🐛 Issue';
      case 'pullrequest':
        return '🔀 Pull Request';
      case 'commit':
        return '📝 Commit';
      case 'release':
        return '🚀 Release';
      default:
        return `📋 ${type}`;
    }
  }

  private formatReason(reason: string): string {
    switch (reason) {
      case 'assign':
        return '👤 Assigned';
      case 'author':
        return '✍️ Author';
      case 'comment':
        return '💬 Comment';
      case 'invitation':
        return '📨 Invitation';
      case 'manual':
        return '👁️ Manual';
      case 'mention':
        return '📢 Mention';
      case 'review_requested':
        return '👀 Review Requested';
      case 'security_alert':
        return '🚨 Security Alert';
      case 'state_change':
        return '🔄 State Change';
      case 'subscribed':
        return '🔔 Subscribed';
      case 'team_mention':
        return '👥 Team Mention';
      default:
        return reason;
    }
  }

  async destroy(): Promise<void> {
    await this.client.destroy();
  }
}
