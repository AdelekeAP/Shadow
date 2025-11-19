# 🧪 Shadow - Testing Guide

## Prerequisites
- Backend running on `http://localhost:8000`
- Frontend running on `http://localhost:3000`
- User account: `nicomannion6@gmail.com` (with your password)

---

## 🎯 Testing Mood Logging with AI Sentiment Analysis

### **Method 1: UI Testing (Recommended)**

1. **Login to Dashboard**
   ```
   URL: http://localhost:3000
   Email: nicomannion6@gmail.com
   Password: [your password]
   ```

2. **Open Mood Logger**
   - Look for the **purple floating button** at bottom-right: "💭 Log Mood"
   - Click it to open the modal

3. **Log Different Moods**

   **Test Case 1: Negative Sentiment**
   - Mood: 😰 Stressed
   - Energy: 2/5 (Low)
   - Note: "I'm feeling overwhelmed with all these deadlines coming up. Too much work!"
   - Expected: AI detects NEGATIVE sentiment (~99% confidence)

   **Test Case 2: Positive Sentiment**
   - Mood: 💪 Motivated
   - Energy: 4/5 (High)
   - Note: "Great day! Finished all my assignments early and feeling confident!"
   - Expected: AI detects POSITIVE sentiment (~100% confidence)

   **Test Case 3: Neutral/Mixed**
   - Mood: 😌 Calm
   - Energy: 3/5 (Medium)
   - Note: "Just working on my project, nothing special today"
   - Expected: AI might detect NEGATIVE (~50-70% confidence) - neutral texts often lean negative

   **Test Case 4: No Note**
   - Mood: 🎯 Focused
   - Energy: 4/5
   - Note: [leave empty]
   - Expected: No sentiment analysis (field is optional)

4. **Check Results**
   - After submitting, you'll see an alert with AI analysis
   - Example: "Mood logged successfully! AI Analysis: NEGATIVE sentiment detected"

---

### **Method 2: API Testing (Python Script)**

1. **Update Password in Script**
   ```bash
   nano test_mood_flow.py
   # Change PASSWORD = "test123" to your actual password
   ```

2. **Install requests library** (if not installed)
   ```bash
   source venv/bin/activate
   pip install requests
   ```

3. **Run Test Script**
   ```bash
   source venv/bin/activate
   python test_mood_flow.py
   ```

4. **Expected Output**
   ```
   ============================================================
     🧪 Shadow Mood Logging Test
   ============================================================

   1️⃣  Logging in...
   ✅ Login successful!

   2️⃣  Logging STRESSED mood with negative note...
   ✅ Mood logged successfully!
      🤖 AI Analysis: NEGATIVE (99.9% confidence)
      📊 Sentiment Score: -1

   3️⃣  Logging MOTIVATED mood with positive note...
   ✅ Mood logged successfully!
      🤖 AI Analysis: POSITIVE (100.0% confidence)
      📊 Sentiment Score: 1

   4️⃣  Logging CALM mood without note...
   ✅ Mood logged successfully!
      ℹ️  No sentiment analysis (no note provided)

   5️⃣  Fetching mood history...
   ✅ Found 3 recent mood logs

   6️⃣  Fetching mood trends (last 7 days)...
   ✅ Mood Trends:
      • Total logs: 3
      • Average energy: 3.0/5
      • Most common mood: stressed

      📊 Sentiment Statistics:
      • Positive: 1
      • Neutral: 0
      • Negative: 1
      • Average sentiment: 0.0
   ```

---

### **Method 3: Direct API Testing (curl)**

