#!/bin/bash

# 1. Download Code
echo "⬇️ Pulling latest code..."
git pull

# 2. Restart the Service (Let Systemd handle the processes)
echo "♻️ Restarting Systemd Service..."
sudo systemctl restart watchdog

# 3. Confirmation
echo "✅ Deployment Complete! Systemd has reloaded the bots."
