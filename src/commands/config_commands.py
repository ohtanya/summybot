"""
Configuration commands for SummyBot
"""

import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime
import logging

from ..config import Config

logger = logging.getLogger(__name__)

class ConfigCommands(commands.Cog):
    """Commands for configuring the bot's behavior"""
    
    def __init__(self, bot):
        self.bot = bot
    
    config_group = app_commands.Group(name='config', description='Configure SummyBot settings')
    
    @config_group.command(name='show', description='Show current server configuration')
    async def slash_config_show(self, interaction: discord.Interaction):
        """Show current configuration for this server"""
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("❌ You need 'Manage Server' permission to use this command.", ephemeral=True)
            return
            
        guild_config = Config.get_guild_config(interaction.guild.id)
        
        embed = discord.Embed(
            title=f"⚙️ Configuration for {interaction.guild.name}",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        if not guild_config:
            embed.description = "No configuration found. Use `/config setup` to get started."
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Monitored channels
        monitored_channels = []
        for channel_id in guild_config.get('monitored_channels', []):
            channel = interaction.guild.get_channel(channel_id)
            if channel:
                monitored_channels.append(channel.mention)
        
        embed.add_field(
            name="Monitored Channels",
            value="\n".join(monitored_channels) if monitored_channels else "None",
            inline=False
        )
        
        # Summary channel
        summary_channel_id = guild_config.get('summary_channel_id')
        summary_channel = interaction.guild.get_channel(summary_channel_id) if summary_channel_id else None
        
        embed.add_field(
            name="Summary Channel",
            value=summary_channel.mention if summary_channel else "Not set",
            inline=False
        )
        
        embed.set_footer(text="Use /config commands to modify settings")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @config_group.command(name='setup', description='Interactive setup guide for SummyBot')
    async def slash_config_setup(self, interaction: discord.Interaction):
        """Interactive setup for the bot configuration"""
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("❌ You need 'Manage Server' permission to use this command.", ephemeral=True)
            return
            
        embed = discord.Embed(
            title="🛠️ SummyBot Setup",
            description="Let's set up your server configuration!",
            color=discord.Color.green()
        )
        
        embed.add_field(
            name="Step 1",
            value="Set a summary channel with `/config summary_channel`",
            inline=False
        )
        
        embed.add_field(
            name="Step 2",
            value="Add channels to monitor with `/config add_channel`",
            inline=False
        )
        
        embed.add_field(
            name="Step 3",
            value="Test with `/test_summary` to see if everything works",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @config_group.command(name='summary_channel', description='Set the channel where daily summaries will be posted')
    @app_commands.describe(channel='The channel where summaries will be posted')
    async def slash_set_summary_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        """Set the channel where daily summaries will be posted"""
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("❌ You need 'Manage Server' permission to use this command.", ephemeral=True)
            return
            
        # Check if bot has permissions in the channel
        bot_member = channel.guild.get_member(self.bot.user.id)
        permissions = channel.permissions_for(bot_member)
        
        if not permissions.send_messages or not permissions.embed_links:
            await interaction.response.send_message(f"❌ I don't have permission to send messages/embeds in {channel.mention}", ephemeral=True)
            return
        
        Config.set_summary_channel(interaction.guild.id, channel.id)
        
        embed = discord.Embed(
            title="✅ Summary Channel Set",
            description=f"Daily summaries will be posted to {channel.mention}",
            color=discord.Color.green()
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @config_group.command(name='add_channel', description='Add a channel to be monitored for daily summaries')
    @app_commands.describe(channel='The channel to monitor for conversations')
    async def slash_add_monitored_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        """Add a channel to be monitored for daily summaries"""
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("❌ You need 'Manage Server' permission to use this command.", ephemeral=True)
            return
            
        # Check if bot has permissions in the channel
        bot_member = channel.guild.get_member(self.bot.user.id)
        permissions = channel.permissions_for(bot_member)
        
        if not permissions.read_message_history:
            await interaction.response.send_message(f"❌ I don't have permission to read message history in {channel.mention}", ephemeral=True)
            return
        
        Config.add_monitored_channel(interaction.guild.id, channel.id)
        
        embed = discord.Embed(
            title="✅ Channel Added",
            description=f"{channel.mention} will be included in daily summaries",
            color=discord.Color.green()
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @config_group.command(name='remove_channel', description='Remove a channel from being monitored')
    @app_commands.describe(channel='The channel to remove from monitoring')
    async def slash_remove_monitored_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        """Remove a channel from being monitored"""
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("❌ You need 'Manage Server' permission to use this command.", ephemeral=True)
            return
            
        Config.remove_monitored_channel(interaction.guild.id, channel.id)
        
        embed = discord.Embed(
            title="✅ Channel Removed",
            description=f"{channel.mention} will no longer be included in daily summaries",
            color=discord.Color.green()
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @config_group.command(name='test_mode', description='Toggle test mode (summaries sent to your DMs only)')
    async def test_mode(self, interaction: discord.Interaction, enabled: bool):
        """Enable or disable test mode for private testing"""
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("❌ You need 'Manage Server' permission to use this command.", ephemeral=True)
            return
        
        guild_config = Config.get_guild_config(interaction.guild.id) or {
            'monitored_channels': [],
            'summary_channel_id': None,
            'test_mode': False,
            'test_user_id': None
        }
        
        guild_config['test_mode'] = enabled
        if enabled:
            guild_config['test_user_id'] = interaction.user.id
        else:
            guild_config['test_user_id'] = None
            
        Config.set_guild_config(interaction.guild.id, guild_config)
        
        if enabled:
            embed = discord.Embed(
                title="🧪 Test Mode Enabled",
                description="Daily summaries will be sent to your DMs instead of the summary channel for testing.",
                color=discord.Color.orange()
            )
        else:
            embed = discord.Embed(
                title="✅ Test Mode Disabled",
                description="Daily summaries will be posted to the configured summary channel normally.",
                color=discord.Color.green()
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @config_group.command(name='list_channels', description='List all monitored channels')
    async def slash_list_monitored_channels(self, interaction: discord.Interaction):
        """List all monitored channels"""
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("❌ You need 'Manage Server' permission to use this command.", ephemeral=True)
            return
            
        monitored_channels = Config.get_monitored_channels(interaction.guild.id)
        
        if not monitored_channels:
            await interaction.response.send_message("❌ No channels are being monitored", ephemeral=True)
            return
        
        channel_list = []
        for channel_id in monitored_channels:
            channel = interaction.guild.get_channel(channel_id)
            if channel:
                channel_list.append(f"• {channel.mention}")
            else:
                channel_list.append(f"• Unknown channel (ID: {channel_id})")
        
        embed = discord.Embed(
            title="📋 Monitored Channels",
            description="\n".join(channel_list),
            color=discord.Color.blue()
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name='help', description='Show help information for SummyBot')
    @app_commands.describe(category='Specific help category (optional)')
    async def slash_help(self, interaction: discord.Interaction, category: str = None):
        """Show help information for SummyBot"""
        
        if category == 'config':
            embed = discord.Embed(
                title="⚙️ Configuration Commands",
                color=discord.Color.blue()
            )
            
            embed.add_field(
                name="/config show",
                value="Show current server configuration",
                inline=False
            )
            
            embed.add_field(
                name="/config setup",
                value="Interactive setup guide",
                inline=False
            )
            
            embed.add_field(
                name="/config summary_channel",
                value="Set where summaries are posted",
                inline=False
            )
            
            embed.add_field(
                name="/config add_channel",
                value="Add channel to monitoring",
                inline=False
            )
            
            embed.add_field(
                name="/config remove_channel",
                value="Remove channel from monitoring",
                inline=False
            )
            
        else:
            embed = discord.Embed(
                title="🤖 SummyBot Help",
                description="I summarize daily conversations from your channels!",
                color=discord.Color.purple()
            )
            
            embed.add_field(
                name="📊 Summary Commands",
                value="`/summary` - Generate manual summary\n"
                      "`/daily` - Force daily summary\n"
                      "`/test_summary` - Test summarization",
                inline=False
            )
            
            embed.add_field(
                name="⚙️ Configuration",
                value="`/config show` - Show configuration\n"
                      "`/config setup` - Setup guide\n"
                      "`/help config` - Configuration help",
                inline=False
            )
            
            embed.add_field(
                name="🕐 Automatic Summaries",
                value="Daily summaries are automatically posted at 11 PM UTC",
                inline=False
            )
            
            embed.add_field(
                name="🔒 Privacy",
                value="All slash commands are private (ephemeral) - only you can see the responses!",
                inline=False
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    cog = ConfigCommands(bot)
    await bot.add_cog(cog)
    bot.tree.add_command(cog.config_group)
