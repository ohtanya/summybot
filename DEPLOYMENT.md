# SummyBot VPS Deployment Guide

This guide will help you deploy SummyBot on your VPS using PM2 for production use.

## 🚀 Quick Deployment

### 1. Upload Files to VPS

Upload these files to your VPS:
```bash
# Using scp (replace user@your-vps-ip with your details)
scp -r summybot/ user@your-vps-ip:/tmp/

# Or clone from Git if you have a repository
git clone your-repo-url /opt/summybot
```

### 2. Run Deployment Script

```bash
# Make script executable and run
chmod +x /tmp/summybot/deploy.sh
sudo /tmp/summybot/deploy.sh
```

### 3. Configure Bot Token

```bash
# Edit the environment file
sudo nano /opt/summybot/.env

# Add your Discord bot token:
DISCORD_BOT_TOKEN=your_actual_bot_token_here
```

### 4. Start the Bot

```bash
cd /opt/summybot
pm2 start ecosystem.config.js
pm2 save
pm2 startup
```

## 📋 Manual Installation Steps

If you prefer manual setup:

### 1. Install Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python
sudo apt install -y python3 python3-pip python3-venv git

# Install Node.js and PM2
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs
sudo npm install -g pm2
```

### 2. Setup Application

```bash
# Create directory
sudo mkdir -p /opt/summybot
sudo chown $USER:$USER /opt/summybot
cd /opt/summybot

# Copy your bot files here
# Then setup virtual environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
# Create .env file
cp .env.example .env
nano .env  # Add your bot token
```

### 4. Start with PM2

```bash
pm2 start ecosystem.config.js
pm2 save
pm2 startup  # Follow the instructions this command gives you
```

## 🛠️ Management Commands

Use the included management script:

```bash
# Make it executable
chmod +x /opt/summybot/manage.sh

# Available commands:
./manage.sh start      # Start the bot
./manage.sh stop       # Stop the bot
./manage.sh restart    # Restart the bot
./manage.sh status     # Check status
./manage.sh logs       # View logs
./manage.sh update     # Update dependencies
./manage.sh monitor    # Open PM2 dashboard
./manage.sh backup     # Create backup
```

## 📊 Monitoring

### PM2 Commands
```bash
pm2 status summybot    # Check status
pm2 logs summybot      # View logs
pm2 monit             # Real-time monitoring
pm2 restart summybot  # Restart bot
pm2 stop summybot     # Stop bot
pm2 delete summybot   # Remove from PM2
```

### Log Files
- Application logs: `/opt/summybot/summybot.log`
- PM2 logs: `/opt/summybot/logs/`
- Error logs: `/opt/summybot/logs/err.log`
- Output logs: `/opt/summybot/logs/out.log`

## 🔧 Configuration

### Environment Variables (.env)
```bash
DISCORD_BOT_TOKEN=your_bot_token_here
OPENAI_API_KEY=optional_openai_key
COMMAND_PREFIX=!
SUMMARY_TIME_HOUR=23
SUMMARY_TIME_MINUTE=0
LOG_LEVEL=INFO
```

### PM2 Configuration (ecosystem.config.js)
- Auto-restart on crashes
- Memory limit: 2GB
- Log rotation
- Environment variables

## 🔄 Updates

To update the bot:
```bash
cd /opt/summybot
git pull  # If using Git
./manage.sh update
```

## 🛡️ Security

### Firewall
```bash
# Only allow necessary ports
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable
```

### File Permissions
```bash
# Secure the .env file
chmod 600 /opt/summybot/.env
```

### Bot Token Security
- Never commit `.env` to version control
- Use environment variables for sensitive data
- Regularly rotate bot tokens

## 🚨 Troubleshooting

### Bot Won't Start
```bash
# Check logs
pm2 logs summybot

# Check Python environment
/opt/summybot/.venv/bin/python --version

# Test bot directly
cd /opt/summybot
/opt/summybot/.venv/bin/python main.py
```

### Memory Issues
```bash
# Check memory usage
pm2 monit

# Increase memory limit in ecosystem.config.js
max_memory_restart: '4G'
```

### Permission Errors
```bash
# Fix ownership
sudo chown -R $USER:$USER /opt/summybot

# Fix permissions
chmod +x /opt/summybot/manage.sh
```

## 📦 Backup Strategy

### Automated Backups
```bash
# Add to crontab for daily backups
0 2 * * * /opt/summybot/manage.sh backup

# Add to crontab
crontab -e
```

### Manual Backup
```bash
./manage.sh backup
```

## 🔧 Advanced Configuration

### Custom Paths
Edit `ecosystem.config.js` to change:
- Application directory
- Log file locations
- Python interpreter path

### Multiple Instances
For high availability, you can run multiple instances:
```javascript
instances: 2  // In ecosystem.config.js
```

### Auto-scaling
PM2 can auto-scale based on CPU usage:
```bash
pm2 start ecosystem.config.js --instances max
```

## 📞 Support

If you encounter issues:
1. Check the logs: `pm2 logs summybot`
2. Verify bot token and permissions
3. Check Discord API status
4. Ensure all dependencies are installed

Remember to keep your bot token secure and never share it publicly!