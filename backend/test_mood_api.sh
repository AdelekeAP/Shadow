#!/bin/bash

# Test Mood Logging API with Sentiment Analysis
# Usage: ./test_mood_api.sh <email> <password>

EMAIL="${1:-nicomannion6@gmail.com}"
PASSWORD="${2:-your_password}"
API_URL="http://localhost:8000/api/v1"

echo "============================================"
echo "🧪 Testing Shadow Mood Logging API"
echo "============================================"
echo ""

# Step 1: Login
echo "1️⃣  Logging in as $EMAIL..."
LOGIN_RESPONSE=$(curl -s -X POST "$API_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}")

TOKEN=$(echo $LOGIN_RESPONSE | grep -o '"access_token":"[^"]*' | sed 's/"access_token":"//')

if [ -z "$TOKEN" ]; then
  echo "❌ Login failed!"
  echo "Response: $LOGIN_RESPONSE"
  exit 1
fi

echo "✅ Login successful!"
echo ""

# Step 2: Log a stressed mood
echo "2️⃣  Logging stressed mood with negative note..."
MOOD1=$(curl -s -X POST "$API_URL/mood/log-mood" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "mood_type": "stressed",
    "energy_level": 2,
    "note": "I am feeling overwhelmed with all these deadlines coming up. Too much work!"
  }')

echo "$MOOD1" | python3 -m json.tool
echo ""

# Step 3: Log a motivated mood
echo "3️⃣  Logging motivated mood with positive note..."
MOOD2=$(curl -s -X POST "$API_URL/mood/log-mood" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "mood_type": "motivated",
    "energy_level": 4,
    "note": "Great day! I finished all my assignments early and feel ready for the exam!"
  }')

echo "$MOOD2" | python3 -m json.tool
echo ""

# Step 4: Get mood trends
echo "4️⃣  Fetching mood trends (last 7 days)..."
TRENDS=$(curl -s -X GET "$API_URL/mood/mood-trends?days=7" \
  -H "Authorization: Bearer $TOKEN")

echo "$TRENDS" | python3 -m json.tool
echo ""

echo "============================================"
echo "✅ Mood logging test complete!"
echo "============================================"
