# Local Docker Development with Ollama

This guide explains how to run the D&D RAG System locally using Docker Compose with Ollama for LLM inference.

## Architecture

```
┌─────────────────────────────────────┐
│  D&D RAG Application (Port 7860)    │
│  - Gradio web interface             │
│  - ChromaDB vector database         │
│  - RAG retrieval system             │
└──────────────┬──────────────────────┘
               │
               │ HTTP API calls
               ▼
┌─────────────────────────────────────┐
│  Ollama Service (Port 11434)        │
│  - Qwen3-4B-RPG-Roleplay-V2 model   │
│  - LLM inference API                │
└─────────────────────────────────────┘
```

## Prerequisites

- Docker Desktop installed and running
- At least 8GB of available RAM
- ~10GB of free disk space (for model + data)

## Quick Start

### 1. Start All Services

```bash
docker-compose up -d
```

This will:
1. Start the Ollama service
2. Pull the RPG model (~2.4GB - first time only)
3. Start the D&D application
4. Initialize the RAG database on first run

### 2. Wait for Model Download

The first time you run this, it will download the Ollama model. Check progress:

```bash
# Watch Ollama setup logs
docker-compose logs -f ollama-setup

# Check if model is ready
docker exec dnd-ollama ollama list
```

### 3. Access the Application

Open your browser to:
- **D&D App**: http://localhost:7860
- **Ollama API**: http://localhost:11434 (not needed for normal use)

### 4. View Logs

```bash
# All services
docker-compose logs -f

# Just the app
docker-compose logs -f app

# Just Ollama
docker-compose logs -f ollama
```

## Managing Services

### Stop Everything

```bash
docker-compose down
```

### Stop and Remove All Data

```bash
docker-compose down -v
```

**Warning**: This will delete:
- Downloaded Ollama models (~2.4GB)
- ChromaDB vector database
- All game state

### Restart a Service

```bash
# Restart just the app
docker-compose restart app

# Restart just Ollama
docker-compose restart ollama
```

### Rebuild After Code Changes

```bash
docker-compose up -d --build
```

## Data Persistence

Data is stored in Docker volumes:

- `ollama-data`: Ollama models and config (~2.4GB)
- `chromadb-data`: RAG vector database (~100MB)

These persist between container restarts but are removed with `docker-compose down -v`.

## Development Mode

To enable live code reloading, uncomment these lines in `docker-compose.yml`:

```yaml
volumes:
  - ./web:/app/web
  - ./dnd_rag_system:/app/dnd_rag_system
```

Then restart:

```bash
docker-compose up -d --build
```

Now changes to Python files will be reflected immediately (you may need to refresh the browser).

## Troubleshooting

### Ollama Model Not Found

If you get "model not found" errors:

```bash
# Pull the model manually
docker exec dnd-ollama ollama pull hf.co/Chun121/Qwen3-4B-RPG-Roleplay-V2:Q4_K_M

# Check it's installed
docker exec dnd-ollama ollama list
```

### App Can't Connect to Ollama

Check that Ollama service is healthy:

```bash
docker-compose ps
```

Should show `ollama` as "healthy". If not:

```bash
docker-compose logs ollama
docker-compose restart ollama
```

### Port Already in Use

If port 7860 or 11434 is already in use, edit `docker-compose.yml`:

```yaml
ports:
  - "8860:7860"  # Use port 8860 instead of 7860
```

### RAG Database Issues

To reset the RAG database:

```bash
docker-compose down
docker volume rm cas_nlp_big_project_chromadb-data
docker-compose up -d
```

The app will reinitialize the database on startup.

## Using a Different Model

To use a different Ollama model:

1. Edit `dnd_rag_system/config/settings.py`:
   ```python
   OLLAMA_MODEL_NAME = "your-model-name"
   ```

2. Update `docker-compose.yml` ollama-setup service:
   ```yaml
   ollama pull your-model-name
   ```

3. Rebuild:
   ```bash
   docker-compose down
   docker-compose up -d --build
   ```

## Performance Tips

### GPU Acceleration (NVIDIA only)

If you have an NVIDIA GPU:

1. Install [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html)

2. Add to `docker-compose.yml` under the `ollama` service:
   ```yaml
   deploy:
     resources:
       reservations:
         devices:
           - driver: nvidia
             count: 1
             capabilities: [gpu]
   ```

3. Restart:
   ```bash
   docker-compose down
   docker-compose up -d
   ```

This will significantly speed up LLM inference!

## Differences from HuggingFace Deployment

| Feature | Local Docker | HuggingFace Spaces |
|---------|--------------|-------------------|
| LLM Provider | Ollama (local) | HuggingFace Inference API |
| Model | Qwen3-4B | Via API (configurable) |
| GPU | Optional (NVIDIA) | Provided by HF |
| Cost | Free (uses your hardware) | Free tier available |
| Privacy | Fully local | Data sent to HF API |

## Next Steps

- Try different Ollama models for better/faster responses
- Enable GPU acceleration for faster inference
- Mount code volumes for live development
- Customize the RAG database with your own content

Enjoy your local D&D RAG system! 🎲
