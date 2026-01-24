# Use a slim Python base image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies needed for Python packages
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy the production requirements file first to leverage Docker layer caching
COPY requirements-prod.txt .

# Install dependencies
# Using --no-cache-dir to reduce image size
RUN pip install --no-cache-dir -r requirements-prod.txt

# Copy the rest of the application code and data into the container
# The .dockerignore file will exclude specified files and directories
COPY . .

# Only install Ollama if not on Hugging Face Spaces
# HF Spaces will use the Inference API instead
RUN if [ -z "$SPACE_ID" ]; then \
        apt-get update && apt-get install -y curl && curl -fsSL https://ollama.com/install.sh | sh; \
    fi

# Note: We skip RAG initialization during build to avoid timeouts
# The app will initialize the RAG database on first startup instead
# This makes builds faster and more reliable

# Copy and set up the startup script
COPY start.sh .
RUN chmod +x start.sh

# Expose the port Gradio will run on
EXPOSE 7860

# Use the startup script as the entrypoint
CMD ["./start.sh"]
