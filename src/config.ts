import dotenv from 'dotenv';
import { Config } from './types';

dotenv.config();

export const config: Config = {
  discordToken: process.env.DISCORD_TOKEN || '',
  githubToken: process.env.GITHUB_TOKEN || '',
  channelId: process.env.DISCORD_CHANNEL_ID || '',
  checkIntervalMinutes: parseInt(process.env.CHECK_INTERVAL_MINUTES || '5'),
  onlyUnread: process.env.ONLY_UNREAD === 'true'
};

export function validateConfig(): void {
  const requiredFields = ['discordToken', 'githubToken', 'channelId'];
  const missingFields = requiredFields.filter(field => !config[field as keyof Config]);
  
  if (missingFields.length > 0) {
    console.error('Missing required environment variables:');
    missingFields.forEach(field => {
      console.error(`- ${field.toUpperCase()}`);
    });
    console.error('Please check your .env file and make sure all required variables are set.');
    process.exit(1);
  }
}