```bash
# 1. Login and get token
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"nicomannion6@gmail.com","password":"YOUR_PASSWORD"}' \
  | grep -o '"access_token":"[^"]*' | sed 's/"access_token":"//')

# 2. Log a mood with sentiment analysis
curl -X POST http://localhost:8000/api/v1/mood/log-mood \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "mood_type": "stressed",
    "energy_level": 2,
    "note": "Feeling overwhelmed with deadlines!"
  }' | python3 -m json.tool

# 3. Get mood trends
curl -X GET "http://localhost:8000/api/v1/mood/mood-trends?days=7" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

---

## 📊 What to Look For

### **Sentiment Analysis Results**

The AI should correctly identify:

✅ **Negative Sentiment** (-1):
- "I'm stressed about exams"
- "Too much work, feeling overwhelmed"
- "I can't handle this workload"
- Confidence: Usually 90%+

✅ **Positive Sentiment** (1):
- "Great day! Finished everything"
- "Feeling confident and ready"
- "Excellent progress today"
- Confidence: Usually 95%+

✅ **Neutral Sentiment** (0):
- "Just working on assignments"
- "Attending classes normally"
- Low confidence (50-70%)

### **Mood Trends Analytics**

Check `/api/v1/mood/mood-trends` returns:
- ✅ Average energy level
- ✅ Most common mood
- ✅ Mood distribution (count per mood type)
- ✅ Daily average energy
- ✅ **Sentiment statistics** (positive, neutral, negative counts)
- ✅ Average sentiment score

---

## 🐛 Troubleshooting

### Issue: "Mood logged successfully" but no AI analysis shown
**Cause**: Note field was empty
**Solution**: Add text in the note field to trigger sentiment analysis

### Issue: Login fails or hangs
**Cause**: Backend not running or wrong password
**Solution**:
```bash
# Check backend status
curl http://localhost:8000/health

# Restart backend
pkill -f uvicorn
source venv/bin/activate
python -m uvicorn app.main:app --reload --port 8000
```

### Issue: Sentiment analysis always shows same result
**Cause**: Model might not be loading correctly
**Solution**: Check backend logs for model loading:
```bash
tail -f backend_debug.log | grep -i "sentiment\|distilbert"
```

### Issue: API returns 401 Unauthorized
**Cause**: Token expired (30 min expiry)
**Solution**: Log in again to get new token

---

## ✅ Success Criteria

The mood logging feature is working correctly if:

1. ✅ Mood logger button appears on dashboard
2. ✅ Modal opens with 8 mood options
3. ✅ Energy scale works (1-5 selection)
4. ✅ Note field accepts text (500 char limit)
5. ✅ Submission shows success message
6. ✅ **AI sentiment analysis shows in alert** (when note provided)
7. ✅ Mood history API returns logged moods
8. ✅ Trends API includes sentiment statistics
9. ✅ Different notes produce different sentiment scores
10. ✅ Empty notes don't trigger sentiment analysis

---

## 📈 Advanced Testing

### Test Sentiment Analysis Accuracy

Try these specific phrases and verify AI detection:

| Phrase | Expected Sentiment | Expected Score |
|--------|-------------------|----------------|
| "I absolutely love this course!" | POSITIVE | 1 |
| "This is terrible, I hate it" | NEGATIVE | -1 |
| "It's okay, nothing special" | NEGATIVE/NEUTRAL | -1 or 0 |
| "Amazing progress today!" | POSITIVE | 1 |
| "Feeling very anxious about exams" | NEGATIVE | -1 |
| "Doing my homework normally" | NEGATIVE/NEUTRAL | -1 or 0 |

### Test Multiple Moods

Log 5+ moods and check:
- `/api/v1/mood/moods` - Returns all logs
- `/api/v1/mood/mood-trends?days=7` - Shows accurate statistics
- Sentiment distribution is correct (positive/neutral/negative counts)

---

## 🤖 AI Model Details

**Model**: `distilbert-base-uncased-finetuned-sst-2-english` (Hugging Face)
**Framework**: PyTorch Transformers
**Performance**: Uses Apple MPS GPU acceleration
**Accuracy**: 99%+ on clear positive/negative text
**Processing Time**: < 1 second per analysis

---

*Last Updated: November 16, 2025*
*Testing completed for Sentiment Analysis integration*
