# 🚀 SmartStudy v2.0 - Quick Start Guide

## ✅ Backend Status: FULLY WORKING!

Your SmartStudy AI backend is now fully operational. Here's what you can do:

---

## 🎯 Available API Endpoints

### Chat with SmartStudy AI
```bash
POST /api/v1/smartstudy/chat
{
  "content": "I'm struggling with algorithms, can you help?",
  "conversation_id": null  # or UUID to continue conversation
}
```

**Response:**
```json
{
  "conversation_id": "uuid-here",
  "user_message": "I'm struggling with algorithms...",
  "ai_response": "I understand you're having trouble with algorithms...",
  "tokens_used": 350,
  "created_at": "2025-11-25T14:30:00"
}
```

### Get Suggested Prompts
```bash
GET /api/v1/smartstudy/suggested-prompts
```

Returns contextual prompts based on your current state (CGPA, mood, tasks).

### Check Dashboard Trigger
```bash
GET /api/v1/smartstudy/dashboard-trigger
```

Tells you if SmartStudy should show a help prompt on the dashboard.

### List Conversations
```bash
GET /api/v1/smartstudy/conversations
```

### Get Specific Conversation
```bash
GET /api/v1/smartstudy/conversations/{conversation_id}
```

---

## 🧪 Test the Backend

### Option 1: Use the API Docs (Easiest)
1. Start the backend:
   ```bash
   cd backend
   source venv/bin/activate
   uvicorn app.main:app --reload
   ```

2. Open in browser: http://localhost:8000/api/docs

3. Try the SmartStudy endpoints!

### Option 2: Use cURL
```bash
# First, login to get a token
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"your@email.com", "password":"yourpassword"}'

# Then chat with SmartStudy
curl -X POST http://localhost:8000/api/v1/smartstudy/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{"content":"Help me understand binary trees"}'
```

---

## 🎨 What SmartStudy Knows About You

When you chat, SmartStudy automatically loads:

1. **Your Profile**
   - Name, CGPA, target CGPA, learning style

2. **Your Courses**
   - All enrolled courses with CA scores
   - Predicted grades
   - Completion rates

3. **Your Recent Tasks** (last 30 days)
   - Topics, types, weights
   - Completion status
   - Priority scores

4. **Your Recent Moods** (last 14 days)
   - Mood types and energy levels
   - Detected emotions
   - Notes

5. **Your CGPA Gap**
   - How far you are from your target

---

## 💡 How SmartStudy Responds

### Empathetic Coaching
If you're anxious/stressed → Short, reassuring responses
If you're motivated → Deeper insights and challenges
If you're sad → Supportive guidance and small wins

### Topic Expertise
Ask about any CS topic:
- Algorithms & Data Structures
- Web Development
- Machine Learning
- Databases
- And more!

### Strategic Advice
"I have 10 tasks due this week, what should I prioritize?"
→ SmartStudy ranks them by CGPA impact

### Practical Steps
Not just theory - actionable, specific guidance

---

## 🔧 Configuration

### Your OpenAI API Key
✅ Already configured in `.env`:
```
OPENAI_API_KEY=sk-proj-gB_iLHlR1obqc-44h8KYsQOjnNO4D7ewcrgj36ag8YClm8TVEQ-...
```

### Cost Estimation
- GPT-4: ~$0.03 per chat message
- Context tokens: ~500-800 per request
- Completion tokens: ~300-500 per response
- **Total**: ~$0.03-0.05 per conversation turn

**Tip**: Set a monthly budget limit in your OpenAI dashboard

---

## 🎯 Frontend Integration (Next Steps)

You need to create:

### 1. SmartStudyChat Component
**File**: `frontend/src/components/SmartStudyChat.jsx`

```jsx
import { useState, useEffect } from 'react';
import api from '../services/api';

export default function SmartStudyChat() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [conversationId, setConversationId] = useState(null);

  const sendMessage = async () => {
    if (!input.trim()) return;

    setLoading(true);
    try {
      const response = await api.post('/api/v1/smartstudy/chat', {
        content: input,
        conversation_id: conversationId
      });

      setConversationId(response.data.conversation_id);
      setMessages([...messages,
        { role: 'user', content: input },
        { role: 'assistant', content: response.data.ai_response }
      ]);
      setInput('');
    } catch (error) {
      console.error('Chat error:', error);
    }
    setLoading(false);
  };

  return (
    // Your chat UI here
  );
}
```

### 2. Add to Dashboard
**File**: `frontend/src/pages/DashboardPage.jsx`

```jsx
// Check if trigger should show
useEffect(() => {
  async function checkTrigger() {
    const trigger = await api.get('/api/v1/smartstudy/dashboard-trigger');
    if (trigger.data.show_trigger) {
      // Show "Get Help" prompt
    }
  }
  checkTrigger();
}, []);
```

### 3. API Service Functions
**File**: `frontend/src/services/api.js`

Add these functions:
```javascript
export const smartstudy = {
  sendMessage: (content, conversationId) =>
    api.post('/api/v1/smartstudy/chat', { content, conversation_id: conversationId }),

  getConversations: () =>
    api.get('/api/v1/smartstudy/conversations'),

  getSuggestedPrompts: () =>
    api.get('/api/v1/smartstudy/suggested-prompts'),

  getDashboardTrigger: () =>
    api.get('/api/v1/smartstudy/dashboard-trigger')
};
```

---

## 🎉 What You've Built

### SmartStudy Features:
✅ GPT-4 powered AI chat
✅ Context-aware responses (knows your courses, tasks, moods)
✅ 7-emotion detection system
✅ Adaptive tone based on mood
✅ Contextual suggested prompts
✅ Dashboard trigger system
✅ Conversation history
✅ Token usage tracking

### Database:
✅ 7 new tables
✅ 3 enhanced tables
✅ All migrations successful

### Backend:
✅ 8 API endpoints
✅ OpenAI integration
✅ Emotion analysis service
✅ Context loading system

---

## 📊 Monitoring

### Check OpenAI Usage:
1. Go to https://platform.openai.com/usage
2. See your API usage and costs
3. Set usage limits if needed

### Database Status:
```sql
-- Check conversations
SELECT COUNT(*) FROM chat_conversations;

-- Check messages
SELECT COUNT(*) FROM chat_messages;

-- Check emotion detection
SELECT primary_emotion, COUNT(*)
FROM mood_logs
WHERE primary_emotion IS NOT NULL
GROUP BY primary_emotion;
```

---

## 🐛 Troubleshooting

### "OpenAI client not initialized"
- Check `.env` file has OPENAI_API_KEY
- Restart backend server

### "Model download failed" (Emotion Detection)
- Requires internet connection on first use
- Model: ~500MB download
- Auto-retries with exponential backoff

### "Context loading slow"
- Normal on first load
- Consider adding caching for large datasets

---

## 🚀 Next Steps

1. **Test the backend** using API docs (http://localhost:8000/api/docs)
2. **Implement frontend** chat component (3-4 hours)
3. **Add dashboard integration** (1 hour)
4. **Test end-to-end** chat flow
5. **Deploy** and launch!

---

**You're now ready to transform Shadow into an AI-powered learning companion!** 🎓✨
