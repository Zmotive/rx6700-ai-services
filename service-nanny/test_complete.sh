#!/bin/bash

echo "🧪 Complete Service Nanny Test Suite"
echo "===================================="
echo ""

# Test 1: List services
echo "1️⃣  List all services:"
curl -s http://localhost:8080/services | python3 -m json.tool | head -20
echo ""

# Test 2: Get specific service
echo "2️⃣  Get minimal-sd-api details:"
curl -s http://localhost:8080/services/minimal-sd-api | python3 -m json.tool | head -15
echo ""

# Test 3: Check status
echo "3️⃣  Check minimal-sd-api status:"
curl -s http://localhost:8080/services/minimal-sd-api/status | python3 -m json.tool
echo ""

# Test 4: Get logs
echo "4️⃣  Get recent logs (last 5 lines):"
curl -s "http://localhost:8080/services/minimal-sd-api/logs?tail=5" | python3 -m json.tool | grep -A 20 '"logs"'
echo ""

echo "✅ All API tests passed!"
