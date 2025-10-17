"""
Summary-related commands for SummyBot
"""

import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timedelta, timezone
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
            # Collect messages from the specified timeframe - use timezone-aware datetime
            current_time = datetime.now(timezone.utc)
            cutoff_time = current_time - timedelta(hours=hours)
            messages = []
            
            print(f"DEBUG: Looking for messages after {cutoff_time} in channel {channel.name}")
            print(f"DEBUG: Current time is {current_time}")
            
            total_messages = 0
            bot_messages = 0
            async for message in channel.history(after=cutoff_time, limit=1000):
                total_messages += 1
                if message.author.bot:
                    bot_messages += 1
                else:
                    messages.append(message)
            
            print(f"DEBUG: Found {total_messages} total messages, {bot_messages} bot messages, {len(messages)} user messages")
            
            if not messages:
                await interaction.followup.send(f"❌ No messages found in {channel.mention} for the last {hours} hours", ephemeral=True)
                return
            
            # Generate summary
            summary = await self.summarizer.summarize_conversations(messages)
            
            # Create embed
            embed = discord.Embed(
                title=f"📊 Private Summary for #{channel.name}",
                color=discord.Color.blue(),
                timestamp=datetime.now(timezone.utc)
            )
            
            # Check if summary is too long for embed description (2048 char limit)
            if len(summary) > 1900:  # Leave some room for formatting
                # Split long summaries
                summary_parts = summary.split('\n\n')
                embed.description = summary_parts[0][:1900] + "..."
                
                # Add remaining parts as fields if possible
                for i, part in enumerate(summary_parts[1:], 1):
                    if len(embed.fields) < 10 and len(part) < 1024:  # Field value limit
                        embed.add_field(
                            name=f"📝 Part {i+1}",
                            value=part,
                            inline=False
                        )
            else:
                embed.description = summary
            
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
            # Collect messages from the specified timeframe - use timezone-aware datetime
            current_time = datetime.now(timezone.utc)
            cutoff_time = current_time - timedelta(hours=hours)
            messages = []
            
            print(f"DEBUG: Looking for messages after {cutoff_time} in channel {channel.name}")
            print(f"DEBUG: Current time is {current_time}")
            
            total_messages = 0
            bot_messages = 0
            async for message in channel.history(after=cutoff_time, limit=1000):
                total_messages += 1
                if message.author.bot:
                    bot_messages += 1
                else:
                    messages.append(message)
            
            print(f"DEBUG: Found {total_messages} total messages, {bot_messages} bot messages, {len(messages)} user messages")
            
            if not messages:
                await interaction.followup.send(f"❌ No messages found in {channel.mention} for the last {hours} hours", ephemeral=True)
                return
            
            # Generate summary
            summary = await self.summarizer.summarize_conversations(messages)
            
            # Create embed
            embed = discord.Embed(
                title=f"📊 Summary for {channel.name}",
                color=discord.Color.green(),
                timestamp=datetime.now(timezone.utc)
            )
            
            # Check if summary is too long for embed description (2048 char limit)
            if len(summary) > 1900:  # Leave some room for formatting
                # Split long summaries
                summary_parts = summary.split('\n\n')
                embed.description = summary_parts[0][:1900] + "..."
                
                # Add remaining parts as fields if possible
                for i, part in enumerate(summary_parts[1:], 1):
                    if len(embed.fields) < 10 and len(part) < 1024:  # Field value limit
                        embed.add_field(
                            name=f"📝 Part {i+1}",
                            value=part,
                            inline=False
                        )
            else:
                embed.description = summary
            
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
    @app_commands.command(name='summy', description='Generate a summary with a custom question/focus')
    @app_commands.describe(
        question='Specific question or topic to focus on (e.g., "what happened when people talked about the ghost dick book?")',
        channel='Channel to summarize (defaults to current channel)',
        hours='Number of hours to look back (default: 24, max: 168)'
    )
    async def summy(
        self, 
        interaction: discord.Interaction, 
        question: str,
        channel: discord.TextChannel = None, 
        hours: int = 24
    ):
        """Generate a summary focused on a specific question or topic"""
        if not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message("❌ You need 'Manage Messages' permission to use this command.", ephemeral=True)
            return
            
        if channel is None:
            channel = interaction.channel
        
        if hours > 168:  # Limit to 1 week
            await interaction.response.send_message("❌ Cannot summarize more than 168 hours (1 week)", ephemeral=True)
            return
        
        await interaction.response.send_message(f"🔍 Generating summy for {channel.mention} focused on: \"{question}\"...", ephemeral=True)
        
        try:
            # Collect messages from the specified timeframe - use timezone-aware datetime
            current_time = datetime.now(timezone.utc)
            after_time = current_time - timedelta(hours=hours)
            
            print(f"DEBUG: Collecting messages after {after_time} (UTC)")
            
            messages = []
            async for message in channel.history(after=after_time, limit=None):
                if not message.author.bot:  # Skip bot messages
                    messages.append(message)
                    
            print(f"DEBUG: Found {len(messages)} messages")
            
            if not messages:
                await interaction.followup.send(f"❌ No messages found in {channel.mention} for the last {hours} hours", ephemeral=True)
                return
            
            # Generate focused answer with custom prompt
            summary = await self.summarizer.summarize_conversations(messages, custom_prompt=question)
            
            # Create simple embed for the focused answer
            embed = discord.Embed(
                title=f"🔍 Summy",
                description=f"**Question:** {question}\n\n**Answer:**\n{summary}",
                color=discord.Color.purple(),
                timestamp=datetime.utcnow()
            )
            
            embed.add_field(
                name="📍 Channel",
                value=channel.mention,
                inline=True
            )
            
            embed.add_field(
                name="📈 Messages Scanned",
                value=f"{len(messages)} messages",
                inline=True
            )
            
            embed.set_footer(text=f"Summy • Last {hours} hours")
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error in summy: {e}")
            await interaction.followup.send("❌ An error occurred during the summy generation", ephemeral=True)

    @app_commands.command(name='preview_summary', description='Generate a summary and choose where to send it')
    @app_commands.describe(
        channel='Channel to summarize (defaults to current channel)',
        hours='Number of hours to look back (default: 24, max: 168)'
    )
    async def preview_summary(
        self, 
        interaction: discord.Interaction, 
        channel: discord.TextChannel = None, 
        hours: int = 24
    ):
        """Generate a summary preview with options to send it different places"""
        if not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message("❌ You need 'Manage Messages' permission to use this command.", ephemeral=True)
            return
            
        if channel is None:
            channel = interaction.channel
        
        if hours > 168:  # Limit to 1 week
            await interaction.response.send_message("❌ Cannot summarize more than 168 hours (1 week)", ephemeral=True)
            return
        
        await interaction.response.send_message(f"🔄 Generating summary preview for {channel.mention} (last {hours} hours)...", ephemeral=True)
        
        try:
            # Collect messages from the specified timeframe
            current_time = datetime.now(timezone.utc)
            cutoff_time = current_time - timedelta(hours=hours)
            messages = []
            
            total_messages = 0
            bot_messages = 0
            async for message in channel.history(after=cutoff_time, limit=1000):
                total_messages += 1
                if message.author.bot:
                    bot_messages += 1
                else:
                    messages.append(message)
            
            if not messages:
                await interaction.followup.send(f"❌ No messages found in {channel.mention} for the last {hours} hours", ephemeral=True)
                return
            
            # Generate summary
            summary = await self.summarizer.summarize_conversations(messages)
            
            # Create preview embed
            embed = discord.Embed(
                title=f"📋 Summary Preview for #{channel.name}",
                color=discord.Color.gold(),
                timestamp=datetime.now(timezone.utc)
            )
            
            # Handle long summaries
            if len(summary) > 1900:
                summary_parts = summary.split('\n\n')
                embed.description = summary_parts[0][:1900] + "..."
                
                for i, part in enumerate(summary_parts[1:], 1):
                    if len(embed.fields) < 10 and len(part) < 1024:
                        embed.add_field(
                            name=f"📝 Part {i+1}",
                            value=part,
                            inline=False
                        )
            else:
                embed.description = summary
            
            embed.add_field(
                name="📊 Stats",
                value=f"**Messages:** {len(messages)}\n**Timeframe:** Last {hours} hours",
                inline=True
            )
            
            embed.set_footer(text="Choose where to send this summary:")
            
            # Create view with buttons
            view = SummaryDestinationView(embed, channel, len(messages), hours)
            
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error generating summary preview: {e}")
            await interaction.followup.send("❌ An error occurred while generating the summary preview", ephemeral=True)


