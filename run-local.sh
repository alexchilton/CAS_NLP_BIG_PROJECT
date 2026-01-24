#!/bin/bash

# Quick start script for local Docker Compose development

set -e

echo "🎲 D&D RAG System - Local Docker Setup"
echo "========================================"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop and try again."
    exit 1
fi

echo "✅ Docker is running"
echo ""

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "⚠️  docker-compose not found, trying 'docker compose' instead..."
    COMPOSE_CMD="docker compose"
else
    COMPOSE_CMD="docker-compose"
fi

echo "📦 Building and starting services..."
echo ""

# Build and start services
$COMPOSE_CMD up -d --build

echo ""
echo "⏳ Waiting for services to be ready..."
echo ""

# Wait for Ollama to be healthy
echo "Waiting for Ollama service..."
for i in {1..60}; do
    if docker inspect dnd-ollama 2>/dev/null | grep -q '"Status": "healthy"'; then
        echo "✅ Ollama is healthy"
        break
    fi
    if [ $i -eq 60 ]; then
        echo "⚠️  Ollama did not become healthy in time"
        echo "Check logs with: $COMPOSE_CMD logs ollama"
    fi
    sleep 2
done

# Wait for app to be ready
echo "Waiting for D&D app..."
for i in {1..60}; do
    if curl -s http://localhost:7860 > /dev/null 2>&1; then
        echo "✅ D&D app is ready"
        break
    fi
    if [ $i -eq 60 ]; then
        echo "⚠️  App did not become ready in time"
        echo "Check logs with: $COMPOSE_CMD logs app"
    fi
    sleep 2
done

echo ""
echo "=========================================="
echo "🎉 D&D RAG System is running!"
echo "=========================================="
echo ""
echo "📱 Access the application:"
echo "   http://localhost:7860"
echo ""
echo "📊 Useful commands:"
echo "   View logs:        $COMPOSE_CMD logs -f"
echo "   Stop services:    $COMPOSE_CMD down"
echo "   Restart app:      $COMPOSE_CMD restart app"
echo ""
echo "📚 For more info, see DOCKER_LOCAL.md"
echo ""
