"""
SummyBot - Discord Conversation Summarizer
A Discord bot that summarizes daily conversations from various channels.
"""

import discord
from discord.ext import commands, tasks
import asyncio
import logging
from datetime import datetime, time
from typing import List, Dict
import os
from dotenv import load_dotenv

from src.summarizer import ConversationSummarizer
from src.config import Config

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('summybot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SummyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True  # This is a privileged intent
        intents.guilds = True
        intents.messages = True
        
        super().__init__(
            command_prefix=Config.COMMAND_PREFIX,  # Keep for backwards compatibility
            intents=intents,
            help_command=None
        )
        
        self.summarizer = ConversationSummarizer()
        
    async def setup_hook(self):
        """Called when the bot is starting up"""
        logger.info("Setting up SummyBot...")
        
        # Start the daily summary task
        self.daily_summary.start()
        
        # Load cogs/extensions
        await self.load_cogs()
        
        # Sync slash commands
        try:
            synced = await self.tree.sync()
            logger.info(f"Synced {len(synced)} slash commands")
        except Exception as e:
            logger.error(f"Failed to sync slash commands: {e}")
        
    async def load_cogs(self):
        """Load bot extensions/cogs"""
        try:
            await self.load_extension('src.commands.summary_commands')
            await self.load_extension('src.commands.config_commands')
            logger.info("Loaded all cogs successfully")
        except Exception as e:
            logger.error(f"Failed to load cogs: {e}")
    
    async def on_ready(self):
        """Called when the bot is ready"""
        logger.info(f'{self.user} has connected to Discord!')
        logger.info(f'Bot is in {len(self.guilds)} guilds')
        
        # Set bot status
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="conversations to summarize"
            )
        )
    
    @tasks.loop(time=time(hour=23, minute=0))  # Run at 11 PM daily
    async def daily_summary(self):
        """Generate and post daily summaries for all configured guilds"""
        logger.info("Starting daily summary generation...")
        
        for guild in self.guilds:
            try:
                await self.generate_guild_summary(guild)
            except Exception as e:
                logger.error(f"Failed to generate summary for guild {guild.name}: {e}")
        
        logger.info("Daily summary generation completed")
    
    async def generate_guild_summary(self, guild: discord.Guild):
        """Generate summary for a specific guild"""
        # Get guild configuration
        guild_config = Config.get_guild_config(guild.id)
        
        if not guild_config:
            logger.info(f"No configuration found for guild {guild.name}")
            return

        # Check if test mode is enabled
        if guild_config.get('test_mode', False):
            test_user_id = guild_config.get('test_user_id')
            if test_user_id:
                test_user = self.get_user(test_user_id)
                if test_user:
                    await self.send_test_summary(guild, test_user, guild_config)
                    return
                else:
                    logger.warning(f"Test user not found for guild {guild.name}")
        
        summary_channel = guild.get_channel(guild_config['summary_channel_id'])
        if not summary_channel:
            logger.warning(f"Summary channel not found for guild {guild.name}")
            return
        
        # Collect messages from monitored channels
        all_messages = []
        for channel_id in guild_config['monitored_channels']:
            channel = guild.get_channel(channel_id)
            if channel:
                messages = await self.collect_daily_messages(channel)
                all_messages.extend(messages)
        
        if not all_messages:
            logger.info(f"No messages to summarize for guild {guild.name}")
            return
        
        # Generate summary
        summary = await self.summarizer.summarize_conversations(all_messages)
        
        # Post summary
        await self.post_summary(summary_channel, summary, guild.name)
    
    async def send_test_summary(self, guild: discord.Guild, test_user: discord.User, guild_config: dict):
        """Send summary to test user's DMs instead of channel"""
        # Collect messages from monitored channels
        all_messages = []
        for channel_id in guild_config['monitored_channels']:
            channel = guild.get_channel(channel_id)
            if channel:
                messages = await self.collect_daily_messages(channel)
                all_messages.extend(messages)
        
        if not all_messages:
            logger.info(f"No messages to summarize for guild {guild.name} (test mode)")
            try:
                await test_user.send(f"🔍 **Test Summary for {guild.name}**\nNo conversations found for today.")
            except discord.Forbidden:
                logger.warning(f"Could not send test summary to user {test_user.display_name}")
            return
        
        # Generate summary
        summary = await self.summarizer.summarize_conversations(all_messages)
        
        # Send to test user's DMs
        embed = discord.Embed(
            title=f"🧪 Test Daily Summary for {guild.name}",
            description=summary,
            color=discord.Color.orange(),
            timestamp=datetime.utcnow()
        )
        
        embed.set_footer(text="Test Mode - Generated by SummyBot")
        
        try:
            await test_user.send(embed=embed)
            logger.info(f"Sent test summary to {test_user.display_name} for {guild.name}")
        except discord.Forbidden:
            logger.warning(f"Could not send test summary to user {test_user.display_name}")
    
    async def collect_daily_messages(self, channel: discord.TextChannel) -> List[discord.Message]:
        """Collect messages from the last 24 hours in a channel"""
        messages = []
        now = datetime.utcnow()
        yesterday = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        try:
            async for message in channel.history(after=yesterday, limit=None):
                if not message.author.bot:  # Skip bot messages
                    messages.append(message)
        except discord.Forbidden:
            logger.warning(f"No permission to read messages in {channel.name}")
        except Exception as e:
            logger.error(f"Error collecting messages from {channel.name}: {e}")
        
        return messages
    
    async def post_summary(self, channel: discord.TextChannel, summary: str, guild_name: str):
        """Post the generated summary to the summary channel"""
        embed = discord.Embed(
            title=f"📝 Daily Summary for {guild_name}",
            description=summary,
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        embed.set_footer(text="Generated by SummyBot")
        
        try:
            await channel.send(embed=embed)
            logger.info(f"Posted daily summary to {channel.name} in {guild_name}")
        except Exception as e:
            logger.error(f"Failed to post summary to {channel.name}: {e}")

def main():
    """Main entry point"""
    bot = SummyBot()
    
    # Check for bot token
    token = os.getenv('DISCORD_BOT_TOKEN')
    if not token:
        logger.error("DISCORD_BOT_TOKEN environment variable is not set!")
        return
    
    try:
        bot.run(token)
    except discord.LoginFailure:
        logger.error("Invalid bot token provided!")
    except Exception as e:
        logger.error(f"Bot crashed: {e}")

if __name__ == "__main__":
    main()
