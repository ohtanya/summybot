# SummyBot - Discord Conversation Summarizer

This project contains a Discord bot that automatically summarizes daily conversations from various channels and posts them to a designated summary channel.

## Key Features
- Automatic daily conversation summaries at configurable times
- Manual summary generation for any channel and timeframe
- Multiple AI/NLP summarization methods (OpenAI, local transformers, extractive)
- Channel monitoring configuration per Discord server
- Permission-aware operation with proper Discord integration

## Main Components
- `main.py` - Main bot application with Discord.py integration
- `src/summarizer.py` - Conversation analysis and summarization logic
- `src/config.py` - Configuration management for multiple Discord servers
- `src/commands/` - Bot command modules for user interaction

## Commands Available
- Summary commands: `!summary`, `!daily`, `!test_summary`
- Configuration: `!config`, `!config setup`, `!config add_channel`
- Help system with detailed usage instructions

## Setup Requirements
- Discord bot token from Discord Developer Portal
- Python 3.8+ with discord.py and other dependencies
- Optional OpenAI API key for enhanced summarization
- Proper Discord permissions for message reading and posting

## Architecture
The bot uses a modular design with separate concerns for:
- Discord API interaction and event handling
- Message collection and conversation analysis  
- Multiple summarization backends with fallback
- Per-server configuration persistence
- Scheduled task management for daily summaries

This is a production-ready Discord bot project suitable for community servers that want to track and summarize daily discussions across multiple channels.
