#!/bin/bash
# Stop Gradio Server Script
# Kills any running Gradio server processes

echo "🛑 Stopping Gradio Server..."
echo "================================"

# Find and kill any running Gradio processes
# Match any python process running app_gradio.py
PIDS=$(ps aux | grep -E "[P]ython.*app_gradio|[p]ython.*app_gradio" | awk '{print $2}')

if [ -z "$PIDS" ]; then
    echo "✓ No running Gradio server found"
    echo ""
    echo "💡 Checking for processes using port 7860..."
    PORT_PIDS=$(lsof -ti:7860 2>/dev/null)
    if [ -n "$PORT_PIDS" ]; then
        echo "⚠️  Found process(es) using port 7860:"
        lsof -i:7860
        echo ""
        echo "🔪 Killing process(es) on port 7860..."
        for PID in $PORT_PIDS; do
            echo "   Killing PID $PID"
            kill $PID
            sleep 1
            if ps -p $PID > /dev/null 2>&1; then
                kill -9 $PID
            fi
        done
        echo "✓ Port 7860 freed"
    fi
    exit 0
fi

echo "Found running Gradio server(s):"
ps aux | grep -E "[P]ython.*app_gradio|[p]ython.*app_gradio"
echo ""

for PID in $PIDS; do
    echo "🔪 Killing process $PID..."
    kill $PID
    sleep 1
    
    # Force kill if still running
    if ps -p $PID > /dev/null 2>&1; then
        echo "   Process still alive, force killing..."
        kill -9 $PID
    fi
done

echo ""
echo "✓ All Gradio processes stopped"
echo "💡 Use ./start_gradio.sh to start a new server"
