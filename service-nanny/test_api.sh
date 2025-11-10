#!/bin/bash
# Quick test script for Service Nanny

set -e

API_URL="http://localhost:8080"

echo "🧪 Testing Service Nanny API"
echo "================================"
echo ""

# Test 1: Health check
echo "1️⃣  Testing health endpoint..."
curl -s "$API_URL/health" | jq .
echo "✅ Health check passed"
echo ""

# Test 2: List services
echo "2️⃣  Listing discovered services..."
curl -s "$API_URL/services" | jq '.services[] | {name, gpu_required, status}'
echo "✅ Service discovery working"
echo ""

# Test 3: Get specific service
echo "3️⃣  Getting minimal-sd-api details..."
curl -s "$API_URL/services/minimal-sd-api" | jq .
echo "✅ Service query working"
echo ""

# Test 4: Check service status
echo "4️⃣  Checking minimal-sd-api status..."
curl -s "$API_URL/services/minimal-sd-api/status" | jq .
echo "✅ Status check working"
echo ""

echo "🎉 All basic tests passed!"
echo ""
echo "📝 Next steps:"
echo "  • Start a service: curl -X POST $API_URL/services/minimal-sd-api/start"
echo "  • Check status: curl $API_URL/services/minimal-sd-api/status | jq"
echo "  • Stop a service: curl -X POST $API_URL/services/minimal-sd-api/stop"
echo "  • View logs: curl $API_URL/services/minimal-sd-api/logs?tail=20"
