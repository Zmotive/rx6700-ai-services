#!/bin/bash
# Stable Diffusion GPU API Startup Script

echo "🚀 Starting GPU Stable Diffusion API..."
echo "📍 Location: /home/zack/ai-workspace/Projects"
echo "🎮 GPU: AMD RX 6700 XT with ROCm"
echo ""

cd /home/zack/ai-workspace/Projects

# Check if container is already running
if docker compose -f docker-compose.minimal-sd.yml ps | grep -q "Up"; then
    echo "✅ Container is already running!"
    echo "🌐 API available at: http://localhost:8000"
    echo ""
    echo "📖 Usage:"
    echo "  • Generate custom image: python3 test_generation.py \"your prompt\""
    echo "  • Generate examples: python3 test_generation.py"
    echo "  • API health check: curl http://localhost:8000/health"
    echo "  • Stop server: docker compose -f docker-compose.minimal-sd.yml down"
else
    echo "🔄 Starting container..."
    docker compose -f docker-compose.minimal-sd.yml up -d
    
    echo "⏳ Waiting for initialization (this takes ~30 seconds)..."
    sleep 30
    
    # Check if it started successfully
    if docker compose -f docker-compose.minimal-sd.yml ps | grep -q "Up"; then
        echo "✅ GPU Stable Diffusion API is running!"
        echo "🌐 Available at: http://localhost:8000"
        echo ""
        echo "📖 Quick Commands:"
        echo "  • Test generation: python3 test_generation.py \"a beautiful landscape\""
        echo "  • View examples: ls examples/"
        echo "  • Check logs: docker compose -f docker-compose.minimal-sd.yml logs"
        echo "  • Stop server: docker compose -f docker-compose.minimal-sd.yml down"
    else
        echo "❌ Failed to start. Check logs with:"
        echo "   docker compose -f docker-compose.minimal-sd.yml logs"
    fi
fi