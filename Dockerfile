# Use a slim Python base image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file first to leverage Docker layer caching
COPY requirements.txt .

# Install dependencies
# Using --no-cache-dir to reduce image size
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code and data into the container
# The .dockerignore file will exclude specified files and directories
COPY . .

# Only install Ollama if not on Hugging Face Spaces
# HF Spaces will use the Inference API instead
RUN if [ -z "$SPACE_ID" ]; then \
        apt-get update && apt-get install -y curl && curl -fsSL https://ollama.com/install.sh | sh; \
    fi

# Run the ingestion script to populate the ChromaDB vector store
# This step pre-builds the database so the app starts ready
RUN python initialize_rag.py

# Copy and set up the startup script
COPY start.sh .
RUN chmod +x start.sh

# Expose the port Gradio will run on
EXPOSE 7860

# Use the startup script as the entrypoint
CMD ["./start.sh"]
