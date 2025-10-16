#!/bin/bash

# SummyBot Management Script
# Usage: ./manage.sh [start|stop|restart|status|logs|update]

APP_NAME="summybot"
APP_DIR="/opt/summybot"

case "$1" in
    start)
        echo "🚀 Starting SummyBot..."
        cd $APP_DIR
        pm2 start ecosystem.config.js
        ;;
    stop)
        echo "🛑 Stopping SummyBot..."
        pm2 stop $APP_NAME
        ;;
    restart)
        echo "🔄 Restarting SummyBot..."
        pm2 restart $APP_NAME
        ;;
    status)
        echo "📊 SummyBot Status:"
        pm2 status $APP_NAME
        ;;
    logs)
        echo "📝 SummyBot Logs (Ctrl+C to exit):"
        pm2 logs $APP_NAME --lines 50
        ;;
    update)
        echo "📦 Updating SummyBot..."
        cd $APP_DIR
        
        # Stop the bot
        pm2 stop $APP_NAME
        
        # Update dependencies
        .venv/bin/pip install --upgrade discord.py python-dotenv aiohttp transformers torch
        
        # Restart the bot
        pm2 restart $APP_NAME
        echo "✅ Update complete!"
        ;;
    monitor)
        echo "📊 Opening PM2 Monitor..."
        pm2 monit
        ;;
    backup)
        echo "💾 Creating backup..."
        tar -czf "/tmp/summybot-backup-$(date +%Y%m%d-%H%M%S).tar.gz" \
            -C /opt summybot/data summybot/.env summybot/logs
        echo "✅ Backup created in /tmp/"
        ;;
    *)
        echo "SummyBot Management Script"
        echo "Usage: $0 {start|stop|restart|status|logs|update|monitor|backup}"
        echo ""
        echo "Commands:"
        echo "  start    - Start the bot"
        echo "  stop     - Stop the bot"
        echo "  restart  - Restart the bot"
        echo "  status   - Show bot status"
        echo "  logs     - Show real-time logs"
        echo "  update   - Update dependencies and restart"
        echo "  monitor  - Open PM2 monitoring dashboard"
        echo "  backup   - Create backup of data and config"
        exit 1
        ;;
esac