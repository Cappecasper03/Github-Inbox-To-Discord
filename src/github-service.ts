import axios from 'axios';
import { GitHubNotification } from './types';

export class GitHubService {
  private readonly token: string;
  private readonly baseURL = 'https://api.github.com';
  private lastChecked: Date | null = null;

  constructor(token: string) {
    this.token = token;
  }

  async getNotifications(onlyUnread = true): Promise<GitHubNotification[]> {
    try {
      const params: any = {
        all: !onlyUnread,
        participating: false,
        per_page: 50
      };

      // If we have a last checked time, only get notifications since then
      if (this.lastChecked && onlyUnread) {
        params.since = this.lastChecked.toISOString();
      }

      const response = await axios.get(`${this.baseURL}/notifications`, {
        headers: {
          'Authorization': `token ${this.token}`,
          'Accept': 'application/vnd.github.v3+json',
          'User-Agent': 'GitHub-Discord-Bot'
        },
        params
      });

      this.lastChecked = new Date();
      return response.data;
    } catch (error) {
      console.error('Error fetching GitHub notifications:', error);
      throw error;
    }
  }

  async markAsRead(notificationId: string): Promise<void> {
    try {
      await axios.patch(`${this.baseURL}/notifications/threads/${notificationId}`, {}, {
        headers: {
          'Authorization': `token ${this.token}`,
          'Accept': 'application/vnd.github.v3+json',
          'User-Agent': 'GitHub-Discord-Bot'
        }
      });
    } catch (error) {
      console.error(`Error marking notification ${notificationId} as read:`, error);
      throw error;
    }
  }

  getNotificationUrl(notification: GitHubNotification): string {
    // Extract the actual URL from the subject URL
    const subjectUrl = notification.subject.url;
    if (subjectUrl) {
      // Convert API URL to web URL
      const urlParts = subjectUrl.split('/');
      const repoPath = `${urlParts[4]}/${urlParts[5]}`;
      const type = notification.subject.type.toLowerCase();
      const number = urlParts[urlParts.length - 1];
      
      if (type === 'issue') {
        return `https://github.com/${repoPath}/issues/${number}`;
      } else if (type === 'pullrequest') {
        return `https://github.com/${repoPath}/pull/${number}`;
      } else if (type === 'commit') {
        return `https://github.com/${repoPath}/commit/${number}`;
      } else if (type === 'release') {
        return `https://github.com/${repoPath}/releases/tag/${number}`;
      }
    }
    
    // Fallback to repository URL
    return notification.repository.html_url;
  }
}
