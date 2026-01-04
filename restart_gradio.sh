#!/bin/bash
# Restart Gradio Server Script
# Kills any running Gradio server and starts a fresh one

echo "🔄 Restarting Gradio Server..."
echo "================================"

# Find and kill any running Gradio processes
echo "🔍 Looking for running Gradio processes..."
PIDS=$(ps aux | grep -E "[P]ython.*app_gradio|[p]ython.*app_gradio" | awk '{print $2}')

if [ -z "$PIDS" ]; then
    echo "✓ No running Gradio server found"
else
    echo "🛑 Stopping existing Gradio server(s)..."
    for PID in $PIDS; do
        echo "   Killing process $PID"
        kill $PID
        sleep 1
        # Force kill if still running
        if ps -p $PID > /dev/null 2>&1; then
            echo "   Force killing process $PID"
            kill -9 $PID
        fi
    done
    echo "✓ All Gradio processes stopped"
fi

# Check port 7860 as fallback
PORT_PIDS=$(lsof -ti:7860 2>/dev/null)
if [ -n "$PORT_PIDS" ]; then
    echo "⚠️  Found process(es) still using port 7860, killing..."
    for PID in $PORT_PIDS; do
        kill -9 $PID
    done
fi

# Wait a moment for ports to be released
sleep 2

# Start new Gradio server
echo ""
echo "🚀 Starting fresh Gradio server..."
echo "================================"

cd "$(dirname "$0")"

# Check if we should run in background or foreground
if [ "$1" == "--background" ] || [ "$1" == "-b" ]; then
    echo "Starting in background mode..."
    mkdir -p logs
    nohup python3 web/app_gradio.py > logs/gradio.log 2>&1 &
    NEW_PID=$!
    sleep 2
    echo "✓ Gradio server started in background (PID: $NEW_PID)"
    echo "📋 Logs: tail -f logs/gradio.log"
    echo "🌐 URL: http://localhost:7860"
else
    echo "Starting in foreground mode (Ctrl+C to stop)..."
    echo "💡 Tip: Use --background or -b to run in background"
    echo ""
    python3 web/app_gradio.py
fi
