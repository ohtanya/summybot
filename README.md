# SummyBot 🤖📝

[![Discord](https://img.shields.io/badge/Discord-Bot-7289da?style=flat-square&logo=discord)](https://discord.com/)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue?style=flat-square&logo=python)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

A Discord bot that automatically summarizes daily conversations from various channels and posts them to a designated summary channel. Perfect for keeping track of important discussions across your server!

## ✨ Features

- 🕐 **Automatic Daily Summaries**: Generates summaries at 11 PM UTC every day
- 📊 **Manual Summaries**: Generate summaries on-demand for any channel and timeframe  
- 🎯 **Channel Monitoring**: Configure which channels to monitor for conversations
- 🧠 **Multiple AI Methods**: Supports OpenAI API, local transformers, and fallback methods
- ⚙️ **Slash Commands**: Modern Discord slash commands with private responses
- 🧪 **Test Mode**: Private testing with DMs before going live
- 🔒 **Permission-Aware**: Respects Discord permissions and only accesses authorized channels
- 🚀 **Production Ready**: PM2 deployment with auto-restart and monitoring

## 🚀 Quick Start

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/summybot.git
   cd summybot
   ```

2. **Install dependencies**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env and add your Discord bot token
   ```

4. **Run the bot**
   ```bash
   python main.py
   ```

### VPS Deployment

For production deployment with PM2, see [DEPLOYMENT.md](DEPLOYMENT.md)

## 🤖 Bot Setup

### 1. Create Discord Application
1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application
3. Go to "Bot" section and create a bot
4. Copy the bot token
5. Enable "Message Content Intent" under Privileged Gateway Intents

### 2. Invite Bot to Server
Use this URL (replace `YOUR_CLIENT_ID`):
```
https://discord.com/oauth2/authorize?client_id=YOUR_CLIENT_ID&permissions=84992&scope=bot+applications.commands
```

### 3. Configure Bot
```bash
/config setup              # Interactive setup
/config summary_channel    # Set where summaries go
/config add_channel        # Add channels to monitor
/config test_mode true     # Enable private testing
```

## 💬 Commands

### Summary Commands
- `/summary` - Generate summary for any channel/timeframe
- `/private_summary` - Send summary to your DMs
- `/daily` - Force generate today's daily summary  
- `/test_summary` - Test with recent messages

### Configuration Commands
- `/config show` - View current server configuration
- `/config setup` - Interactive setup guide
- `/config summary_channel` - Set summary destination
- `/config add_channel` - Add channel to monitoring
- `/config remove_channel` - Stop monitoring a channel
- `/config test_mode` - Toggle private testing mode

## 🧠 AI Summarization

The bot uses multiple summarization methods in order of preference:

1. **OpenAI GPT-3.5** (if API key provided) - Highest quality
2. **Local BART Model** (free) - Good quality, runs offline  
3. **Simple Extractive** (fallback) - Basic but functional

## 🧪 Testing

### Private Testing Options
- **Ephemeral Commands**: All slash commands are private by default
- **DM Summaries**: Use `/private_summary` to get results in DMs
- **Test Mode**: Enable with `/config test_mode true` for private daily summaries
- **Private Channels**: Create a test channel only you can see

## 📁 Project Structure

```
summybot/
├── main.py                    # Bot entry point
├── requirements.txt           # Python dependencies
├── ecosystem.config.js        # PM2 configuration
├── deploy.sh                 # VPS deployment script
├── manage.sh                 # Bot management script
├── .env.example              # Environment template
├── src/
│   ├── config.py            # Configuration management
│   ├── summarizer.py        # AI summarization logic
│   └── commands/
│       ├── summary_commands.py    # Summary slash commands
│       └── config_commands.py     # Configuration commands
├── data/                     # Auto-generated data directory
├── logs/                     # PM2 logs (production)
└── .github/
    └── copilot-instructions.md
```

## ⚙️ Configuration

### Environment Variables (.env)
```bash
DISCORD_BOT_TOKEN=your_bot_token_here
OPENAI_API_KEY=optional_for_enhanced_summaries
COMMAND_PREFIX=!
SUMMARY_TIME_HOUR=23
SUMMARY_TIME_MINUTE=0
LOG_LEVEL=INFO
```

### Required Permissions
- View Channels
- Send Messages
- Embed Links  
- Read Message History
- Use Application Commands

## 🛠️ Development

### Running Tests
```bash
# Test summarization
/test_summary

# Test configuration  
/config show
```

### Adding Features
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 🚀 Production Deployment

### Using PM2 (Recommended)
```bash
# Quick deployment
chmod +x deploy.sh
sudo ./deploy.sh

# Manual management
./manage.sh start|stop|restart|status|logs
```

### Docker (Alternative)
```bash
# Coming soon - Docker support planned
```

## 📊 Monitoring

### PM2 Commands
```bash
pm2 status summybot    # Check status
pm2 logs summybot      # View logs  
pm2 monit             # Real-time monitoring
pm2 restart summybot  # Restart bot
```

### Health Checks
- Bot status indicator in Discord
- Automatic restart on crashes
- Memory usage monitoring
- Log file rotation

## 🛡️ Security

- Environment variables for sensitive data
- No token storage in code
- Permission-based access control
- Local AI processing (optional OpenAI)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- 📖 Check [DEPLOYMENT.md](DEPLOYMENT.md) for deployment issues
- 🐛 Open an issue for bugs
- 💡 Request features via issues
- 📧 Contact via Discord for urgent issues

## 🙏 Acknowledgments

- [discord.py](https://github.com/Rapptz/discord.py) - Discord API wrapper
- [Transformers](https://github.com/huggingface/transformers) - AI models
- [PM2](https://pm2.keymetrics.io/) - Process management

---

**Note**: This bot processes message content for summarization. Ensure compliance with your server's privacy policies and Discord's Terms of Service.

## Bot Setup in Discord

### 1. Invite the Bot
Make sure your bot has these permissions:
- Read Messages/View Channels
- Send Messages
- Embed Links
- Read Message History

### 2. Configure the Bot

1. **Set Summary Channel**:
   ```
   !config summary_channel #daily-summaries
   ```

2. **Add Channels to Monitor**:
   ```
   !config add_channel #general
   !config add_channel #development
   !config add_channel #random
   ```

3. **Test the Setup**:
   ```
   !test_summary
   ```

## Commands

### Summary Commands

- `!summary [#channel] [hours]` - Generate a manual summary
  - Example: `!summary #general 12` (last 12 hours)
  - Default: current channel, last 24 hours

- `!daily` - Force generate today's daily summary

- `!test_summary` - Test summarization with recent messages

### Configuration Commands

- `!config` - Show current server configuration
- `!config setup` - Interactive setup guide
- `!config summary_channel #channel` - Set summary destination
- `!config add_channel #channel` - Add channel to monitoring
- `!config remove_channel #channel` - Remove channel from monitoring
- `!config list_channels` - List all monitored channels

### Help

- `!help` - General help
- `!help config` - Configuration command help

## How It Works

1. **Message Collection**: The bot monitors configured channels and collects messages from the last 24 hours
2. **Conversation Analysis**: Messages are grouped by context and analyzed for topics and participants
3. **Summarization**: Using AI/NLP techniques, the bot generates concise summaries of conversations
4. **Daily Posting**: At 11 PM UTC, summaries are automatically posted to the configured summary channel

## Summarization Methods

The bot uses multiple summarization approaches in order of preference:

1. **OpenAI API** (if configured): GPT-3.5-turbo for high-quality summaries
2. **Local Transformers**: BART model for offline summarization
3. **Extractive Summary**: Simple fallback method

## Configuration Files

- `requirements.txt` - Python dependencies
- `.env` - Environment variables (create from `.env.example`)
- `data/guild_configs.json` - Server-specific configurations (auto-generated)

## Project Structure

```
summybot/
├── main.py                 # Bot entry point
├── requirements.txt        # Dependencies
├── .env.example           # Environment template
├── src/
│   ├── config.py          # Configuration management
│   ├── summarizer.py      # Summarization logic
│   └── commands/
│       ├── summary_commands.py    # Summary-related commands
│       └── config_commands.py     # Configuration commands
├── data/                  # Auto-generated data directory
└── .github/
    └── copilot-instructions.md
```

## Permissions Required

### Bot Permissions
- View Channels
- Send Messages
- Embed Links
- Read Message History
- Use Slash Commands (future feature)

### User Permissions for Commands
- **Configuration Commands**: Manage Server
- **Manual Summaries**: Manage Messages
- **Admin Commands**: Administrator

## Troubleshooting

### Common Issues

1. **Bot not responding**:
   - Check if bot is online
   - Verify bot has necessary permissions
   - Check console for error messages

2. **Cannot read messages**:
   - Ensure bot has "Read Message History" permission
   - Check channel-specific permissions

3. **Summaries not generating**:
   - Verify channels are configured
   - Check if there are enough messages (minimum 3)
   - Review logs for errors

4. **Daily summaries not posting**:
   - Confirm summary channel is set
   - Check bot permissions in summary channel
   - Verify time zone settings

### Logs

The bot creates a `summybot.log` file with detailed information about operations and any errors.

## Customization

### Changing Summary Time
Edit the time in `main.py`:
```python
@tasks.loop(time=time(hour=23, minute=0))  # 11 PM UTC
```

### Adjusting Summarization
Modify parameters in `src/summarizer.py`:
- Message collection limits
- Summary length
- Topic extraction logic

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is open source. See LICENSE file for details.

## Support

If you encounter issues or have questions:
1. Check the troubleshooting section
2. Review the logs (`summybot.log`)
3. Create an issue on GitHub

---

**Note**: This bot processes message content for summarization. Ensure compliance with your server's privacy policies and Discord's Terms of Service.
