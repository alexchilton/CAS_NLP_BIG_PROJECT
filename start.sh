#!/bin/bash
# Start Ollama server in the background
ollama serve &

# Wait a few seconds for the server to initialize
sleep 3

# Pull the required model
echo "Pulling Ollama model..."
ollama pull "hf.co/Chun121/Qwen3-4B-RPG-Roleplay-V2:Q4_K_M"

# Start the Gradio application
echo "Starting Gradio app..."
python app_gradio.py
