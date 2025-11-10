#!/bin/bash
# Qwen2.5-Coder Service Startup Script
# Starts Ollama service and pulls the model if needed

set -e

echo "=== Qwen2.5-Coder-7B-Instruct Service ==="
echo "Model: qwen2.5-coder:7b"
echo "Backend: Ollama with ROCm support"
echo ""

# Start the service if not already running
if ! docker ps | grep -q qwen-coder; then
    echo "Starting qwen-coder container..."
    docker compose up -d
    echo "Waiting for Ollama to be ready..."
    sleep 5
else
    echo "✓ Container already running"
fi

# Check if model is already pulled
if docker exec qwen-coder ollama list | grep -q "qwen2.5-coder:7b"; then
    echo "✓ Model already downloaded"
else
    echo "⏳ Pulling qwen2.5-coder:7b model..."
    echo "   This may take 5-10 minutes depending on your connection."
    echo "   Model size: ~4.7 GB"
    docker exec -it qwen-coder ollama pull qwen2.5-coder:7b
fi

echo ""
echo "✓ Service is ready!"
echo "API available at: http://localhost:8001"
echo "OpenAI-compatible endpoint: http://localhost:8001/v1/chat/completions"
echo ""
echo "Test the service:"
echo '  curl http://localhost:8001/api/generate -d '\''{"model":"qwen2.5-coder:7b","prompt":"Write a hello world in Python","stream":false}'\'''
echo ""
echo "List models:"
echo "  docker exec qwen-coder ollama list"
echo ""
echo "View logs:"
echo "  docker logs qwen-coder -f"
