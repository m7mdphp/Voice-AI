#!/bin/bash

# Tiryaq Voice AI - VPS Deployment Script
# Usage: bash deploy.sh

APP_DIR="/app"
VENV_DIR="$APP_DIR/myenv"
PORT=8000

echo "🚀 Starting Deployment for Tiryaq Voice AI..."

# 1. Setup Virtual Environment
if [ ! -d "$VENV_DIR" ]; then
    echo "📦 Creating virtual environment..."
    cd $APP_DIR
    python3 -m venv myenv
fi

source $VENV_DIR/bin/activate
echo "✅ Virtual Environment Activated"

# 2. Install Dependencies
echo "⬇️ Installing Dependencies..."
pip install --upgrade pip
pip install -r $APP_DIR/requirements.txt --break-system-packages

# 3. Kill Existing Processes (Port 8000/8080)
echo "🛑 Checking for existing processes..."
fuser -k $PORT/tcp 2>/dev/null || true
pkill -f "python main.py" || true
pkill -f "uvicorn" || true
sleep 2

# 4. Start Server
echo "🔥 Starting Server on Port $PORT..."
mkdir -p $APP_DIR/logs

# Run with nohup to persist after logout
nohup python3 -c "
import sys
sys.path.insert(0, '$APP_DIR')
from main import app
import uvicorn
uvicorn.run(app, host='0.0.0.0', port=$PORT, workers=1)
" > $APP_DIR/logs/server.log 2>&1 &

echo "✅ Server started in background!"
echo "📜 Check logs with: tail -f $APP_DIR/logs/server.log"
