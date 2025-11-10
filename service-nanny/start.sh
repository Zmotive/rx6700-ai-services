#!/bin/bash
# Service Nanny Quick Start Script

echo "🔧 Service Nanny - Quick Start"
echo "================================"
echo ""

# Check if already running
if docker ps | grep -q service-nanny; then
    echo "✅ Service Nanny is already running!"
    echo ""
    echo "🌐 API: http://localhost:8080"
    echo ""
    echo "📖 Quick Commands:"
    echo "  • List services:    curl http://localhost:8080/services | jq"
    echo "  • Start service:    curl -X POST http://localhost:8080/services/SERVICE_NAME/start"
    echo "  • Check status:     curl http://localhost:8080/services/SERVICE_NAME/status | jq"
    echo "  • Stop service:     curl -X POST http://localhost:8080/services/SERVICE_NAME/stop"
    echo "  • View logs:        docker compose logs -f"
    echo "  • Stop nanny:       docker compose down"
    exit 0
fi

# Start Service Nanny
echo "🚀 Starting Service Nanny..."
docker compose up -d

echo ""
echo "⏳ Waiting for Service Nanny to initialize..."
sleep 5

# Check if started successfully
if docker ps | grep -q service-nanny; then
    echo "✅ Service Nanny is running!"
    echo ""
    echo "🌐 API: http://localhost:8080"
    echo ""
    
    # Test API
    if curl -s http://localhost:8080/health > /dev/null 2>&1; then
        echo "🔍 Discovered services:"
        curl -s http://localhost:8080/services | jq -r '.services[] | "  • \(.name) (\(.description))"'
        echo ""
    fi
    
    echo "📖 Quick Commands:"
    echo "  • List services:    curl http://localhost:8080/services | jq"
    echo "  • Start service:    curl -X POST http://localhost:8080/services/minimal-sd-api/start"
    echo "  • Check status:     curl http://localhost:8080/services/minimal-sd-api/status | jq"
    echo "  • View logs:        docker compose logs -f"
    echo ""
    echo "📚 Full docs: ./README.md"
else
    echo "❌ Failed to start Service Nanny"
    echo "Check logs with: docker compose logs"
    exit 1
fi
