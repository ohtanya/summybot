#!/bin/bash

# SummyBot VPS Deployment Script
# Run this script on your VPS to deploy the bot

echo "🚀 Deploying SummyBot..."

# Update system packages
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install Python and pip if not installed
echo "🐍 Installing Python and dependencies..."
sudo apt install -y python3 python3-pip python3-venv git

# Install Node.js and PM2 if not installed
echo "📦 Installing Node.js and PM2..."
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs
sudo npm install -g pm2

# Create application directory
APP_DIR="/opt/summybot"
echo "📁 Setting up application directory: $APP_DIR"
sudo mkdir -p $APP_DIR
sudo chown $USER:$USER $APP_DIR

# Clone or copy the application
echo "📥 Setting up application files..."
cd $APP_DIR

# Create Python virtual environment
echo "🔧 Setting up Python virtual environment..."
python3 -m venv .venv
source .venv/bin/python

# Install Python dependencies
echo "📦 Installing Python packages..."
.venv/bin/pip install --upgrade pip
.venv/bin/pip install discord.py python-dotenv aiohttp transformers torch

# Create logs directory
mkdir -p logs

# Create .env file template
echo "⚙️ Creating environment file..."
cat > .env << EOL
# Discord Bot Token (Required)
DISCORD_BOT_TOKEN=your_bot_token_here

# OpenAI API Key (Optional)
OPENAI_API_KEY=

# Bot Configuration
COMMAND_PREFIX=!
SUMMARY_TIME_HOUR=23
SUMMARY_TIME_MINUTE=0

# Database Configuration
DATABASE_URL=sqlite:///summybot.db

# Logging Level
LOG_LEVEL=INFO
EOL

# Update ecosystem config with correct path
echo "🔧 Updating PM2 configuration..."
sed -i "s|/path/to/summybot|$APP_DIR|g" ecosystem.config.js
sed -i "s|python3|$APP_DIR/.venv/bin/python|g" ecosystem.config.js

echo "✅ Deployment setup complete!"
echo ""
echo "📝 Next steps:"
echo "1. Edit .env file and add your Discord bot token:"
echo "   nano $APP_DIR/.env"
echo ""
echo "2. Start the bot with PM2:"
echo "   cd $APP_DIR"
echo "   pm2 start ecosystem.config.js"
echo ""
echo "3. Save PM2 configuration and enable startup:"
echo "   pm2 save"
echo "   pm2 startup"
echo ""
echo "4. Check bot status:"
echo "   pm2 status"
echo "   pm2 logs summybot"