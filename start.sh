#!/bin/bash

# Check if running on Hugging Face Spaces
if [ -n "$SPACE_ID" ] || [ -n "$SPACE_AUTHOR_NAME" ] || [ -n "$HF_SPACE" ]; then
    echo "🤗 Running on Hugging Face Spaces - using HF Inference API"
    echo "Skipping Ollama setup..."
elif [ -n "$LOCAL_DEV" ]; then
    echo "🐳 Running in Docker Compose - using Ollama service"
    echo "Ollama endpoint: $OLLAMA_BASE_URL"
    echo "Waiting for Ollama service to be ready..."

    # Wait for Ollama to be available
    max_attempts=30
    attempt=0
    while [ $attempt -lt $max_attempts ]; do
        if curl -s "$OLLAMA_BASE_URL/api/tags" > /dev/null 2>&1; then
            echo "✅ Ollama service is ready!"
            break
        fi
        attempt=$((attempt + 1))
        echo "Waiting for Ollama... ($attempt/$max_attempts)"
        sleep 2
    done

    if [ $attempt -eq $max_attempts ]; then
        echo "⚠️  Warning: Could not connect to Ollama service"
        echo "The app will start but LLM features may not work"
    fi
else
    echo "🦙 Running locally - starting Ollama"
    # Start Ollama server in the background
    ollama serve &

    # Wait a few seconds for the server to initialize
    sleep 3

    # Pull the required model
    echo "Pulling Ollama model..."
    ollama pull "hf.co/Chun121/Qwen3-4B-RPG-Roleplay-V2:Q4_K_M"
fi

# Initialize RAG database (only if not already done)
if [ ! -d "chromadb" ] || [ -z "$(ls -A chromadb 2>/dev/null)" ]; then
    echo "📚 Initializing RAG database (first run)..."
    python initialize_rag.py || echo "⚠️  RAG initialization failed, app will start with limited functionality"
else
    echo "✅ RAG database already initialized, skipping..."
fi

# Start the Gradio application
echo "Starting Gradio app..."
python web/app_gradio.py
