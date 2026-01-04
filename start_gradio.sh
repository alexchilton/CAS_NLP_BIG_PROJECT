#!/bin/bash
# Start Gradio Server Script
# Starts a fresh Gradio server (kills existing if running)

echo "🚀 Starting Gradio Server..."
echo "================================"

# Kill any existing server first
./stop_gradio.sh

echo ""
echo "Starting new server..."
cd "$(dirname "$0")"

# Check if we should run in background or foreground
if [ "$1" == "--background" ] || [ "$1" == "-b" ]; then
    echo "Starting in background mode..."
    mkdir -p logs
    nohup python3 web/app_gradio.py > logs/gradio.log 2>&1 &
    NEW_PID=$!
    sleep 2
    echo ""
    echo "✓ Gradio server started (PID: $NEW_PID)"
    echo "📋 Logs: tail -f logs/gradio.log"
    echo "🌐 URL: http://localhost:7860"
    echo ""
    echo "💡 To stop: ./stop_gradio.sh"
else
    echo "Starting in foreground mode (Ctrl+C to stop)..."
    echo "💡 Tip: Use --background or -b to run in background"
    echo ""
    python3 web/app_gradio.py
fi
