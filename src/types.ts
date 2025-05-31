export interface GitHubNotification {
  id: string;
  unread: boolean;
  reason: string;
  updated_at: string;
  last_read_at: string | null;
  subject: {
    title: string;
    url: string;
    latest_comment_url: string;
    type: string;
  };
  repository: {
    id: number;
    name: string;
    full_name: string;
    html_url: string;
    description: string | null;
    private: boolean;
  };
  url: string;
  subscription_url: string;
}

export interface Config {
  discordToken: string;
  githubToken: string;
  channelId: string;
  checkIntervalMinutes: number;
  onlyUnread: boolean;
}