class SummaryDestinationView(discord.ui.View):
    """View with buttons to choose where to send the summary"""
    
    def __init__(self, summary_embed: discord.Embed, channel: discord.TextChannel, message_count: int, hours: int):
        super().__init__(timeout=300)  # 5 minute timeout
        self.summary_embed = summary_embed
        self.channel = channel
        self.message_count = message_count
        self.hours = hours
    
    @discord.ui.button(label='Send to Channel', style=discord.ButtonStyle.primary, emoji='📢')
    async def send_to_channel(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Send the summary to the current channel"""
        try:
            # Update embed for public posting
            public_embed = discord.Embed(
                title=f"📊 Summary for #{self.channel.name}",
                description=self.summary_embed.description,
                color=discord.Color.green(),
                timestamp=datetime.now(timezone.utc)
            )
            
            # Copy any fields from the original embed
            for field in self.summary_embed.fields:
                if field.name != "📊 Stats":  # Skip the stats field, we'll recreate it
                    public_embed.add_field(name=field.name, value=field.value, inline=field.inline)
            
            public_embed.add_field(
                name="Timeframe",
                value=f"Last {self.hours} hours",
                inline=True
            )
            
            public_embed.add_field(
                name="Messages Analyzed",
                value=str(self.message_count),
                inline=True
            )
            
            public_embed.set_footer(text=f"Requested by {interaction.user.display_name}")
            
            # Send to the channel
            await self.channel.send(embed=public_embed)
            
            # Update the preview message
            await interaction.response.edit_message(
                content="✅ Summary sent to the channel!",
                embed=None,
                view=None
            )
            
        except Exception as e:
            logger.error(f"Error sending summary to channel: {e}")
            await interaction.response.send_message("❌ Failed to send summary to channel", ephemeral=True)
    
    @discord.ui.button(label='Send to DMs', style=discord.ButtonStyle.secondary, emoji='📬')
    async def send_to_dms(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Send the summary to user's DMs"""
        try:
            # Update embed for DM
            dm_embed = discord.Embed(
                title=f"📊 Private Summary for #{self.channel.name}",
                description=self.summary_embed.description,
                color=discord.Color.blue(),
                timestamp=datetime.now(timezone.utc)
            )
            
            # Copy any fields from the original embed
            for field in self.summary_embed.fields:
                if field.name != "📊 Stats":
                    dm_embed.add_field(name=field.name, value=field.value, inline=field.inline)
            
            dm_embed.add_field(
                name="📍 Server",
                value=interaction.guild.name,
                inline=True
            )
            
            dm_embed.add_field(
                name="⏰ Timeframe", 
                value=f"Last {self.hours} hours",
                inline=True
            )
            
            dm_embed.add_field(
                name="📈 Messages Analyzed",
                value=f"{self.message_count} messages",
                inline=True
            )
            
            dm_embed.set_footer(text=f"Private summary from {interaction.guild.name}")
            
            # Send to user's DMs
            await interaction.user.send(embed=dm_embed)
            
            # Update the preview message
            await interaction.response.edit_message(
                content="✅ Summary sent to your DMs!",
                embed=None,
                view=None
            )
            
        except discord.Forbidden:
            await interaction.response.send_message("❌ I couldn't send you a DM. Please check your privacy settings.", ephemeral=True)
        except Exception as e:
            logger.error(f"Error sending summary to DMs: {e}")
            await interaction.response.send_message("❌ Failed to send summary to DMs", ephemeral=True)
    
    @discord.ui.button(label='Cancel', style=discord.ButtonStyle.danger, emoji='❌')
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Cancel and delete the preview"""
        await interaction.response.edit_message(
            content="❌ Summary preview cancelled.",
            embed=None,
            view=None
        )
    
    async def on_timeout(self):
        """Called when the view times out"""
        # Disable all buttons
        for item in self.children:
            item.disabled = True


async def setup(bot):
    await bot.add_cog(SummaryCommands(bot))
