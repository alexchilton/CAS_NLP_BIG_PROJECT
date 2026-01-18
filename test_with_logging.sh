#!/bin/bash

# Kill existing servers
pkill -9 -f "app_gradio.py"
sleep 2

# Start Gradio with full logging
echo "Starting Gradio with logging..."
cd /Users/alexchilton/DataspellProjects/CAS_NLP_BIG_PROJECT
python3 web/app_gradio.py 2>&1 | tee /tmp/gradio_debug.log &
GRADIO_PID=$!

sleep 10

# Run the shop test
echo "Running shop test..."
python3 e2e_tests/test_shop_ui_playwright.py 2>&1 | tee /tmp/shop_test.log

# Keep Gradio running for inspection
echo "Test complete. Gradio logs in /tmp/gradio_debug.log"
echo "Test logs in /tmp/shop_test.log"
echo "Press Ctrl+C to stop Gradio"
wait $GRADIO_PID
