#!/bin/bash

# GitHub Inbox Discord Bot Service Manager
SERVICE_NAME="github-inbox-bot"
SERVICE_FILE="/home/cappo/github-inbox-bot/github-inbox-bot.service"
SYSTEM_SERVICE_PATH="/etc/systemd/system/$SERVICE_NAME.service"

case "$1" in
    install)
        echo "Installing $SERVICE_NAME as a systemd service..."
        sudo cp "$SERVICE_FILE" "$SYSTEM_SERVICE_PATH"
        sudo systemctl daemon-reload
        sudo systemctl enable "$SERVICE_NAME"
        echo "✅ Service installed and enabled!"
        echo "Use './service-manager.sh start' to start the service"
        ;;
    
    uninstall)
        echo "Uninstalling $SERVICE_NAME service..."
        sudo systemctl stop "$SERVICE_NAME" 2>/dev/null
        sudo systemctl disable "$SERVICE_NAME" 2>/dev/null
        sudo rm -f "$SYSTEM_SERVICE_PATH"
        sudo systemctl daemon-reload
        echo "✅ Service uninstalled!"
        ;;
    
    start)
        echo "Starting $SERVICE_NAME..."
        sudo systemctl start "$SERVICE_NAME"
        echo "✅ Service started!"
        ;;
    
    stop)
        echo "Stopping $SERVICE_NAME..."
        sudo systemctl stop "$SERVICE_NAME"
        echo "✅ Service stopped!"
        ;;
    
    restart)
        echo "Restarting $SERVICE_NAME..."
        sudo systemctl restart "$SERVICE_NAME"
        echo "✅ Service restarted!"
        ;;
    
    status)
        sudo systemctl status "$SERVICE_NAME"
        ;;
    
    logs)
        echo "Showing logs for $SERVICE_NAME (press Ctrl+C to exit)..."
        sudo journalctl -u "$SERVICE_NAME" -f
        ;;
    
    *)
        echo "GitHub Inbox Discord Bot Service Manager"
        echo "Usage: $0 {install|uninstall|start|stop|restart|status|logs}"
        echo ""
        echo "Commands:"
        echo "  install   - Install bot as a systemd service"
        echo "  uninstall - Remove bot from systemd services"
        echo "  start     - Start the bot service"
        echo "  stop      - Stop the bot service"
        echo "  restart   - Restart the bot service"
        echo "  status    - Show service status"
        echo "  logs      - Show live service logs"
        exit 1
        ;;
esac
