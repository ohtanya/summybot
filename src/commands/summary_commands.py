"""
Summary-related commands for SummyBot
"""

import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timedelta
import logging

from ..summarizer import ConversationSummarizer
from ..config import Config

logger = logging.getLogger(__name__)

class SummaryCommands(commands.Cog):
    """Commands for generating and managing conversation summaries"""
    
    def __init__(self, bot):
        self.bot = bot
        self.summarizer = ConversationSummarizer()
    
    @app_commands.command(name='private_summary', description='Generate a summary and send it to your DMs')
    @app_commands.describe(
        channel='Channel to summarize (defaults to current channel)',
        hours='Number of hours to look back (default: 24, max: 168)'
    )
    async def private_summary(
        self, 
        interaction: discord.Interaction, 
        channel: discord.TextChannel = None, 
        hours: int = 24
    ):
        """Generate a summary and send it privately to the user's DMs"""
        if not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message("❌ You need 'Manage Messages' permission to use this command.", ephemeral=True)
            return
            
        if channel is None:
            channel = interaction.channel
        
        if hours > 168:  # Limit to 1 week
            await interaction.response.send_message("❌ Cannot summarize more than 168 hours (1 week)", ephemeral=True)
            return
        
        await interaction.response.send_message(f"🔄 Generating private summary for {channel.mention} (last {hours} hours)...", ephemeral=True)
        
        try:
            # Collect messages from the specified timeframe
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            messages = []
            
            async for message in channel.history(after=cutoff_time, limit=1000):
                if not message.author.bot:
                    messages.append(message)
            
            if not messages:
                await interaction.followup.send(f"❌ No messages found in {channel.mention} for the last {hours} hours", ephemeral=True)
                return
            
            # Generate summary
            summary = await self.summarizer.summarize_conversations(messages)
            
            # Create embed
            embed = discord.Embed(
                title=f"📊 Private Summary for #{channel.name}",
                color=discord.Color.blue(),
                timestamp=datetime.utcnow()
            )
            
            # Add summary as main description with better formatting
            formatted_summary = f"**Channel Activity:**\n{summary}\n"
            embed.description = formatted_summary
            
            embed.add_field(
                name="📍 Server",
                value=interaction.guild.name,
                inline=True
            )
            
            embed.add_field(
                name="⏰ Timeframe", 
                value=f"Last {hours} hours",
                inline=True
            )
            
            embed.add_field(
                name="📈 Messages Analyzed",
                value=f"{len(messages)} messages",
                inline=True
            )
            
            embed.set_footer(text=f"Private summary requested by {interaction.user.display_name}")
            
            # Send to user's DMs
            try:
                await interaction.user.send(embed=embed)
                await interaction.followup.send("✅ Summary sent to your DMs!", ephemeral=True)
            except discord.Forbidden:
                await interaction.followup.send("❌ I couldn't send you a DM. Please check your privacy settings and try again.", ephemeral=True)
            
        except discord.Forbidden:
            await interaction.followup.send(f"❌ I don't have permission to read messages in {channel.mention}", ephemeral=True)
        except Exception as e:
            logger.error(f"Error generating private summary: {e}")
            await interaction.followup.send("❌ An error occurred while generating the summary", ephemeral=True)

    @app_commands.command(name='summary', description='Generate a summary for a channel')
    @app_commands.describe(
        channel='Channel to summarize (defaults to current channel)',
        hours='Number of hours to look back (default: 24, max: 168)'
    )
    async def slash_summary(
        self, 
        interaction: discord.Interaction, 
        channel: discord.TextChannel = None, 
        hours: int = 24
    ):
        """Generate a manual summary for a channel"""
        if not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message("❌ You need 'Manage Messages' permission to use this command.", ephemeral=True)
            return
            
        if channel is None:
            channel = interaction.channel
        
        if hours > 168:  # Limit to 1 week
            await interaction.response.send_message("❌ Cannot summarize more than 168 hours (1 week)", ephemeral=True)
            return
        
        await interaction.response.send_message(f"🔄 Generating summary for {channel.mention} (last {hours} hours)...", ephemeral=True)
        
        try:
            # Collect messages from the specified timeframe
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            messages = []
            
            async for message in channel.history(after=cutoff_time, limit=1000):
                if not message.author.bot:
                    messages.append(message)
            
            if not messages:
                await interaction.followup.send(f"❌ No messages found in {channel.mention} for the last {hours} hours", ephemeral=True)
                return
            
            # Generate summary
            summary = await self.summarizer.summarize_conversations(messages)
            
            # Create embed
            embed = discord.Embed(
                title=f"📊 Summary for {channel.name}",
                description=summary,
                color=discord.Color.green(),
                timestamp=datetime.utcnow()
            )
            
            embed.add_field(
                name="Timeframe",
                value=f"Last {hours} hours",
                inline=True
            )
            
            embed.add_field(
                name="Messages Analyzed",
                value=str(len(messages)),
                inline=True
            )
            
            embed.set_footer(text=f"Requested by {interaction.user.display_name}")
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except discord.Forbidden:
            await interaction.followup.send(f"❌ I don't have permission to read messages in {channel.mention}", ephemeral=True)
        except Exception as e:
            logger.error(f"Error generating manual summary: {e}")
            await interaction.followup.send("❌ An error occurred while generating the summary", ephemeral=True)
    
    @app_commands.command(name='daily', description='Force generate today\'s daily summary')
    async def slash_daily(self, interaction: discord.Interaction):
        """Force generate today's daily summary for all monitored channels"""
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("❌ You need 'Manage Server' permission to use this command.", ephemeral=True)
            return
            
        await interaction.response.send_message("🔄 Generating daily summary for all monitored channels...", ephemeral=True)
        
        try:
            await self.bot.generate_guild_summary(interaction.guild)
            await interaction.followup.send("✅ Daily summary generated successfully!", ephemeral=True)
        except Exception as e:
            logger.error(f"Error generating forced daily summary: {e}")
            await interaction.followup.send("❌ An error occurred while generating the daily summary", ephemeral=True)
    
    @app_commands.command(name='test_summary', description='Test summarization with recent messages')
    async def slash_test_summary(self, interaction: discord.Interaction):
        """Test the summarization with recent messages from current channel"""
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ You need 'Administrator' permission to use this command.", ephemeral=True)
            return
            
        await interaction.response.send_message("🧪 Testing summarization with recent messages...", ephemeral=True)
        
        try:
            # Get last 50 messages from current channel
            messages = []
            async for message in interaction.channel.history(limit=50):
                if not message.author.bot:
                    messages.append(message)
            
            if len(messages) < 5:
                await interaction.followup.send("❌ Not enough messages to test summarization", ephemeral=True)
                return
            
            # Generate test summary
            summary = await self.summarizer.summarize_conversations(messages)
            
            embed = discord.Embed(
                title="🧪 Test Summary",
                description=summary,
                color=discord.Color.orange(),
                timestamp=datetime.utcnow()
            )
            
            embed.add_field(
                name="Test Messages",
                value=str(len(messages)),
                inline=True
            )
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error in test summary: {e}")
            await interaction.followup.send("❌ An error occurred during the test", ephemeral=True)

async def setup(bot):
    await bot.add_cog(SummaryCommands(bot))
