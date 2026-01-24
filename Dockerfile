# D&D RAG System - HuggingFace Spaces Deployment
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies needed for Python packages
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file first to leverage Docker layer caching
COPY requirements-minimal.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements-minimal.txt

# Copy the rest of the application code and data into the container
# The .dockerignore file will exclude test files and other unnecessary content
COPY . .

# Skip Ollama installation - it's only needed for local development
# On HuggingFace Spaces, the app will use the Inference API instead
# For local development with Ollama, use docker-compose or install separately

# Note: We skip RAG initialization during build to avoid timeouts
# The app will initialize the RAG database on first startup instead

# Copy and set up the startup script
COPY start.sh .
RUN chmod +x start.sh

# Expose the port Gradio will run on
EXPOSE 7860

# Use the startup script as the entrypoint
CMD ["./start.sh"]
