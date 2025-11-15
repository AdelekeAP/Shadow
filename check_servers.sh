#!/bin/bash

echo "🔍 Checking Shadow Servers..."
echo ""

# Check Backend
echo "Backend (Port 8001):"
if curl -s http://localhost:8001/health > /dev/null 2>&1; then
    echo "  ✅ Running - http://localhost:8001"
    echo "  ✅ API Docs - http://localhost:8001/api/docs"
else
    echo "  ❌ Not running"
fi
echo ""

# Check Frontend
echo "Frontend (Port 3001):"
if curl -s http://localhost:3001 > /dev/null 2>&1; then
    echo "  ✅ Running - http://localhost:3001"
else
    echo "  ❌ Not running"
fi
echo ""

# Check Database
echo "Database:"
if psql -U postgres -d shadow_db -c "SELECT 1" > /dev/null 2>&1; then
    echo "  ✅ Connected - shadow_db"
else
    echo "  ❌ Cannot connect"
fi
echo ""

echo "📊 Summary:"
echo "  Backend:  http://localhost:8001"
echo "  Frontend: http://localhost:3001"
echo "  Database: shadow_db (PostgreSQL)"
